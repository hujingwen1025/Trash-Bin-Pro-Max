# R06 - 6 mm walls / 10 mm floors / four mirrored hybrid bins

Use this complete revision in place of R04/R05 parts. The floor change affects the wall tab depth, curved corner lower geometry/pad height, magnet insert height and calibration samples. Mixing previous wall/curve/insert files with R06 floors is not the validated assembly.

## Material and supplier tolerance

The user-supplied listing title identifies 椴木板三合板, interpreted as **basswood plywood**, rather than the previously specified birch plywood. It does not specify structural grade, ply construction, bond quality or stiffness. The supplier states around 0.2 mm error. This package conservatively checks **5.8-6.2 mm walls and 9.8-10.2 mm floors**. Actual batch measurements have not been supplied. See Supplier_Specification_R06.json.

## What changed

- Wall stock stays nominal 6 mm; lower wall tabs and seating shoulders now match the nominal 10 mm floor.
- F01 is nominal 10 mm thick, with the same planar footprint and holes.
- C01 floor-pad undersides move from Z9 to Z10, pads now span Z10-18, and the lower locating geometry follows the new floor.
- M01 is 10 mm high; OD29.2, underside pocket diameter25.2 x 5 remain unchanged. Its roof is 5 mm at nominal dimensions.
- Exterior nominal bin dimensions remain 347.5 x 347.5 x 450, full layout 700 x 700 x 450, with R75 exposed curves around the confirmed diameter147.5 post (1.25 nominal radial gap).
- M3x12 and M4x20 countersunk screws remain specified. Geometric reach is checked at maximum stock; actual thread/head/nut fit must pass the first article.

## Assembly datums are important for stock variation

Hold B1 wall **inside** faces at X/Y8.5 and344 and seat the floor **top** at Z10 against the shoulders and three printed pads. Mirror these inside datums for other bins. Let outside faces and the floor underside follow actual stock thickness. Do not force every external face and underside to the nominal coordinates.

At the checked extremes, a bin can extend up to 0.4 mm beyond nominal width and 0.2 mm below the nominal underside. Four-bin neighbor clearance remains at least 4.6 mm. Check the actual base/magnet engagement after assembly. Seat M01 pockets flush with the actual floor underside; level/seal only the insert roof as needed, preserving the 5 mm-deep magnet pocket. Resolve rocking or gaps before bonding.

## Tests run

- **235 nominal geometry/export/sample checks**, all pass, in Verification.json.
- **51 additional thickness-tolerance checks**, all pass, in Tolerance_Verification_R06.json. Pairwise extremes cover all 32 independent extreme thickness combinations per bin; exact reflections cover all four bins. Tests include continuous insertion sweeps, bin-to-bin clearance and screw reach.
- **24 finished-part identity checks**, all pass, in Repeat_Part_Verification_R06.json. Selected repeated templates reproduce every intended structural part with proper rotation/translation, without scaling or reflection.
- **134 fresh single-bin master checks**, all pass, in Source/Master_Verification_R06.json. These were regenerated for the 10 mm design, not inherited from the 9 mm assembly.

These tests verify the defined CAD geometry and export files. They do not measure the actual laser kerf, printer distortion, wood bond quality or physical capacity. The 10 kg per-bin load remains a design target pending the guide's 15 kg/60-minute proof test and 10 kg handling trial. The illustrative floor screen assumes E=3000 MPa, not a verified property of this supplier's model-making plywood.

## Production and the low-waste test sequence

Manufacture physical coupons before full-size production. Q01-Q08 cover ordinary fits; **Q09_curve_floor_sample.stl** is the actual lower24 mm crop of C01, printed upright, and **Q10_floor_corner_sample.dwg** is a177.5 x177.5 crop of the10 mm floor. Assemble Q09/Q10 with threeM4x20 screws/nuts and oneM01 to check the changed floor/pads/countersinks/insert interface. Samples are extra to the production quantities.

After sample approval, make one complete B1 prototype and perform dry fit and load tests before making the remaining three. A failed sample requires process correction or regenerated mating geometry before full cutting. This staged approach avoids committing all twenty plates before physical validation.

## Files

- PDF/Manufacturing_and_Assembly_Guide_R06.pdf:20 illustrated pages, including all10 calibration sample IDs.
- PDF/Dimensioned_Parts_and_Layouts_R06.pdf:26 dimensioned pages.
- PDF/Full_Scale_Cutting_Profiles_R06.pdf:28 vector pages at1:1. Verify the100 mm bar; no page fitting.
- PDF/Repeat_Part_Order_R06.pdf:3-page consolidated order and first-article instructions.
- DWG/:33 genuineR2000 DWGs; DXF/:33 corresponding files. Cut only CUT, inmm at1:1. Apply measured kerf compensation once.
- STEP/ and STL/:all four B-specific variants, assemblies, common insert and10 calibration models. Print individual C01/M01 production files and Q05/Q09 samples; plywood STLs and assembly STLs are viewing models.

The separate compact manufacturer-order ZIP selects four production cutting patterns: W01x4, W02x4, W03-profile short blanksx8, F01x4. Finish four short blanks as B1_W03 and four as B1_W04 on opposite countersink faces. Print B1_C01x2, B2_C01x2 and M01x16. Use either this consolidated order or the per-instance Manufacturing_List.csv, not both.

Source/ preserves the updated generators, master solids/profiles and verification scripts. Rebuilding from parameters requires regenerating the master first, refreshing the embedded master data, rebuilding the mirrors and coupons, then generating Q09/Q10 and converting its DWG. Rerun all geometry/tolerance/repeat checks and visually review the PDFs before release. Nominal thicknesses, material assumptions and tolerance datums must stay consistent across files and instructions.
