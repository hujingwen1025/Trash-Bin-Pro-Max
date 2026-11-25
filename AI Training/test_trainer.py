"""Focused tests for data leakage, evaluation, preprocessing, and actual training."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import torch

import train_hgi30 as trainer


class TrainerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / 'classification'
        self.data.mkdir()
        for label in ['applecore', 'battery_button', 'plastic_bottle']:
            folder = self.data / label
            folder.mkdir()
            for i in range(9):
                # Different pixels, non-square shapes, and three simple visual classes.
                rng = np.random.default_rng(i + len(label) * 100)
                pixels = rng.integers(0, 64, (48, 64, 3), dtype=np.uint8)
                pixels[:, :, ['applecore', 'battery_button', 'plastic_bottle'].index(label)] += 160
                Image.fromarray(pixels).save(folder / f'{label}{i:04d}.png')
        self.audit_output = self.root / 'audit'
        self.audit_output.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_duplicate_pixels_removed_even_with_different_encoding(self):
        source = self.data / 'applecore/applecore0000.png'
        with Image.open(source) as image:
            image.save(self.data / 'applecore/copy.bmp')
        classes, samples = trainer.scan_dataset(self.data, self.audit_output)
        self.assertEqual(len(samples), 27)
        report = json.loads((self.audit_output / 'data_audit.json').read_text())
        self.assertEqual(len(report['duplicates_removed']), 1)
        split = trainer.make_split(classes, samples, 42, .15, .15, {})
        self.assertEqual(len({s['sha256'] for s in split}), len(split))

    def test_conflicting_labels_and_corrupt_images_stop_run(self):
        shutil.copy2(self.data / 'applecore/applecore0000.png', self.data / 'battery_button/conflict.png')
        (self.data / 'plastic_bottle/broken.jpg').write_bytes(b'not an image')
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            trainer.scan_dataset(self.data, self.audit_output)
        report = json.loads((self.audit_output / 'data_audit.json').read_text())
        self.assertEqual(len(report['cross_class_conflicts']), 1)
        self.assertEqual(len(report['corrupt_images']), 1)
        (self.data / 'battery_button/conflict.png').unlink()
        with self.assertRaisesRegex(ValueError, 'Unreadable'):
            trainer.scan_dataset(self.data, self.audit_output)
        _, samples = trainer.scan_dataset(self.data, self.audit_output, skip_corrupt=True)
        self.assertEqual(len(samples), 27)

    def test_physical_groups_never_cross_splits_and_split_is_repeatable(self):
        classes, samples = trainer.scan_dataset(self.data, self.audit_output)
        groups = {s['path']: f'{s["label"]}-{i // 3}' for i, s in enumerate(samples)}
        first = trainer.make_split(classes, samples, 42, .15, .15, groups)
        second = trainer.make_split(classes, samples, 42, .15, .15, groups)
        self.assertEqual(first, second)
        memberships = {}
        for sample in first:
            memberships.setdefault(sample['group'], set()).add(sample['split'])
        self.assertTrue(all(len(value) == 1 for value in memberships.values()))
        self.assertEqual({s['split'] for s in first}, {'train', 'val', 'test'})

    def test_known_confusion_metrics(self):
        metrics = trainer.report_metrics(torch.tensor([0, 0, 1, 1]), torch.tensor([0, 1, 1, 1]), 2)
        self.assertEqual(metrics['confusion_matrix'], [[1, 1], [0, 2]])
        self.assertAlmostEqual(metrics['accuracy'], .75)
        self.assertAlmostEqual(metrics['macro_f1'], (2 / 3 + .8) / 2)

    def test_group_csv_cannot_split_identical_images_into_different_groups(self):
        duplicate = self.data / 'applecore/copy.png'
        shutil.copy2(self.data / 'applecore/applecore0000.png', duplicate)
        _, samples = trainer.scan_dataset(self.data, self.audit_output)
        audit = json.loads((self.audit_output / 'data_audit.json').read_text())
        groups = self.root / 'groups.csv'
        with groups.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['path', 'group_id'])
            for sample in samples:
                writer.writerow([sample['path'], sample['path']])
            writer.writerow(['applecore/copy.png', 'conflicting-duplicate'])
        with self.assertRaisesRegex(ValueError, 'different group IDs'):
            trainer.read_groups(groups, samples, audit['duplicates_removed'])

    def test_padding_and_prediction_transforms(self):
        image = Image.new('RGB', (60, 20), (255, 0, 0))
        padded = trainer.SquarePad()(image)
        self.assertEqual(padded.size, (60, 60))
        self.assertEqual(padded.getpixel((0, 20)), (255, 0, 0))
        tensor = trainer.make_transform(64, False)(image)
        self.assertEqual(tuple(tensor.shape), (3, 64, 64))
        self.assertTrue(torch.isfinite(tensor).all())

    def test_cache_preserves_exact_model_input_pixels(self):
        _, samples = trainer.scan_dataset(self.data, self.audit_output)
        cache = self.root / 'cache'
        trainer.prepare_cache(self.data, samples, cache, 64, 2)
        sample = samples[0]
        original = trainer.read_image(self.data / sample['path'])
        cached = trainer.read_image(cache / trainer.cache_name(sample, 64))
        self.assertTrue(torch.equal(trainer.make_transform(64, False)(original),
                                    trainer.make_transform(64, False, cached=True)(cached)))
        torch.manual_seed(123)
        first = trainer.make_transform(64, True)(original)
        torch.manual_seed(123)
        second = trainer.make_transform(64, True, cached=True)(cached)
        self.assertTrue(torch.equal(first, second))

    def test_training_resume_and_prediction_end_to_end(self):
        # Small data and image size exercise real gradients, stage changes, checkpoint
        # loading, held-out evaluation, and macOS spawn workers without a weight download.
        run = self.root / 'run'
        common = ['--data', str(self.data), '--epochs', '2', '--head-epochs', '1',
                  '--batch-size', '6', '--image-size', '64', '--no-pretrained',
                  '--device', 'cpu', '--workers', '1', '--cpu-threads', '2', '--log-every', '1',
                  '--cache-dir', str(self.root / 'cache')]
        script = str(Path(trainer.__file__))
        result = subprocess.run([sys.executable, script, 'train', *common, '--output', str(run)],
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ['best.pt', 'last.pt', 'epochs.csv', 'test_per_class.csv',
                     'test_confusion.csv', 'test_predictions.csv', 'splits.json']:
            self.assertTrue((run / name).is_file(), name)
        with (run / 'epochs.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([r['stage'] for r in rows], ['classifier', 'fine-tune'])
        checkpoint = trainer.load_checkpoint(run / 'last.pt')
        self.assertEqual(checkpoint['epoch'], 2)
        self.assertEqual(checkpoint['classes'], ['applecore', 'battery_button', 'plastic_bottle'])
        self.assertTrue(all(v.device.type == 'cpu' for v in checkpoint['model_state'].values()))
        prediction = subprocess.run([sys.executable, script, 'predict', '--checkpoint', str(run / 'best.pt'),
              '--image', str(self.data / 'applecore/applecore0000.png'), '--device', 'cpu'],
              capture_output=True, text=True, timeout=60)
        self.assertEqual(prediction.returncode, 0, prediction.stderr)
        self.assertEqual(len(json.loads(prediction.stdout)['predictions']), 3)
        # Resume the completed run: best snapshot must survive into the new folder,
        # and held-out results must match exactly on CPU.
        resumed = self.root / 'resumed'
        result = subprocess.run([sys.executable, script, 'train', *common, '--output', str(resumed),
                                '--resume', str(run / 'last.pt')], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        original = json.loads((run / 'test_metrics.json').read_text())
        restored = json.loads((resumed / 'test_metrics.json').read_text())
        self.assertEqual(original['confusion_matrix'], restored['confusion_matrix'])
        original_model = trainer.load_checkpoint(run / 'best.pt')['model_state']
        resumed_model = trainer.load_checkpoint(resumed / 'best.pt')['model_state']
        self.assertTrue(all(torch.equal(original_model[k], resumed_model[k]) for k in original_model))

    def test_interrupted_run_resumes_training_at_next_epoch(self):
        output = self.root / 'interrupted'
        output.mkdir()
        trainer.setup_logging(output)
        common = ['--data', str(self.data), '--epochs', '2', '--head-epochs', '1',
                  '--batch-size', '6', '--image-size', '64', '--no-pretrained',
                  '--device', 'cpu', '--workers', '0', '--cpu-threads', '2', '--no-cache']
        args = trainer.parser().parse_args(['train', *common])
        original_save = trainer.save_checkpoint

        def stop_after_epoch(path, payload):
            original_save(path, payload)
            if path.name == 'last.pt' and payload['epoch'] == 1:
                raise KeyboardInterrupt

        with patch.object(trainer, 'save_checkpoint', stop_after_epoch):
            self.assertEqual(trainer.train(args, output), 130)
        resumed = self.root / 'continue'
        result = subprocess.run([sys.executable, trainer.__file__, 'train', *common,
            '--resume', str(output / 'last.pt'), '--output', str(resumed)],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with (resumed / 'epochs.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['epoch'], '2')
        self.assertEqual(rows[0]['stage'], 'fine-tune')


if __name__ == '__main__':
    unittest.main(verbosity=2)
