# R07 — servo Stewart sorter prototype

This package adds a six-servo rotary Stewart platform above the existing R06 four-bin assembly. It provides editable CAD, individual manufactured parts, real DWG/DXF files, purchase specifications, calibration/motion software, and an illustrated manufacturing and assembly guide.

**Prototype only. No physical hardware tests have been performed. Full procurement is on hold: the hard ¥3,000 cap has not been demonstrated by supplier quotes.** Do not send the full quantity for production until sample interfaces, quotations and physical acceptance tests pass. This package does not replace the R06 bin manufacturing package.

## Start here

- `PDF/Manufacturing_and_Assembly_Guide_R07.pdf` — manufacturing, purchasing, assembly, wiring, calibration and physical acceptance procedures.
- `PDF/Dimensioned_Parts_R07.pdf` — top/front/right/isometric part views, envelopes and machining notes.
- `PDF/Manufacturer_Order_CN_R07.pdf` — Chinese quotation/sample instructions.
- `Manufacture_List.csv` — individual part quantities and processes; zero-quantity reference blanks are excluded.
- `03_Purchase/Purchase_List.csv` — buy specifications, with unquoted price fields.
- `03_Purchase/Budget_Quote_Check.csv` — allocation ceilings, **not market prices**.
- `Verification/Geometry_Verification.json` and `DWG_Verification.json` — actual digital results and their scope.
- `Software/README.md` — installation, simulation and attended commissioning.

## Design basis

| Item | Nominal design |
|---|---|
| Payload | One item, up to 2 kg; physical qualification pending |
| Item envelope | Bottle laid flat, up to 320 × Ø100 mm; paper ball up to Ø120 mm |
| Moving hardware allowance | 1.3 kg, including conservatively counted full link tubes |
| Tray | 360 × 360 × 1 mm aluminium, 15 mm corner chamfers, four U-channel braces and perimeter frame |
| Dump motion | 55° tilt, 85 mm translation toward a selected quadrant |
| Actuators | Six Hiwonder HTD-85H, 20T:36T HTD5M reduction |
| Belt / idler | 360-5M-15, with bearing-supported 20T toothed INSIDE idler; confirm one real cell |
| Link centre length | 297.080 ±0.20 mm; six identical tube blanks 249.080 ±0.10 mm |
| Crank centre length | 100.5 mm |
| Central post | Ø147.5 × 512.5 mm external envelope, structural Ø60 × 3 steel core with endcaps |
| Crank shaft level | Global Z640 mm |
| Level / active tray surface | Z858.6 / Z898.6 mm |
| Chutes | R200/Z750 inlet → R240/Z630 knee → R254/Z480 outlet |
| Original base / external frame | 700 × 700 mm / 750 × 750 mm; outer posts 820 mm |
| Bins | Existing R06, nominal rims Z470 mm in this assembled reference |

B1 is +X/+Y, B2 −X/+Y, B3 +X/−Y, B4 −X/−Y. STEP assembly names and `Software/configuration.json` establish the coordinate system. Resting pads relieve the level tray; they do not passively support every off-centre 2 kg load with the motors unpowered.

## Manufacture files correctly

`01_Metal` contains metal parts; `02_Print` contains PETG/TPU parts and disposable jigs. `04_Assembly` contains level, four dump poses, an exploded reference, and the complete system with unchanged R06 bin solids. Assembly STLs are viewing references, not one-piece print jobs. Purchased parts in `03_Purchase` are simplified envelopes, not supplier-certified fabrication drawings.

Cut only CUT-layer contours in millimetres at 1:1. The bearing and crank shaft holes in the cutting files are deliberately rough-sized: Ø21.5 → finish Ø22 H7 and Ø7.5 → finish Ø8 H7. STEP shows finished geometry. Apply measured kerf compensation once. Reference projections for turned, printed and formed parts are **not** cutting patterns. M09 carrier joint holes are inclined taps; use `Carrier_Joint_Hole_Axes.csv`, not vertical laser holes. `Flat_Profile_Dimensions.csv` records profile coordinates and rough/finished hole diameters.

Rear M05 cheeks repeat six times. Finished FRONT M05 and M17 cheeks have drive-specific stop holes/reliefs and retain D1–D6 labels. P09 socket wedges retain L1–L6 labels. Do not order zero-quantity blanks in addition to finished variants. All six tubes, twelve crank plates and four guides are repeated parts. The servo adapter is match-drilled only after receiving the actual matched metal horn.

The Ø147.5 shroud uses a butt seam with an internal splice; an external overlap will not fit the Ø147.7 base pocket. Weld the six underside deck ribs and captive top-cap nuts before final machining/assembly. Base modification includes six central mounting holes and sixteen countersunk corner holes.

## Verification scope

The verification report records STEP validity, one-solid part exports, watertight STL meshes, sampled kinematics, joint articulation, torque equilibrium, shaft/link engineering screens, dimensional perturbations, and sampled solid interference against nominal CAD and purchased envelopes. DWGs are converted to R2000 with ODA, round-tripped to DXF and independently read with LibreDWG.

These checks do not prove continuous collision clearance, printed strength/creep, weld quality, belt life, servo continuous torque, cable/wire routing, actual part fits, impact containment or successful trash discharge. Actual motor current/temperature and the manufacturer's unpublished continuous torque must be qualified. Set items down gently; impact loading onto the tray is unqualified. The bin-bottom cushioning in the purchase list is a trial component and must be qualified under the intended drops and bin fill levels. Hardware defaults remain uncalibrated and unqualified. A missed/bridged item blocks automatic return; unknown startup poses require supported manual recovery.

First quote the complete bill, then approve one servo/cell and one rod sample before the remaining sets. Keep the R06 plywood fit samples and load tests as independent requirements. The guide supplies blank acceptance records and a staged physical test sequence. No purchases or supplier messages have been made.

## Rebuild

Use Python3.11 with Source/requirements-build.txt and follow the ordered workflow in Source/README.md. The final layer checks run after CAD generation. DWG conversion needs separately installed ODA File Converter and LibreDWG; complete-system rebuilding also reads the sibling R06 STEP files. The PDF generator needs an embedded Chinese-capable TrueType font.
