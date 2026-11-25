#!/usr/bin/env python3
"""HGI-30 folder classifier: Mac MPS, two-stage transfer learning, auditable splits.

python train_hgi30.py train --data /path/to/classification
python train_hgi30.py inspect --data /path/to/classification
python train_hgi30.py predict --checkpoint /path/to/best.pt --image photo.jpg
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import platform
import random
import sys
import time

import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
import torchvision
from torchvision import models, transforms
from torchvision.transforms import InterpolationMode

VERSION = 1
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff'}
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
LOG = logging.getLogger('hgi30')


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def setup_logging(output):
    LOG.setLevel(logging.INFO)
    LOG.handlers.clear()
    formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s')
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(output / 'training.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    LOG.addHandler(console)
    LOG.addHandler(file_handler)


def append_event(output, event):
    with (output / 'events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'time': datetime.now().astimezone().isoformat(), **event},
                                allow_nan=False) + '\n')


def append_csv(path, row):
    exists = path.exists()
    with path.open('a', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def hidden(path, root):
    return any(p.startswith('.') or p == '__MACOSX' for p in path.relative_to(root).parts)


def read_image(path):
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert('RGB')


def audit_image(task):
    path, relative, label = task
    try:
        image = read_image(path)
        digest = hashlib.sha256()
        digest.update(f'{image.width}x{image.height}:RGB:'.encode())
        digest.update(image.tobytes())
        return {'path': relative, 'label': label, 'sha256': digest.hexdigest(),
                'width': image.width, 'height': image.height}, None
    except Exception as exc:
        return None, {'path': relative, 'error': str(exc)}


def scan_dataset(root, output, scan_workers=4, skip_corrupt=False):
    """Validate full image decoding; remove identical RGB images before splitting."""
    classes = sorted(p.name for p in root.iterdir()
                     if p.is_dir() and not p.name.startswith('.') and p.name != '__MACOSX')
    if len(classes) < 2:
        raise ValueError('Expected at least two class folders directly inside --data.')
    tasks = []
    for label, name in enumerate(classes):
        paths = sorted(p for p in (root / name).rglob('*')
                       if p.is_file() and p.suffix.lower() in EXTENSIONS and not hidden(p, root))
        if not paths:
            raise ValueError(f'Class folder {name!r} contains no supported images.')
        tasks.extend((p, p.relative_to(root).as_posix(), label) for p in paths)
    LOG.info('Auditing %d images in %d folders; decoding and hashing RGB pixels.',
             len(tasks), len(classes))
    samples, corrupt, duplicates, conflicts, seen = [], [], [], [], {}
    with ThreadPoolExecutor(max_workers=scan_workers) as executor:
        for i, (sample, error) in enumerate(executor.map(audit_image, tasks), 1):
            if error:
                corrupt.append(error)
            else:
                previous = seen.get(sample['sha256'])
                if previous is None:
                    seen[sample['sha256']] = sample
                    samples.append(sample)
                elif previous['label'] != sample['label']:
                    conflicts.append({'first': previous['path'], 'second': sample['path']})
                else:
                    duplicates.append({'kept': previous['path'], 'removed': sample['path']})
            if i % 250 == 0 or i == len(tasks):
                LOG.info('Image audit %d/%d | unique=%d duplicates=%d corrupt=%d conflicts=%d',
                         i, len(tasks), len(samples), len(duplicates), len(corrupt), len(conflicts))
    write_json(output / 'data_audit.json', {'classes': classes, 'scanned': len(tasks),
               'unique_images': len(samples), 'duplicates_removed': duplicates,
               'corrupt_images': corrupt, 'cross_class_conflicts': conflicts})
    if conflicts:
        raise ValueError('Identical images have conflicting class labels. Fix data_audit.json conflicts.')
    if corrupt and not skip_corrupt:
        raise ValueError('Unreadable images found; see data_audit.json. Fix them or use --skip-corrupt.')
    if len(classes) != 30:
        LOG.warning('Found %d classes; full HGI-30 normally has 30. Using your folder labels.', len(classes))
    LOG.warning('Exact duplicate removal does NOT detect rotated/noisy copies or the same physical '
                'item in different photos. Use --groups-csv when their identities are known; '
                'always test on new physical items from your camera.')
    return classes, samples


def read_groups(path, samples, duplicates=()):
    """CSV columns path,group_id; paths relative to the classification directory."""
    mapping = {}
    if path:
        with path.open(newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            if not {'path', 'group_id'}.issubset(reader.fieldnames or []):
                raise ValueError('--groups-csv needs columns path,group_id.')
            for row in reader:
                key = row['path'].replace('\\', '/').removeprefix('./')
                if not row['group_id'].strip() or key in mapping:
                    raise ValueError(f'Blank or repeated group entry: {key}')
                mapping[key] = row['group_id'].strip()
    known = {sample['path'] for sample in samples}
    if path and not known.issubset(mapping):
        missing = sorted(known - mapping.keys())
        raise ValueError(f'Group CSV must cover every retained image. Missing: {missing[:5]}')
    for duplicate in duplicates:
        kept, removed = duplicate['kept'], duplicate['removed']
        if kept in mapping and removed in mapping and mapping[kept] != mapping[removed]:
            raise ValueError(f'Identical images have different group IDs: {kept}, {removed}. '
                             'Merge their physical-item groups before splitting.')
    return mapping


def make_split(classes, samples, seed, val_fraction, test_fraction, groups):
    rng = random.Random(seed)
    assigned = []
    owners = {}
    for label, name in enumerate(classes):
        by_group = {}
        for sample in samples:
            if sample['label'] != label:
                continue
            group = groups.get(sample['path'], sample['sha256'])
            if group in owners and owners[group] != label:
                raise ValueError(f'Group {group!r} spans multiple classes. Check labels/group IDs.')
            owners[group] = label
            by_group.setdefault(group, []).append(sample)
        keys = sorted(by_group)
        rng.shuffle(keys)
        if len(keys) < 3:
            raise ValueError(f'{name}: need at least 3 independent groups/images for train/val/test.')
        n_test = max(1, round(len(keys) * test_fraction))
        n_test = min(n_test, len(keys) - 2)
        n_val = max(1, round(len(keys) * val_fraction))
        n_val = min(n_val, len(keys) - n_test - 1)
        for i, group in enumerate(keys):
            split = 'test' if i < n_test else 'val' if i < n_test + n_val else 'train'
            assigned.extend({**s, 'group': group, 'split': split} for s in by_group[group])
    return sorted(assigned, key=lambda s: s['path'])


def fingerprint(classes, samples):
    content = json.dumps({'classes': classes, 'samples': samples}, sort_keys=True).encode()
    return hashlib.sha256(content).hexdigest()


class SquarePad:
    """Retain the whole object rather than center-cropping away its edges."""
    def __call__(self, image):
        side = max(image.size)
        left = (side - image.width) // 2
        top = (side - image.height) // 2
        return ImageOps.expand(image, (left, top, side - image.width - left,
                                     side - image.height - top), fill=(124, 116, 104))


def base_transform(size):
    return transforms.Compose([SquarePad(), transforms.Resize((size, size),
             interpolation=InterpolationMode.BICUBIC, antialias=True)])


def cache_name(sample, size):
    return f'pad-v1-{size}-{sample["sha256"]}.png'


def prepare_cache(root, samples, cache_dir, size, workers):
    """Lossless cache of the exact same pre-augmentation pixels used without caching."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    resize = base_transform(size)

    def convert(sample):
        destination = cache_dir / cache_name(sample, size)
        if destination.exists():
            return 0
        image = resize(read_image(root / sample['path']))
        temporary = destination.with_suffix(f'.{os.getpid()}.tmp')
        image.save(temporary, format='PNG', compress_level=1)
        temporary.replace(destination)
        return 1

    LOG.info('Preparing lossless %dx%d input cache: %s', size, size, cache_dir)
    created = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i, made in enumerate(executor.map(convert, samples), 1):
            created += made
            if i % 250 == 0 or i == len(samples):
                LOG.info('Image cache %d/%d | created=%d reused=%d', i, len(samples), created, i - created)


def make_transform(size, training, cached=False):
    steps = [] if cached else [base_transform(size)]
    if training:
        # A border allows moderate rotations without cutting the original object's corners.
        steps += [transforms.Pad(max(4, size // 12), fill=(124, 116, 104)),
                  transforms.RandomRotation(15, interpolation=InterpolationMode.BILINEAR,
                                            fill=(124, 116, 104)),
                  transforms.Resize((size, size), interpolation=InterpolationMode.BICUBIC,
                                    antialias=True),
                  transforms.RandomHorizontalFlip(),
                  transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10)]
    return transforms.Compose(steps + [transforms.ToTensor(), transforms.Normalize(MEAN, STD)])


class FolderSamples(Dataset):
    def __init__(self, root, samples, transform, cache_dir=None, size=224):
        self.root, self.samples, self.transform = root, samples, transform
        self.cache_dir, self.size = cache_dir, size

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        path = self.cache_dir / cache_name(sample, self.size) if self.cache_dir else self.root / sample['path']
        return self.transform(read_image(path)), sample['label']


def seed_worker(_worker):
    seed = torch.initial_seed() % (2**32)
    random.seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(1)


def get_device(requested):
    if requested == 'auto':
        requested = 'mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'
    if requested == 'mps' and not torch.backends.mps.is_available():
        raise ValueError('MPS is unavailable. Use native arm64 Python on a supported Mac, or --device cpu.')
    if requested == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA is unavailable.')
    return torch.device(requested)


def synchronize(device):
    if device.type == 'mps':
        torch.mps.synchronize()
    elif device.type == 'cuda':
        torch.cuda.synchronize()


def device_memory(device):
    if device.type == 'mps':
        return round(torch.mps.current_allocated_memory() / 2**20, 1)
    if device.type == 'cuda':
        return round(torch.cuda.memory_allocated() / 2**20, 1)
    return 0.0


def make_model(name, count, pretrained=True):
    if name == 'efficientnet_b0':
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
    elif name == 'mobilenet_v3_large':
        weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_large(weights=weights)
    else:
        raise ValueError(f'Unsupported model: {name}')
    features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(features, count)
    return model


def configure_stage(model, args, epoch, device, state=None):
    head_only = epoch <= args.head_epochs
    for p in model.features.parameters():
        p.requires_grad_(not head_only)
    groups = [dict(params=model.features.parameters(), lr=args.backbone_lr),
              dict(params=model.classifier.parameters(), lr=args.head_lr)]
    optimizer = torch.optim.AdamW(groups, weight_decay=args.weight_decay)
    if state is not None:
        optimizer.load_state_dict(state)
        for values in optimizer.state.values():
            for key, value in values.items():
                # Adam's step counter stays on CPU for non-capturable optimizers.
                if torch.is_tensor(value) and key != 'step':
                    values[key] = value.to(device)
    if head_only:
        backbone_lr, head_lr = 0.0, args.warmup_lr
    else:
        progress = (epoch - args.head_epochs - 1) / max(1, args.epochs - args.head_epochs - 1)
        factor = 0.05 + 0.95 * (1 + math.cos(math.pi * progress)) / 2
        backbone_lr, head_lr = args.backbone_lr * factor, args.head_lr * factor
    optimizer.param_groups[0]['lr'] = backbone_lr
    optimizer.param_groups[1]['lr'] = head_lr
    return optimizer, head_only


def report_metrics(targets, predictions, count):
    confusion = torch.bincount(targets * count + predictions, minlength=count * count).reshape(count, count)
    tp = confusion.diag().double()
    support = confusion.sum(1)
    precision = tp / confusion.sum(0).clamp_min(1)
    recall = tp / support.clamp_min(1)
    f1 = 2 * precision * recall / (precision + recall).clamp_min(1e-12)
    return {'accuracy': float(tp.sum() / max(1, int(support.sum()))),
            'macro_f1': float(f1.mean()), 'precision': precision.tolist(),
            'recall': recall.tolist(), 'f1': f1.tolist(), 'support': support.tolist(),
            'confusion_matrix': confusion.tolist()}


def run_epoch(model, loader, criterion, device, count, epoch, phase, output,
              log_every, optimizer=None, head_only=False):
    training = optimizer is not None
    model.train(training)
    if training and head_only:
        # Freeze BatchNorm statistics and feature-extractor stochastic layers too.
        model.features.eval()
    total_loss = torch.zeros((), device=device)
    hits = torch.zeros((), dtype=torch.long, device=device)
    all_targets, all_predictions, all_scores = [], [], []
    seen = 0
    synchronize(device)
    start = time.perf_counter()
    with torch.set_grad_enabled(training):
        for batch, (images, labels) in enumerate(loader, 1):
            images = images.to(device, non_blocking=device.type == 'cuda')
            labels = labels.to(device, non_blocking=device.type == 'cuda')
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0, foreach=False)
                optimizer.step()
            predictions = logits.detach().argmax(1)
            all_targets.append(labels.detach())
            all_predictions.append(predictions)
            if not training:
                all_scores.append(logits.detach().softmax(1).amax(1))
            seen += len(labels)
            total_loss += loss.detach() * len(labels)
            hits += (predictions == labels).sum()
            if batch % log_every == 0 or batch == len(loader):
                loss_value, accuracy = total_loss.item() / seen, hits.item() / seen
                if not math.isfinite(loss_value):
                    raise FloatingPointError('Non-finite loss; stopping without replacing the best model.')
                elapsed = time.perf_counter() - start
                event = {'type': 'batch', 'epoch': epoch, 'phase': phase, 'batch': batch,
                         'batches': len(loader), 'images': seen, 'loss': loss_value,
                         'accuracy': accuracy, 'images_per_second': seen / max(elapsed, 1e-9),
                         'eta_seconds': elapsed / batch * (len(loader) - batch),
                         'device_memory_mib': device_memory(device)}
                LOG.info('Epoch %03d | %-5s | batch %d/%d | loss %.4f | acc %.2f%% | '
                         '%.1f img/s | ETA %.0fs | device %.0f MiB', epoch, phase, batch,
                         len(loader), loss_value, accuracy * 100, event['images_per_second'],
                         event['eta_seconds'], event['device_memory_mib'])
                append_event(output, event)
    targets = torch.cat(all_targets).cpu()
    predictions = torch.cat(all_predictions).cpu()
    scores = torch.cat(all_scores).cpu().tolist() if all_scores else []
    metrics = report_metrics(targets, predictions, count)
    metrics.update(loss=total_loss.item() / seen, seconds=time.perf_counter() - start)
    return metrics, predictions.tolist(), scores


def save_report(output, name, metrics, classes, samples=None, predictions=None, scores=None):
    write_json(output / f'{name}_metrics.json', metrics)
    with (output / f'{name}_per_class.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['class', 'precision', 'recall', 'f1', 'support'])
        for i, label in enumerate(classes):
            writer.writerow([label, metrics['precision'][i], metrics['recall'][i],
                             metrics['f1'][i], metrics['support'][i]])
    with (output / f'{name}_confusion.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['actual / predicted', *classes])
        for label, row in zip(classes, metrics['confusion_matrix']):
            writer.writerow([label, *row])
    if samples is not None:
        with (output / f'{name}_predictions.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['path', 'actual', 'predicted', 'confidence', 'correct'])
            for sample, prediction, score in zip(samples, predictions, scores):
                writer.writerow([sample['path'], classes[sample['label']], classes[prediction],
                                 score, int(sample['label'] == prediction)])


def cpu_tree(value):
    if torch.is_tensor(value):
        return value.detach().cpu()
    if isinstance(value, dict):
        return {k: cpu_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [cpu_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(cpu_tree(v) for v in value)
    return value


def save_checkpoint(path, payload):
    temporary = path.with_suffix('.tmp')
    torch.save(cpu_tree(payload), temporary)
    temporary.replace(path)


def load_checkpoint(path):
    return torch.load(path, map_location='cpu', weights_only=True)


def make_loader(dataset, args, training, device, generator=None):
    kwargs = dict(batch_size=args.batch_size, shuffle=training, num_workers=args.workers,
                  pin_memory=device.type == 'cuda', worker_init_fn=seed_worker,
                  generator=generator, drop_last=False)
    if args.workers:
        kwargs.update(persistent_workers=True, prefetch_factor=2, multiprocessing_context='spawn')
    return DataLoader(dataset, **kwargs)


def prepare_data(args, output):
    root = args.data.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Dataset folder does not exist: {root}')
    if root == output or root in output.parents:
        raise ValueError('--output must be outside the dataset directory.')
    classes, samples = scan_dataset(root, output, args.scan_workers, args.skip_corrupt)
    audit = json.loads((output / 'data_audit.json').read_text())
    groups = read_groups(args.groups_csv, samples, audit['duplicates_removed'])
    samples = make_split(classes, samples, args.seed, args.val_fraction, args.test_fraction, groups)
    split_fingerprint = fingerprint(classes, samples)
    write_json(output / 'splits.json', {'version': VERSION, 'root': str(root),
               'fingerprint': split_fingerprint, 'seed': args.seed, 'classes': classes,
               'grouped_by_user': bool(groups), 'samples': samples})
    partitions = {key: [s for s in samples if s['split'] == key] for key in ['train', 'val', 'test']}
    for i, name in enumerate(classes):
        counts = [sum(s['label'] == i for s in partitions[key]) for key in partitions]
        LOG.info('Class %-25s | train=%4d val=%4d test=%4d', name, *counts)
    LOG.info('Split totals: %s', {k: len(v) for k, v in partitions.items()})
    return root, classes, partitions, split_fingerprint


def train(args, output):
    root, classes, partitions, split_fingerprint = prepare_data(args, output)
    device = get_device(args.device)
    torch.set_num_threads(args.cpu_threads)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == 'mps':
        torch.mps.manual_seed(args.seed)
    runtime = {'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(),
               'torch': str(torch.__version__), 'torchvision': str(torchvision.__version__),
               'device': str(device), 'precision': 'float32', 'cpu_threads': args.cpu_threads,
               'mps_available': torch.backends.mps.is_available(),
               'mps_fast_math': os.environ.get('PYTORCH_MPS_FAST_MATH', 'unset'),
               'mps_fallback': os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK', 'unset')}
    write_json(output / 'runtime.json', runtime)
    LOG.info('Runtime: %s', runtime)
    if device.type == 'cpu':
        LOG.warning('Running on CPU. A supported Mac with native Apple Silicon Python can use MPS.')
    if os.environ.get('PYTORCH_MPS_FAST_MATH') == '1':
        LOG.warning('External PYTORCH_MPS_FAST_MATH=1 is enabled; unset it for the intended baseline.')
    previous = load_checkpoint(args.resume) if args.resume else None
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    if previous:
        required = ['model', 'image_size', 'epochs', 'head_epochs', 'backbone_lr', 'head_lr',
                    'warmup_lr', 'weight_decay', 'label_smoothing', 'class_weights', 'batch_size']
        if previous['fingerprint'] != split_fingerprint or previous['classes'] != classes:
            raise ValueError('Dataset/split changed since the checkpoint. Start a new run.')
        for key in required:
            if previous['config'][key] != config[key]:
                raise ValueError(f'Resume requires the original --{key.replace("_", "-")} value.')
    LOG.info('Creating %s; %s.', args.model, 'restoring checkpoint' if previous else
             'RANDOM INITIALIZATION (testing mode)' if args.no_pretrained else 'loading ImageNet pretrained weights')
    model = make_model(args.model, len(classes), pretrained=not previous and not args.no_pretrained)
    if previous:
        model.load_state_dict(previous['model_state'])
    model.to(device)
    generator = torch.Generator()
    cache_dir = None if args.no_cache else args.cache_dir.expanduser().resolve()
    if cache_dir:
        if cache_dir == root or root in cache_dir.parents:
            raise ValueError('--cache-dir must be outside the dataset directory.')
        prepare_cache(root, [s for entries in partitions.values() for s in entries],
                      cache_dir, args.image_size, args.scan_workers)
    datasets = {key: FolderSamples(root, entries, make_transform(args.image_size, key == 'train', bool(cache_dir)),
                                  cache_dir, args.image_size)
                for key, entries in partitions.items()}
    loaders = {key: make_loader(dataset, args, key == 'train', device,
                               generator if key == 'train' else None)
               for key, dataset in datasets.items()}
    counts = torch.bincount(torch.tensor([s['label'] for s in partitions['train']]), minlength=len(classes)).float()
    weights = None
    if args.class_weights:
        weights = counts.sum().div(counts).sqrt()
        weights /= weights.mean()
        weights = weights.to(device)
    # Evaluate with unweighted, unsmoothed loss for comparable validation reports.
    train_loss = nn.CrossEntropyLoss(weight=weights, label_smoothing=args.label_smoothing)
    eval_loss = nn.CrossEntropyLoss()
    best = previous['best_score'] if previous else -1.0
    best_epoch = previous['best_epoch'] if previous else 0
    stale = previous['stale_epochs'] if previous else 0
    first_epoch = previous['epoch'] + 1 if previous else 1
    optimizer_state = previous['optimizer_state'] if previous else None
    optimizer = None
    if previous:
        # Restore the best weights as well when resuming into a new output folder.
        best_payload = previous.get('best_model_state')
        if best_payload is None:
            raise ValueError('Resume expects last.pt, which contains the best model snapshot.')
        save_checkpoint(output / 'best.pt', {**previous, 'epoch': best_epoch, 'model_state': best_payload,
                                             'optimizer_state': {}, 'best_model_state': None})
    LOG.info('Training %d epochs maximum: %d classifier-only, then full fine-tuning. '
             'Selection=validation macro-F1; patience=%d.', args.epochs, args.head_epochs, args.patience)
    best_model_state = previous['best_model_state'] if previous else None
    try:
        for epoch in range(first_epoch, args.epochs + 1):
            # Keep Adam moments within a stage, reset deliberately when unfreezing.
            new_optimizer, head_only = configure_stage(model, args, epoch, device,
                optimizer_state if epoch != args.head_epochs + 1 else None)
            optimizer = new_optimizer
            if epoch == args.head_epochs + 1:
                stale = 0
                LOG.info('Unfreezing the backbone. Fine-tuning all layers; resetting Adam moments.')
            generator.manual_seed(args.seed + epoch)
            LOG.info('Epoch %03d/%03d | stage=%s | backbone LR=%.7f | classifier LR=%.7f',
                     epoch, args.epochs, 'classifier' if head_only else 'fine-tune',
                     optimizer.param_groups[0]['lr'], optimizer.param_groups[1]['lr'])
            training, _, _ = run_epoch(model, loaders['train'], train_loss, device, len(classes),
                epoch, 'train', output, args.log_every, optimizer, head_only)
            validation, _, _ = run_epoch(model, loaders['val'], eval_loss, device, len(classes),
                epoch, 'val', output, args.log_every)
            improved = validation['macro_f1'] > best + args.min_delta
            if improved:
                best = validation['macro_f1']
                best_epoch = epoch
                stale = 0
                best_model_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            elif not head_only:
                stale += 1
            row = dict(epoch=epoch, stage='classifier' if head_only else 'fine-tune',
                       backbone_lr=optimizer.param_groups[0]['lr'],
                       classifier_lr=optimizer.param_groups[1]['lr'],
                       train_loss=training['loss'], train_accuracy=training['accuracy'],
                       val_loss=validation['loss'], val_accuracy=validation['accuracy'],
                       val_macro_f1=validation['macro_f1'], best_macro_f1=best,
                       train_seconds=training['seconds'], val_seconds=validation['seconds'],
                       improved=int(improved), stale_epochs=stale)
            append_csv(output / 'epochs.csv', row)
            append_event(output, {'type': 'epoch', **row})
            LOG.info('Epoch %03d complete | train %.2f%% | val %.2f%% | val macro-F1 %.4f | '
                     'best %.4f | %s | patience %d/%d', epoch, training['accuracy'] * 100,
                     validation['accuracy'] * 100, validation['macro_f1'], best,
                     'NEW BEST' if improved else 'no improvement', stale, args.patience)
            worst = sorted(range(len(classes)), key=lambda i: validation['f1'][i])[:5]
            LOG.info('Lowest validation F1: %s', ', '.join(f'{classes[i]}={validation["f1"][i]:.3f}' for i in worst))
            payload = dict(version=VERSION, epoch=epoch, model_name=args.model, classes=classes,
                           image_size=args.image_size, preprocessing='square-pad-resize-imagenet-v1',
                           model_state=model.state_dict(), optimizer_state=optimizer.state_dict(),
                           config=config, fingerprint=split_fingerprint, best_score=best,
                           best_epoch=best_epoch, stale_epochs=stale, best_model_state=best_model_state)
            if improved:
                save_checkpoint(output / 'best.pt', {**payload, 'optimizer_state': {}, 'best_model_state': None})
                save_report(output, 'best_validation', validation, classes)
            save_checkpoint(output / 'last.pt', payload)
            optimizer_state = optimizer.state_dict()
            if not head_only and stale >= args.patience:
                LOG.info('Early stopping: validation macro-F1 did not improve for %d epochs.', stale)
                break
    except KeyboardInterrupt:
        LOG.warning('Interrupted. last.pt contains the most recent fully completed epoch. '
                    'The current partial epoch is not saved; resume last.pt to continue.')
        return 130
    if best_model_state is None:
        raise ValueError('No completed epoch is available to evaluate.')
    model.load_state_dict(best_model_state)
    LOG.info('Evaluating the selected best model once on the held-out test split.')
    testing, predictions, scores = run_epoch(model, loaders['test'], eval_loss, device,
        len(classes), 0, 'test', output, args.log_every)
    save_report(output, 'test', testing, classes, partitions['test'], predictions, scores)
    LOG.info('TEST | accuracy %.2f%% | macro-F1 %.4f | loss %.4f',
             testing['accuracy'] * 100, testing['macro_f1'], testing['loss'])
    for i, name in enumerate(classes):
        LOG.info('TEST %-25s | precision %.3f recall %.3f F1 %.3f support %d',
                 name, testing['precision'][i], testing['recall'][i], testing['f1'][i], testing['support'][i])
    write_json(output / 'labels.json', {'classes': classes, 'class_to_index': {c: i for i, c in enumerate(classes)}})
    LOG.info('Saved best.pt, last.pt, logs, splits, and test reports to %s', output)
    return 0


def predict(args):
    checkpoint = load_checkpoint(args.checkpoint)
    device = get_device(args.device)
    model = make_model(checkpoint['model_name'], len(checkpoint['classes']), pretrained=False)
    model.load_state_dict(checkpoint['model_state'])
    model.to(device).eval()
    image = make_transform(checkpoint['image_size'], False)(read_image(args.image)).unsqueeze(0).to(device)
    with torch.inference_mode():
        probabilities = model(image).softmax(1)[0].cpu()
    values, indices = probabilities.topk(min(args.top_k, len(probabilities)))
    print(json.dumps({'image': str(args.image), 'device': str(device),
          'predictions': [{'class': checkpoint['classes'][i], 'probability': p}
                          for p, i in zip(values.tolist(), indices.tolist())]}, indent=2))
    return 0


def parser():
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = result.add_subparsers(dest='command', required=True)
    for command in ['train', 'inspect']:
        p = sub.add_parser(command)
        p.add_argument('--data', type=Path, required=True, help='Folder containing one subfolder per class.')
        p.add_argument('--output', type=Path, help='New empty run folder; defaults to runs/TIMESTAMP beside this script.')
        p.add_argument('--seed', type=int, default=42)
        p.add_argument('--val-fraction', type=float, default=0.15)
        p.add_argument('--test-fraction', type=float, default=0.15)
        p.add_argument('--groups-csv', type=Path, help='Optional physical-item/augmentation groups: path,group_id.')
        p.add_argument('--skip-corrupt', action='store_true')
        p.add_argument('--scan-workers', type=int, default=4)
        if command == 'inspect':
            continue
        p.add_argument('--model', choices=['efficientnet_b0', 'mobilenet_v3_large'], default='efficientnet_b0')
        p.add_argument('--device', choices=['auto', 'mps', 'cpu', 'cuda'], default='auto')
        p.add_argument('--epochs', type=int, default=40, help='Total epochs including the head warm-up.')
        p.add_argument('--head-epochs', type=int, default=3)
        p.add_argument('--batch-size', type=int, default=32)
        p.add_argument('--image-size', type=int, default=224)
        p.add_argument('--workers', type=int, default=2, help='Parallel image-loader workers; 0 for troubleshooting.')
        p.add_argument('--cache-dir', type=Path, default=Path(__file__).resolve().parent / '.image-cache',
                       help='Reusable lossless input cache outside the dataset; default beside this script.')
        p.add_argument('--no-cache', action='store_true', help='Disable disk cache to save space.')
        p.add_argument('--cpu-threads', type=int, default=min(4, os.cpu_count() or 1))
        p.add_argument('--backbone-lr', type=float, default=3e-5)
        p.add_argument('--head-lr', type=float, default=3e-4)
        p.add_argument('--warmup-lr', type=float, default=1e-3)
        p.add_argument('--weight-decay', type=float, default=1e-4)
        p.add_argument('--label-smoothing', type=float, default=0.05)
        p.add_argument('--class-weights', action='store_true', help='Inverse-square-root weights based on training counts.')
        p.add_argument('--patience', type=int, default=8)
        p.add_argument('--min-delta', type=float, default=0.0001)
        p.add_argument('--log-every', type=int, default=20)
        p.add_argument('--resume', type=Path, help='Resume a last.pt checkpoint with original training settings.')
        p.add_argument('--no-pretrained', action='store_true', help='Offline/testing only: random initialization lowers expected quality.')
    p = sub.add_parser('predict')
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--device', choices=['auto', 'mps', 'cpu', 'cuda'], default='auto')
    p.add_argument('--top-k', type=int, default=5)
    return result


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.command == 'predict':
        if args.top_k < 1:
            p.error('--top-k must be positive.')
        return predict(args)
    if not 0 < args.val_fraction < 1 or not 0 < args.test_fraction < 1 or args.val_fraction + args.test_fraction >= 1:
        p.error('Validation and test fractions must be positive and sum to less than 1.')
    if args.scan_workers < 1:
        p.error('--scan-workers must be positive.')
    if args.command == 'train':
        if args.epochs < 1 or not 0 <= args.head_epochs < args.epochs:
            p.error('--epochs must be positive and greater than --head-epochs.')
        if min(args.batch_size, args.image_size, args.cpu_threads, args.patience, args.log_every) < 1 or args.workers < 0:
            p.error('Batch size, image size, threads, patience, and log interval must be positive; workers >= 0.')
        if args.image_size < 64 or min(args.backbone_lr, args.head_lr, args.warmup_lr) <= 0:
            p.error('--image-size must be >=64 and learning rates must be positive.')
        if not 0 <= args.label_smoothing < 1 or args.weight_decay < 0 or args.min_delta < 0:
            p.error('Invalid label smoothing, weight decay, or min delta.')
    output = (args.output or Path(__file__).resolve().parent / 'runs' /
              datetime.now().strftime('%Y%m%d-%H%M%S-%f')).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        p.error('--output must be a new or empty directory to protect existing runs. Resume into a new folder.')
    output.mkdir(parents=True, exist_ok=True)
    setup_logging(output)
    write_json(output / 'config.json', {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()})
    try:
        if args.command == 'inspect':
            prepare_data(args, output)
            LOG.info('Inspection complete; no model trained. See data_audit.json and splits.json.')
            return 0
        return train(args, output)
    except Exception:
        LOG.exception('Run failed. See the traceback above and training.log. '
                      'For GPU memory errors, try --batch-size 16 in a new run; '
                      'for worker errors, try --workers 0.')
        return 1


if __name__ == '__main__':
    torch.multiprocessing.freeze_support()
    raise SystemExit(main())
