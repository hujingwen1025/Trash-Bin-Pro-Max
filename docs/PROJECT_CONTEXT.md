# Project context

Consolidated on 20 November 2026 from the saved project files and the available
user-visible messages in the mechanical-design, material/manufacturing, and
camera/classification chats. This is a handoff, not a new engineering validation.

## Purpose and intended operation

Trash Bin Pro Max identifies one waste item at a time on a central loading deck
and routes it toward one of four removable bins. An overhead camera and presence
sensor provide inputs. A Raspberry Pi performs image inference; an LCD and user
controls display the proposed classification and allow corrections. Corrected
examples can be reviewed and used in periodic supervised retraining. A correction
does not update the deployed model automatically.

The original sketch described a 6-DOF platform. The user deferred that mechanism
while the bins were developed, then authorized the R07 six-servo rotary Stewart
sorter. R07 now contains prototype CAD, sampled kinematic/solid checks and guarded
motion software. Physical qualification and procurement remain open.

## Current bin design: R06

| Item | Current information |
|---|---|
| Arrangement | Four mirrored bins around a central post |
| Individual nominal bin envelope | 347.5 x 347.5 x 450 mm |
| Four-bin layout | Nominal 700 x 700 x 450 mm |
| Central post | User-confirmed diameter 147.5 mm |
| Exposed curved face | Nominal R75, giving 1.25 mm nominal radial post clearance |
| Walls | Nominal 6 mm plywood |
| Floor | Nominal 10 mm plywood, replacing the previous 9 mm floor |
| Working wood material | Basswood plywood inferred from supplier listing: 椴木板三合板 |
| Supplier thickness variation | Interpreted conservatively as approximately +/-0.2 mm |
| Curved corner and inserts | PETG prints, with mechanical fasteners and specified joints |
| Load objective | 10 kg per bin; physical testing still required |

The manufacturer offered 10 mm floors rather than 9 mm. R06 updates the wall
tabs, curved-part floor interface, magnet inserts, fasteners, fit samples, and
order packet together. Use R06 as a complete set; do not mix R05/R04 floors or
mating parts into it. The material listing is not a certified wood grade or
stiffness specification.

The final mechanical chat reports 235 model/export checks, 51 thickness checks,
and 24 repeated-part checks passing. The checked thickness ranges are 5.8-6.2 mm
walls and 9.8-10.2 mm floors; the reported minimum inter-bin clearance is 4.6 mm
under the checked variations and locating conditions. These are recorded digital
results, not a fresh simulation or proof of manufactured strength. Refer to the
R06 verification files and assembly instructions for the exact conditions.

Manufacturing release sequence: produce the supplied fit coupons, including
Q09/Q10 floor-interface samples; confirm actual stock, kerf, and printed fits;
assemble and test one full B1 bin; then release the remaining parts. The original
10 kg target and 15 kg supported proof-test procedure require physical trials.

## R07 sorter prototype

Use `Rev 07 - Servo Stewart Sorter/README.md` and its current verification files
for the sorter. R07 complements R06; it does not replace the R06 bin parts.

| Item | R07 nominal design / recorded status |
|---|---|
| Payload | One item up to 2 kg; physical qualification pending |
| Moving hardware model | 1.3 kg; CAD plus 0.2 kg hardware allowance totals about 1.261 kg |
| Motion | Four 55-degree tilt poses with 85 mm translation |
| Servos / transmission | Six HTD-85H; 20T:36T HTD5M, 360-5M-15 belt and 20T toothed inside idler |
| Crank / link centres | 100.5 / 297.080 mm; identical link tubes 249.080 mm |
| Base / top anchor radii | 130 / 66.1 mm |
| Post | 147.5 OD x512.5 mm envelope; 60 OD x3 steel core and two 6 mm endcaps |
| Fixed deck | 6 mm aluminium, maximum OD540, six underside ribs phased 24.9 degrees |
| Shaft / tray heights | Shaft axes Z640; resting tray top Z858.6; active tray top Z898.6 |
| Upper assembly | Carrier underside 13 mm, tray top 23 mm above upper joint plane |
| Upper joints | 16 mm balls, 16.3 mm cavities; labelled socket wedges and inclined carrier taps |
| Carrier machining | Positive bosses around taps; socket ears clocked +/-11 degrees; use hole-axis CSV |
| Guides | Four one-piece prints, 360 mm floor width; R200/Z750 to R240/Z630 to R254/Z480 |
| Backstop frame | 750 mm square; posts820, side rails710 at Z500/800; padded360x300 panels |
| Guide supports | 92 mm 2020 posts at radial205, tangent+/-150 mm |
| Digital evidence | 86 CAD/engineering checks, 301 distinct sampled solid poses, 65 cutting/reference file checks and 65 DWG round trips/independent reads |
| Software evidence | 23 simulated-bus/clock tests; includes USB latency budgeting and fault behaviour |
| Physical tests | None performed; flags remain uncalibrated and unqualified |
| Procurement | HOLD; hard CNY3,000 cap, no accepted quotations or purchases |

The calculated factored motor torque is about3.825 Nm using a1.5 load factor,
2 kg at a conservative245 mm CG radius/83 mm height, and1.3 kg moving hardware.
The servo's published stall rating is not a continuous rating; thermal duty is
unqualified. Sampled collision checks do not prove continuous clearance, actual
manufacturing tolerances, wire/cable routing or successful trash discharge.

The package contains individual STEP/STL/DXF/DWG files, level/four dump/exploded
assemblies, a complete system reference with the R06 bins, three PDFs, quantities,
purchase specifications and runnable simulation/calibration/motion software.
Purchased CAD is schematic envelope data. Confirm the actual servo/horn, bearing,
pulley, belt, key, insert and fastener stacks on one cell/rod before the full set.
Manufacture only the positive-quantity parts in its CSV; zero-quantity blanks are
reference-only. Angled taps require secondary machining; rough laser bores leave
stock for reaming. The original base gets six central and sixteen corner holes.

Normal hardware motion requires recorded calibration and physical qualification;
attended commissioning has a separate explicit option. Unknown startup poses
block motion. Empty/free-of-bridging confirmation is required before returning
from a dump, including the home command. Feedback during motion rotates two
transactions per50 ms frame; actual USB timing still needs qualification. Faults
hold the last commanded positions while power remains; the independent DC stop
and supported recovery are required. Central resting pads are not a passive
support for every off-centre load.

Set items down gently. The early30 mm placement-drop note was withdrawn by a
documented annotation-only correction; impact loading is unqualified. Bin-bottom
cushioning is a trial purchase specification, initially150 mm, requiring supplier
data and progressive tests with empty/part-filled bins. R06 static capacity does
not establish impact capacity. Rubber foot head/nut reliefs also require the
finishing CSV and actual hardware trial. Full load, thermal, routing, restrained
power-loss and bin-removal tests are listed in the guide and blank test record.

The latest `Geometry_Verification.json` governs the nominal digital result.
`Verification/History/` preserves rejected intermediate sweeps. A subsequent
annotation-only correction withdrew the unqualified drop note without changing
CAD geometry; its hashes are recorded separately. Drawing envelopes were then recalculated from exact analytic solids to remove cached bounding margins; no STEP/STL geometry changed, and every corrected box is contained in the conservative boxes used for the successful sweep. Final64-part exports were rechecked. No supplier messages were sent.

## Repeated-part ordering

The four bins do not require twenty different cutting patterns. The verified
order uses four representative laser-cut patterns for twenty plywood blanks:
four W01, four W02, eight short-wall W03/W04 blanks, and four F01 floors. The
short walls need two finishing batches with countersinks on opposite faces.
Printed curves use two copies of each of two handed templates, plus sixteen
common magnet inserts. Use the R06 order CSVs and selected files for exact
quantities, finishing faces, copy labels, and calibration parts. R05 order
documents describe the superseded 9 mm-floor version.

## Historical geometry and manufacturing decisions

- The initial R00 concept used a 540 mm square cabinet and a smaller deck. It is
  preserved in `Build-plan.md` and the concept images, not the current bin CAD.
- R01-R03 explored a 760 mm square cabinet, an approximately 785 mm overall width
  including the display, a 380 mm diameter loading deck at 750 mm height, and a
  camera lens about 440 mm above the deck. These are earlier system-layout
  proposals and need reconciliation with the later 700 mm four-bin assembly.
- The earlier target item envelope included an empty bottle laid flat, up to
  320 mm long and 100 mm diameter, and crumpled paper up to 120 mm across.
  Discharge and clearance for that range have not been physically established.
- The user requested one-piece printed components at one stage. Large liners,
  full-height curves, cabinet sections, and the mast exceed an H2D's published
  usable dimensions in the proposed orientations. Later hybrid bins use
  laser-cut plywood and printed curves.
- A 5,000 CNY prototype budget was stated in the materials/manufacturing chat.
  Supplier recommendations and cost estimates in that chat were planning advice,
  not accepted quotations. No current supplier price or order is established here.

## Camera and classification approach

The suggested first vision setup is one Raspberry Pi Camera Module 3 Wide in
visible light, an existing Pi 4B if available or a Pi 5 when buying new, diffused
white illumination, and a matte washable platform. It was a recommendation;
purchase or installation has not been confirmed.

The earlier 440 mm lens-to-deck spacing does not cover a full 380 mm circular
deck along the short image dimension with the standard Camera Module 3 viewing
angles. The Wide version was recommended based on calculated coverage. Verify
the actual capture mode, field of view, focus, and coverage with tall objects
before fixing a mount. Lighting and camera photos from the real platform matter
more than training solely against downloaded dataset scores.

The four destination categories remain unnamed in the original plan (A-D).
Train item/material recognition separately from the mapping to local sorting
categories. A visible plastic item is not enough to establish contamination,
hidden contents, or final disposal rules. Include an unsure/manual outcome and
an empty-platform condition. Recognition should be demonstrated before automatic
motion is connected.

## HGI-30 and Mac training

The user downloaded HGI-30 and initially used Teachable Machine. Its displayed
baseline settings were 50 epochs, batch size 16, and learning rate 0.001. The
user then requested a Python trainer with detailed logging and Mac acceleration.

`AI Training/train_hgi30.py` supports the user's folder layout directly:
`classification/<class_name>/<image>`. It recognizes folder names such as
`applecore`, `banana_peel`, `battery_button`, and `glassbottle` without a hardcoded
class-name map. Normal HGI-30 has 30 classes; the script warns rather than fails
if a subset or extra class is used.

Implemented default recipe: ImageNet-pretrained EfficientNet-B0; square padding
and 224 x 224 input; three classifier-only warm-up epochs; full fine-tuning up
to 40 total epochs; batch size 32; AdamW; separate backbone/head learning rates
with cosine decay; label smoothing; early stopping by validation macro-F1.
It automatically chooses MPS on a supported Mac and keeps training in float32.
Parallel loading and an exactly matched, lossless resized-image cache accelerate
input handling. These are practical defaults, not a proven optimum for HGI-30.

The trainer saves image audits, repeatable split manifests, batch JSONL events,
readable logs, epoch CSVs, best/last checkpoints, per-class results, confusion
matrices, and held-out predictions. It supports optional physical-item grouping
CSV files, checkpoint resume, and prediction from a new photograph.

Nine automated tests and a real MPS forward/backward training smoke test passed
on native arm64 Python 3.11, PyTorch 2.15, and torchvision 0.29.2. The tests used
synthetic images. No full HGI-30 training run or real-camera accuracy assessment
was performed. The downloaded dataset's filesystem location was not supplied
and it was not present in the saved project folder; it is not bundled here.
The standard ImageNet initialization downloads automatically on first real use.

HGI-30 contains augmented/repeated views. Exact RGB duplicate removal alone
does not prevent the same physical item or a transformed version appearing in
multiple splits. Supply group identities where known and reserve new physical
items photographed on the real bin for an independent evaluation.

## Remaining work

1. Validate supplier stock and R06 coupon fits, then one complete B1 and its loads.
2. Trial-fit the R07 post/base interface and actual supplier hardware; confirm base material and backing support.
3. Define destination categories and their mapping to the trained class labels.
4. Train on the actual HGI-30 images, reviewing grouped validation and errors.
5. Add camera/platform images, empty platform, and appropriate hand-presence data.
6. Select camera/computer hardware and verify mounted coverage and lighting.
7. Build one R07 sample, qualify loads/heat/impact/drop paths and verify quotes before full manufacture.
8. Integrate sensing, inference, display, correction logging, and motion control.

## Information provenance

See `docs/history/` for snapshots of the user-visible messages returned by the
connected chat reader, including the material and vision discussions. They are
the available exported context, not a claim that omitted uploads or every older
ChatGPT message was recoverable. Tool traces and internal reasoning are excluded.
Original attachments available by filesystem path are copied to `Reference Inputs/`.
Their origins and hashes, plus every migrated project file, are recorded in
`docs/MIGRATION.json`. Historical links retain their original destinations for
provenance; the compatibility link resolves prior local project paths.

## R07 illustrated guide update (20 November 2026)

Visual update A adds 13 labelled stage-specific assembly illustrations, exploded joint/tray details, insertion arrows and a shared muted component colour key. Platform preview renders and the overall drawing sheet use the same differentiated colours. The renderer reads existing STEP assemblies without rebuilding CAD. The pre-update package is preserved in `docs/history/R07_Visual_Update/`. This is a documentation/presentation change; engineering files, quantities, control software and the prototype qualification status remain unchanged.

## Supplied-bin STL compatibility check (25 November 2026)

The newly supplied `Bin Studio - Bin (3).stl` (SHA256 `c452d0375a0c02c11b28c5ee07e32fef5f45eb4944629ee5cd9ec087e5026649`) has the same 347.5 x 347.5 x 450 envelope, nominal R75 post-facing curve and 10 mm floor, but 5 mm walls and approximately R80 trash-facing curve. R06 C01 is designed for 6 mm walls/R81 inner curve and the matching R06 finger-jointed panels, three floor-tab slots and side/floor fasteners. Fresh STL sections and all nine nominal fastener-axis probes confirm the supplied monolithic bin lacks those interfaces. It is not a direct-fit mating model for C01; R06 C01 remains the intended part for the complete R06 panel set. The upload coordinates correspond to B1 (+X,+Y); the filename suffix is not a variant ID. All four released C01 meshes passed fresh topology/envelope checks. All 239 existing R06 files remained unchanged. No physical fit/load tests were performed. Evidence is in `Checks/R06 C01 Compatibility - 2026-11-25/`; the uploaded STL is preserved in `Reference Inputs/`.
