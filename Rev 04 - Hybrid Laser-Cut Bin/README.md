# Trash Bin Pro Max - R04 hybrid bin

The files describe one removable bin with a **347.5 x 347.5 x 450 mm** outside envelope. The attached Bin Studio STL is the geometry reference. This revision uses four **6 mm birch plywood walls**, one **9 mm plywood floor**, a **PETG curved corner**, and four **PETG magnet-pocket inserts**. Multiply the quantities by four for the four-bin system.

The current working-load target is **10 kg per bin**, covering the requested 5-10 kg range. A **15 kg supported physical proof-test procedure** and a **10 kg handling trial** are in the drawing booklet. These physical tests have not been performed. The geometry and export checks are recorded in Verification.json.

## Start with the drawings

Open `PDF/Drawings_Assembly_and_Verification.pdf` for part dimensions, coupon instructions, assembly order, print notes, drilling operations, test results and the physical acceptance procedure. `PDF/Full_Scale_Cutting_Profiles.pdf` contains one 1:1 vector cutting page per plywood component or calibration piece. Print at actual size and measure its 100 mm scale bar. Disable page fitting.

The drawing files are marked **NOMINAL STOCK - CALIBRATE BEFORE FULL CUT**. Actual plywood thickness, laser kerf, material distortion and printed fit affect assembly. Use the small coupons with the same stock, laser settings and print orientation before ordering a complete bin.

## Files and quantities

| ID | Part | Quantity per bin | Main dimensions, mm |
| --- | --- | ---: | --- |
| W01 | Rear wall | 1 | 347.5 overall length x 450 overall height x 6 |
| W02 | Right wall | 1 | 347.5 overall length x 450 overall height x 6 |
| W03 | Front short wall | 1 | 253.5 including fingers x 450 overall height x 6 |
| W04 | Left short wall | 1 | 253.5 including fingers x 450 overall height x 6 |
| F01 | Floor | 1 | 347.5 x 347.5 x 9, shaped corner R75 |
| C01 | Printed curve with screw flanges and floor pads | 1 | 130 x 130 x 450 bounding box, nominal R75/R81 shell |
| M01 | Printed magnet insert | 4 | Diameter 29.2 x 9 high, underside pocket diameter 25.2 x 5 deep |

The short walls have a 247.5 mm body starting at source station 102.5, with fingers reaching station 96.5. All component STL and STEP files use source coordinates and mm units. The insert model is centered at its own XY origin. The assembly STEP includes the four positioned inserts. The assembly STL is a viewing model with touching structural surfaces fused to keep the mesh watertight. Use the individual component STLs for printing.

Each production component has an STL and a solid STEP. Each plywood part has a DWG cutting outline. The curve and insert DWGs contain reference projections. DWGs use R2000 format, millimetre units, CUT geometry, and a separate REFERENCE layer for identifiers and sample labels. The curve reference DWG shows cross-sections at Z13 and Z225 and a side silhouette. Those views describe a printed part.

## Calibration pieces

- **Q01_wall_fit** is a 200 x 180 coupon in 6 mm stock. Its lower two rows test the 6 mm wall interface with 36 mm fingers. The upper two rows test a 9 mm floor tongue with a 30 mm finger. Seven choices run from 0.10 through 0.40 total gap in 0.05 increments.
- **Q02_floor_fit** is a 200 x 100 coupon in 9 mm stock. It tests the 6 mm wall tabs against floor slots. Use the 30-wide, 6-thick Q08 wall-tab sample for these slots. Also measure actual sheet thickness directly. The extra 4.5 mm hole at (175,87) tests the small floor-bolt hole in 9 mm stock. Verify it with the actual M4 shaft and a countersink sample.
- Both Q01 and Q02 contain a 20 x 20 square plug at X165-185, Y55-75. The gap between the plug and opening represents two beam widths. Estimate kerf as **(opening size - plug size) / 2**, independently in X and Y. Record a kerf for each thickness. Keep the plug labeled with its stock.
- **Q03_wall_tab**, **Q04_floor_tab** and **Q08_floor_wall_tab** are small matching-width tongue samples. Q03 is a 36-wide tongue in 6 mm stock. Q04 is 30 wide in 9 mm stock, and Q08 is 30 wide in 6 mm stock. Their 50 mm bodies provide space to hold them during fitting.
- **Q05_curve_joint_sample** is a full-scale crop of the actual printed wing, 42.5 x 11 x 72 mm. Print it with the same vertical layer direction as C01. Pair it with **Q06_curve_wall_sample**, cut from 6 mm stock, to check the finger and nut fit. The coupon uses the design's nominal 0.30 mm gap. Change `printed_joint_gap` and regenerate if needed.
- **Q07_insert_fit**, cut from 9 mm stock, tests 0.10, 0.20 and 0.30 mm radial clearance around the actual M01 insert. Default floor holes are diameter 29.6, for 0.20 radial clearance around diameter 29.2.

Choose a sliding fit that seats by hand. Measure actual wall and floor sheet thicknesses and update the parameters before regenerating the full profiles. The nominal vertical finger dimensions provide 0.20 total wood-to-wood clearance and 0.30 total wood-to-printed clearance. The floor fingers are 30 wide, with 0.20 total tangential clearance in the plywood notches. Three curved floor locating tabs use 0.30 total clearance.

## Cutting and secondary operations

The CUT outlines describe the intended finished contour, including joint clearance. **The profiles contain no kerf offset.** Give measured kerf to the laser shop and apply compensation once. Ignore the REFERENCE layer when cutting. Cut the coupons in the actual 6 and 9 mm stock first to confirm that the shop can cut it cleanly and through its full depth. Sand loose char off bonding faces without changing their dimensions.

After laser cutting, countersink the three holes on the exterior face of each short wall to **diameter 6.3 x 90 degrees**. Countersink the three small floor holes from below to **diameter 8 x 90 degrees**. The STEP/STL models include these countersinks. The laser profiles contain their smaller through-hole diameters, **3.4 and 4.5**, for this secondary drill operation. Verify the final seats with the selected screw heads so no head protrudes beyond the original exterior envelope.

The floor-to-curve holes are on radius 100, at 22.5, 45 and 67.5 degrees from source +X. The print has three 8-high bolting pads above the floor. This mechanical attachment was added for the 10 kg target. Two 5-thick interior flanges support the six M3 curve-to-wall screws.

## Printing and hardware

Print C01 upright, full 450 mm height, on a suitable large-format printer. Use PETG, six perimeters as a starting profile, and inspect the slicer to make the 6 mm shell substantially solid. The floor pads, flange starts, finger undersides and nut traps need suitable supports. Check the Q05 sample before committing to the full-height print. The orientation, bonding and physical tests must establish whether the finished print is acceptable.

Print M01 with its closed roof on the bed and pocket upward, then flip for installation. Keep it flush on both faces of the floor when bonding. Use a compatible two-part epoxy on prepared PETG and wood surfaces. Keep adhesive out of the magnet pocket and measure the recess after curing.

For each bin, use **six M3 x 12 countersunk screws and six M3 nuts**, plus **three M4 x 20 countersunk screws and three M4 nuts**. Nut traps are 5.8 mm across flats x 2.6 deep for M3, and 7.2 mm across flats x 3.4 deep for M4. The nut pockets open toward the inside of the bin. Check the purchased M3 nuts in Q05 and verify the M4 pockets in the first printed curve. Use structural wood glue suited to the plywood and allow its full specified cure. Magnets remain purchased parts, selected to fit the original diameter 25.2 x 5 recesses.

## Validation performed

Verification.json records the numerical checks. These include single valid solids, watertight part meshes, STEP reimport volumes, STL volume fidelity, final interference, continuous insertion sweeps, closed and nonduplicated cutting contours, isolated-hole wood ligaments, and DWG geometry/units after round-trip conversion. ODA 27.10 writes the final DWGs, and LibreDWG 0.14 provides an independent read. The first open-source DWG writing route failed validation and was replaced.

The floor screening model assumes a uniformly distributed payload on a simply supported, 335.5 mm span and width, with plywood modulus **3,000 MPa**. At 10 kg it estimates **0.79 mm** deflection and **0.91 MPa** bending stress. At 15 kg the estimates are **1.18 mm** and **1.36 MPa**. Local pockets, grain direction, glue joints, laser damage, moisture and concentrated loads require evaluation on the actual sample. These calculations establish a preliminary target, not a certified capacity.

## Rebuild from parameters

Use Python 3.11 with the libraries in `Source/requirements.txt`. Install the ODA File Converter and LibreDWG. Set `ODA_CONVERTER` to the executable path if it is outside `/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter`. Edit `Source/parameters.json` for measured thicknesses and selected gaps. Kerf values are recorded for the laser shop and do not alter these finished-size outlines. Run the three scripts in this order from the package directory.

```sh
python Source/build_bin.py
python Source/finish_package.py
python Source/draw_package.py
```

The source scripts are included so calibrated files can be regenerated from the same CAD geometry. Source coordinate X/Y ranges, curve size and overall height match the supplied model. Inspect the regenerated drawings and rerun the checks after changing parameters. Geometry features are nominal targets, while actual fit depends on the coupon results.
