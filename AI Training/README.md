# HGI-30 training on a Mac

This package trains an image classifier from your existing folder layout. It uses
PyTorch and pretrained EfficientNet-B0 by default, with a brief classifier warm-up
and then full fine-tuning. It does not require Teachable Machine or a paid API.

The settings are a practical starting recipe, not hyperparameters empirically
proven optimal for your copy of HGI-30. No HGI-30 accuracy is promised. The trained
model recognizes your folder labels; choosing the destination trash bin remains
a separate mapping based on the sorting rules you use.

## Install

Use native Apple Silicon Python 3.11 or 3.12 on an M-series Mac. Python 3.11 was
used for the package tests. Use a CPU-compatible PyTorch release if your Mac or
macOS cannot run MPS. Avoid a Python running under Rosetta when you want Metal.

In Terminal:

```sh
cd "$HOME/Files/Projects/Trash Bin Pro Max/AI Training"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If you have Python 3.12 instead, substitute `python3.12` in the environment command.
On a machine without either version, install a compatible Python first. PyTorch's
current Python/macOS requirements vary by release; use the installer linked below
if pip cannot find a compatible wheel. Install PyTorch and torchvision together.

The first training run downloads the standard ImageNet weights, about 21 MB for
EfficientNet-B0, to PyTorch's normal cache. Training then runs locally. For an
offline machine, preload the same torchvision weights; `--no-pretrained` is for
smoke tests and should not be used for your real training.

## Folder layout

Point `--data` at `classification`, not its parent and not a single class folder:

```text
classification/
  applecore/
    applecore0001.jpg
    applecore0002.jpg
  banana_peel/
    banana_peel0001.jpg
  battery_button/
    battery_button0001.jpg
  ...
```

Folder names become labels automatically and are sorted consistently. Images in
nested folders under a class are supported. Hidden files, Apple `._` files, and
`__MACOSX` directories are ignored. Supported formats: JPEG, PNG, BMP, WebP, TIFF.
The script does not modify, move, or delete your original images.

## Start training

```sh
python train_hgi30.py train --data "/absolute/path/to/HGI-30/classification"
```

That is enough. The script automatically selects MPS if available, otherwise
CUDA if available, otherwise CPU, and prints the actual device. Output goes into
a new dated folder under `AI Training/runs/`. To choose its name:

```sh
python train_hgi30.py train \
  --data "/absolute/path/to/HGI-30/classification" \
  --output "runs/hgi30-first"
```

Output folders must be new or empty. Keep runs and the image cache outside the
classification folder so generated files cannot become accidental classes.

To inspect image integrity, duplicates, counts, and splits without downloading
weights or training:

```sh
python train_hgi30.py inspect --data "/absolute/path/to/HGI-30/classification"
```

## Default training recipe

| Setting | Default |
|---|---|
| Network | EfficientNet-B0 initialized with ImageNet weights |
| Input | 224 x 224 RGB; full image padded to a square, then resized |
| Precision | Float32; no mixed precision, quantization, or fast-math toggle |
| Split | Approximately 70% train, 15% validation, 15% test within each class |
| Classifier warm-up | 3 epochs; backbone and its BatchNorm statistics frozen |
| Full fine-tuning | Up to epoch 40, including the warm-up |
| Optimizer | AdamW, weight decay 0.0001, gradient norm clipped to 1 |
| Warm-up classifier learning rate | 0.001 |
| Fine-tuning learning rates | Backbone 0.00003, classifier 0.0003 |
| Schedule | Cosine decay during fine-tuning, down to 5% of initial rates |
| Batch size | 32 |
| Label smoothing | 0.05 for training; unsmoothed evaluation |
| Augmentation | Mild rotation, horizontal flips, brightness/contrast/saturation |
| Best checkpoint | Highest validation macro-F1, which weights each class equally |
| Early stopping | 8 fine-tuning epochs without sufficient validation improvement |
| Image-loader processes | 2 persistent workers, using macOS-compatible spawn |

These settings differ from Teachable Machine because this script fine-tunes the
backbone, rather than only training a classifier over fixed image features.
This is a new training run; it does not import your Teachable Machine project.

Training logs show wall-clock timestamps, image audit progress, class counts,
stage and learning rates, batch/epoch losses, accuracy, throughput, ETA, device
tensor memory, validation macro-F1, the five weakest classes, and checkpoint/early
stopping decisions. Throughput includes data loading and startup overhead; the
first batch is often slower due to Metal setup and worker startup. Device tensor
memory is not total process/unified memory.

## Mac acceleration and image quality

- **MPS/Metal GPU:** automatic, with the same float32 network and input resolution.
  `--device mps` requires GPU support and fails clearly if it is unavailable.
  Float32 GPU and CPU results can still differ numerically; compare validation
  quality rather than expecting identical predictions in every run.
- **Lossless input cache:** enabled by default in `AI Training/.image-cache/`.
  It stores the exact same padded/resized pixels the model would otherwise read
  on each epoch, as lossless PNGs. Augmentation still runs freshly every epoch.
  This saves repeated decoding of large JPEGs; it does not change the network's
  input pixels. Cache creation takes time on the first run and uses disk space
  (allow a few GB for 18,000 images). Subsequent runs reuse it by pixel hash and
  input size. `--cache-dir /path/outside/dataset` chooses another location;
  `--no-cache` disables it. Delete damaged cache files to regenerate them.
- **Parallel loading:** two persistent subprocesses decode/augment upcoming
  batches. You can try `--workers 4` if loading is the bottleneck; more workers
  consume RAM and are not always faster. `--workers 0` helps troubleshoot.
- **No quality shortcuts enabled:** the default does not use half precision,
  model quantization, a smaller replacement network, or MPS fast math. It also
  does not disable PyTorch's GPU memory safety limits or enable CPU fallback
  silently. Environment variables you set externally can change that behavior;
  they are recorded in `runtime.json`.

Start with batch size 32. If you hit GPU/unified-memory errors, try
`--batch-size 16` in a new run. This keeps image resolution and architecture,
but changes optimization dynamics; compare validation scores. Larger batches
are not guaranteed to improve speed or accuracy. If image details are limiting
quality, you can experiment with `--image-size 320`, accepting more computation
and memory. That is a separate experiment, not the default.

You can prevent sleep during a long run with macOS's built-in command:

```sh
caffeinate -i python train_hgi30.py train \
  --data "/absolute/path/to/HGI-30/classification"
```

## Dataset leakage and trustworthy evaluation

The scanner fully decodes images and hashes their oriented RGB pixels. It removes
exact duplicates within a class from the working index, leaving originals intact.
Identical images with different class labels stop the run for correction.
Unreadable images also stop the run; use `--skip-corrupt` only after reviewing
`data_audit.json`.

**The split is not automatically physical-item independent.** HGI-30 includes
augmented images and repeated viewpoints. A rotated/noisy copy or another photo
of the same bottle can evade exact deduplication and inflate validation/test
scores. Filenames alone do not reliably identify those relationships, so the
script does not guess. If you know the related images, supply a complete CSV:

```csv
path,group_id
applecore/applecore0001.jpg,applecore-item-001
applecore/applecore0002.jpg,applecore-item-001
applecore/applecore0003.jpg,applecore-item-002
```

```sh
python train_hgi30.py train \
  --data "/absolute/path/to/HGI-30/classification" \
  --groups-csv "/absolute/path/to/groups.csv"
```

The CSV must contain every retained image. Use relative paths with the class
folder included. Group IDs must be unique across physical items and each group
must belong to one class. All augmented variants and viewpoints of an item
should share its group ID. You need at least 3 independent groups per class.
Splitting is stratified by group count; image-count percentages may vary when
group sizes differ. Without a CSV, individual unique images are the groups.

Keep an additional evaluation set of new physical items photographed using your
actual overhead camera, deck, and lighting. HGI-30 results alone do not establish
how accurately the complete trash bin will work. Add empty-platform and
hand-present data if you want those labels; the model does not discover them
automatically. Softmax confidence is not a calibrated probability or a reliable
unknown-object detector. Do not repeatedly tune settings against the test split;
use validation results for choices and reserve the test split for final checks.

## Outputs

| File | Contents |
|---|---|
| `best.pt` | Selected weights, class labels, model name, preprocessing, settings |
| `last.pt` | Last complete epoch, optimizer state, plus the best model snapshot for resume |
| `labels.json` | Class names and their output indices |
| `training.log` | Readable timestamped training and error log |
| `events.jsonl` | Machine-readable batch and epoch events |
| `epochs.csv` | Learning rates, training/validation loss, accuracy, macro-F1, timing |
| `splits.json` | Original relative paths, image hashes, group IDs, and split assignment |
| `data_audit.json` | Removed duplicates, corrupt files, and conflicting labels |
| `config.json`, `runtime.json` | Arguments, versions, device, precision, and environment |
| `best_validation_*` | Best validation metrics, per-class scores, confusion matrix |
| `test_*` | Held-out test metrics, per-class scores, confusion matrix, predictions |

Loss values use different training/evaluation objectives: training may include
label smoothing and optional `--class-weights`; validation/test use ordinary
unweighted cross-entropy. Accuracy and macro-F1 are comparable, but a training
loss higher than validation loss alone does not indicate a bug.

## Resume after interruption

Press Ctrl+C to stop. The checkpoint is saved after each complete epoch; work in
the interrupted epoch must be repeated. Resume `last.pt`, not `best.pt`:

```sh
python train_hgi30.py train \
  --data "/absolute/path/to/HGI-30/classification" \
  --resume "runs/hgi30-first/last.pt" \
  --output "runs/hgi30-continued"
```

Use the original training arguments, including any non-default batch size, model,
epoch budget, resolution, split seed/fractions, or group CSV. The dataset and
split fingerprint must match. Existing outputs are never overwritten. History
from before the checkpoint stays in the original run folder. The best model
snapshot is carried into the new folder even if later epochs do not improve.
Weights and optimizer state resume, but random augmentation streams, worker
state, and accelerator nondeterminism are not restored bit for bit.

## Predict a new photograph

```sh
python train_hgi30.py predict \
  --checkpoint "runs/hgi30-first/best.pt" \
  --image "/absolute/path/to/new-trash-photo.jpg"
```

This uses the same evaluation preprocessing and prints the five highest class
scores. It needs no weight download. Checkpoints are PyTorch models, not
Teachable Machine or Core ML exports. A Raspberry Pi deployment can use the
saved labels and preprocessing, but camera capture, category mapping, and
actuator control are separate tasks.

## Tests and references

```sh
python -m unittest -v test_trainer
```

Tests use tiny synthetic images and random initialization; they verify software
behavior, not HGI-30 accuracy. See `VALIDATION.txt` for the actual checks run for
this package and the tested versions.

- [Apple: Accelerated PyTorch training on Mac](https://developer.apple.com/metal/pytorch/)
- [PyTorch MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html)
- [Torchvision EfficientNet-B0 weights](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)
- [PyTorch installation](https://pytorch.org/get-started/locally/)
- [HGI-30 paper](https://arxiv.org/html/2202.11878v1)
