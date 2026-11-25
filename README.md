# Trash Bin Pro Max

A camera-based, four-bin trash sorter with removable collection bins, an overhead
camera, a central loading platform, and user feedback for improving classification.

This repository is the project home for CAD, drawings, manufacturing packages,
source files, AI training code, and project context. Files were consolidated here
on 20 November 2026. The previous `~/Files/Projects/Trash Bin Pro Max` location is
kept as a compatibility link so earlier file links continue to work.

## Start here

- [Current decisions, dimensions, and remaining work](docs/PROJECT_CONTEXT.md)
- [AI trainer and complete usage instructions](AI%20Training/README.md)
- [Related chats, datasets, and technical references](docs/REFERENCES.md)
- [Migration manifest and verification](docs/MIGRATION.json)

## Current bin design: R06

Use the complete **R06 10 mm basswood hybrid-bin** set. The older 9 mm-floor
revisions are retained for history and should not be mixed with R06 mating parts.

- [Manufacturer packet](Trash_Bin_R06_10mm_Manufacturer_Order.zip)
- [Complete R06 CAD package](Trash_Bin_Hybrid_R06_10mm_Four_Bins.zip)
- [Manufacturing and assembly guide](Rev%2006%20-%2010mm%20Basswood%20Hybrid%20Bins/PDF/Manufacturing_and_Assembly_Guide_R06.pdf)
- [Dimensioned parts and layouts](Rev%2006%20-%2010mm%20Basswood%20Hybrid%20Bins/PDF/Dimensioned_Parts_and_Layouts_R06.pdf)
- [Full-size cutting profiles](Rev%2006%20-%2010mm%20Basswood%20Hybrid%20Bins/PDF/Full_Scale_Cutting_Profiles_R06.pdf)
- [Order and testing instructions](Manufacturing%20Order%20-%20R06%2010mm%20Verified%20Parts/Repeat_Part_Order_R06.pdf)

R06 has passed recorded digital checks. Actual-stock coupons, one complete B1
prototype, and physical load tests remain necessary before full production.

## Servo sorter prototype: R07

R07 adds a six-servo Stewart sorter above the existing R06 bins, with a 2 kg
single-item payload target, four 55-degree dump directions, a reinforced post,
guides and a 750 mm external backstop frame.

- [Complete prototype package](Trash_Bin_R07_Servo_Stewart_Prototype.zip)
- [R07 files and release status](Rev%2007%20-%20Servo%20Stewart%20Sorter/README.md)
- [Assembly and manufacturing guide](Rev%2007%20-%20Servo%20Stewart%20Sorter/PDF/Manufacturing_and_Assembly_Guide_R07.pdf)

The recorded nominal CAD sweep passed 301 distinct poses; 23 software tests used
a simulated bus and clock. Physical fit, strength, impact/routing, thermal and
power-loss tests have not been performed. Full procurement remains on hold until
sample qualification and accepted quotations satisfy the hard CNY 3,000 cap.

## Train the image classifier on a Mac

The trainer recognizes one image class per folder, including the HGI-30 layout.
It automatically uses Metal/MPS on a supported Mac, with full-precision training,
parallel image loading, and lossless input caching.

```sh
cd "$HOME/Files/GitHub/Trash Bin Pro Max/AI Training"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python train_hgi30.py train --data "/absolute/path/to/HGI-30/classification"
```

Python 3.12 can be substituted for Python 3.11. See the
[trainer guide](AI%20Training/README.md) for installation compatibility, grouped
splits, logging, resume, prediction, and output files.

The script was functionally tested on CPU and Metal using synthetic images. The
user's downloaded HGI-30 dataset and a fully trained HGI-30 model are not bundled
here. No full-dataset accuracy or training time has been established.

## Repository contents

| Location | Contents |
|---|---|
| `AI Training/` | Trainer, requirements, tests, instructions, validation record |
| `Rev 06 - 10mm Basswood Hybrid Bins/` | Current CAD, exports, source geometry, PDFs, checks |
| `Rev 07 - Servo Stewart Sorter/` | Sorter prototype CAD, software, drawings, guide, BOM and digital verification |
| `Manufacturing Order - R06 10mm Verified Parts/` | Current selected part files, quantities, and order guide |
| `Rev 01` through `Rev 05` folders | Preserved historical designs and deliverables |
| Older manufacturing-order folders | Historical order packages |
| `Reference Inputs/` | Original sketch, supplied bin STL, and available reference screenshots |
| `docs/history/` | Available user-visible chat exports and original repository README |
| `docs/PROJECT_CONTEXT.md` | Consolidated project handoff and unresolved decisions |

The original [concept build plan](Build-plan.md) and root-level concept images
remain historical references. Their early dimensions do not supersede R06.
