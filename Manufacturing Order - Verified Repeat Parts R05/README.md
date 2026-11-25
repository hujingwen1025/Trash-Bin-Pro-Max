# R05 verified repeat-part order - one four-bin set

Use **Repeat_Part_Order_R05.pdf** and the two Order CSVs as the production quantity authority for this consolidated order. The R05 CAD dimensions and intended assemblies are unchanged. The B-prefix on an assembly part is its final placement label, not necessarily a different physical geometry.

## Files to send

- **01_Laser_Cut/DWG/**: four selected blank profiles. Order quantities 4 W01, 4 W02, 8 W03-profile short blanks and 4 F01. The matching **Alternative_DXF/** files are an alternative representation of the same contours, not extra parts.
- **02_Finished_STEP/**: eight representative finished solids with countersinks, holes and nut pockets. Finished quantities are in Finished_Part_Order.csv. For the eight short-wall blanks, make four finished W03-template parts and four finished W04-template parts, with countersinks on opposite faces.
- **03_3D_Print_STL/**: two B1_C01, two B2_C01 and sixteen M01. The two curve templates preserve the complete CAD, including nut-pocket orientation; do not replace them with four B1_C01 prints under this exact-CAD order.
- **04_Calibration/**: seven plywood coupon DWGs and one printed Q05 sample. These are additional setup samples. Print a first M01 for the Q07 trial; if accepted, it may count toward the sixteen production inserts. Repeat coupons when stock or process changes. The common samples and pairs are explained in the reference guide.
- **05_Assembly_Reference/**: the original R05 20-page guide and dimensioned drawings. Their B-specific IDs remain assembly labels. Their per-instance file tables describe the original full package; the quantities in this repeat-part order replace that ordering route. Do not order both routes.
- **Assembly_Label_Map.csv**: every final structural instance mapped to its identical production template. Numeric rotations/translations are assembly placement in global CAD coordinates, not instructions to change the manufacturing geometry.
- **06_Verification/Repeat_Part_Verification.json**: complete finished-solid equivalence checks and original input hashes. Every intended structural component matched a selected template by a proper upright rotation and translation, with zero measured symmetric-difference volume. No reflections, scaling or edits were needed after producing the finished templates.

Use **Message_to_Manufacturer.txt** as the order request. The quantities are for one complete set of four bins. This folder is a compact selection from the existing R05 files; it does not change geometry or the 10 kg per-bin design target. Physical fit and load tests remain to be performed.

The original 225 R05 geometric/export checks apply to the intended assemblies. The new repeat-part audit confirms that ordering the listed copies reproduces those same intended solids. Calibrate actual plywood thickness, laser kerf, printed joint fit and nut fit before ordering a full production run. The curves remain upright, full-height 450 mm prints. The actual post diameter is 147.5 mm with 1.25 mm nominal radial clearance.
