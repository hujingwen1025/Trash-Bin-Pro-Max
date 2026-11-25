# Trash Bin Pro Max — R05 four mirrored hybrid bins

This revision replaces the “four identical copies” quantity assumption with **four separately labeled mirrored kits**. It preserves the supplied bin dimensions, R04 finger-joint design and 10 kg per-bin design target. The screenshots establish a four-quadrant arrangement around the central opening; this package defines the quadrant labels below because the screenshot does not expose the mirror feature planes or identify every visible quadrant by number.

| Kit | Global X | Global Y | Transformation of B1 |
| --- | --- | --- | --- |
| B1 | +2.5 to +350 | +2.5 to +350 | Original/reference |
| B2 | -350 to -2.5 | +2.5 to +350 | Reflect across X=0 |
| B3 | +2.5 to +350 | -350 to -2.5 | Reflect across Y=0 |
| B4 | -350 to -2.5 | -350 to -2.5 | Reflect across both planes |

Top view: **B2 | B1** above the center; **B4 | B3** below it. +Y is up and +X is right. Each bin stays upright, with Z=0 underside and Z=450 rim. The complete bin layout is **700 × 700 × 450 mm**, each bin is **347.5 × 347.5 × 450 mm**, and the neighboring-bin separation is at least **5 mm**. The filenames and diagrams define these identities even if a different naming order was used in the Onshape document. No live Onshape model was modified.

## Read the PDFs before manufacturing

- **PDF/Manufacturing_and_Assembly_Guide_R05.pdf** — 20 illustrated pages: exact file/process map, coupons, materials, hardware, countersink-face map, mirrored assembly directions, dry fit, permanent assembly, finishing and physical test records.
- **PDF/Dimensioned_Parts_and_Layouts_R05.pdf** — 26 pages: quadrant placement, every B-specific production plate and printed curve, and the common magnet insert. Dimensions and global hole locations accompany the actual geometry.
- **PDF/Full_Scale_Cutting_Profiles_R05.pdf** — 27 vector pages: twenty production plywood profiles and seven plywood coupons at 1:1. Print/import at actual size, disable page fitting and measure the 100 mm scale bar. The oversize pages intentionally retain the actual part dimensions.

All drawings use millimetres. These are nominal stock files that require calibration with the actual plywood, laser and PETG process before a full production run. Keep the approved samples with the job.

## What to manufacture

**Laser cut:** each B1/B2/B3/B4 `W01`, `W02`, `W03`, `W04` DWG once in **6 mm birch plywood**; each `F01` DWG once in **9 mm birch plywood**. Total: **16 walls and 4 floors**. Each bin needs its matching five pieces. W01/W02 are long-wall roles and W03/W04 are short-wall roles; their global compass sides change under mirroring.

**3D print:** `STL/B1_C01.stl`, `B2_C01.stl`, `B3_C01.stl`, and `B4_C01.stl`, **one each in PETG**. Print **16** `STL/M01_magnet_insert.stl`, four per bin. The M01 insert is common. Separate files are supplied for all mirrored kits even where a flat profile has the same outline by symmetry.

Each curve is one piece, **130 × 130 × 450 mm**, with its height along printer Z. Keep this upright orientation, matching the Q05 test print. Select a printer with sufficient usable height plus process allowance. The Bambu H2D specification lists 325 mm build height, so it does not accommodate the specified upright 450 mm print. Source: [official H2D specification](https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf), checked 19 November 2026. The design remains unsplit as requested.

`Manufacturing_List.csv` lists every distinct production file and its finished-set quantity. Calibration samples and spares are additional. Hardware for the four bins: **24 M3×12 90-degree countersunk screws + 24 M3 nuts; 12 M4×20 90-degree countersunk screws + 12 M4 nuts; 16 suitably sized magnets**. Adhesives, clamps, finish and tools are listed in the guide.

## File conventions and secondary operations

- **DWG/** contains genuine R2000 DWGs, independently read and round-tripped. Cut only the **CUT** layer. **REFERENCE** holds identifiers and reference drawings. The profiles contain **no kerf offset**; apply measured compensation once in the cutting workflow.
- **DXF/** supplies matching R2000 DXFs for cutters that prefer them. Use **either DWG or DXF**, keeping identical scale and layer choices.
- **STL/** uses mm dimensions. Print the individual C01 and M01 manufacturing files. The plywood STLs are inspection models. `B#_Assembly.stl` and `Four_Bin_Layout_R05.stl` are watertight viewing meshes; touching structure is fused in these viewing models.
- **STEP/** contains individual solid components and assemblies in the global coordinates above. Each bin assembly has ten component solids (six structural parts plus four inserts); the complete layout has forty solids. Source/MasterGeometry holds the embedded reference solids used for reflection.
- `B#_C01_REFERENCE.dwg` and `M01_magnet_insert_REFERENCE.dwg` describe **printed** parts and contain REFERENCE geometry, not laser-cut production outlines.

Laser profiles contain diameter **3.4** M3 through holes in W03/W04 and diameter **4.5** M4 through holes in F01. After cutting, countersink W03/W04 from their exterior faces to **diameter 6.3 × 90°** (nominal depth **1.45**); countersink the three small floor holes from the underside **Z=0** to **diameter 8 × 90°** (depth **1.75**). The STEP/STL solids include the finished countersinks. Verify seats against actual screw heads on samples.

| Bin | W03 countersunk face | W04 countersunk face | Floor countersunk face |
| --- | --- | --- | --- |
| B1 | Y=+2.5 | X=+2.5 | Z=0 |
| B2 | Y=+2.5 | X=-2.5 | Z=0 |
| B3 | Y=-2.5 | X=+2.5 | Z=0 |
| B4 | Y=-2.5 | X=-2.5 | Z=0 |

## Calibration and clearances

Q01/Q02/Q03/Q04/Q06/Q07/Q08 are common **laser-cut** samples; Q05 is a common **PETG print**. Use the common samples to calibrate clearances, then apply those values consistently to the mirrored geometry. They are fit samples, not substitutes for a labeled production part.

- **Q01_wall_fit / 6 mm:** lower rows pair with **Q03_wall_tab / 6 mm**; upper rows pair with **Q04_floor_tab / 9 mm**. Choices: 0.10–0.40 mm total clearance in 0.05 steps.
- **Q02_floor_fit / 9 mm:** pair with **Q08_floor_wall_tab / 6 mm**. Also trial its diameter 4.5 hole and countersink with the purchased M4 screw.
- Q01 and Q02 each contain a 20×20 kerf plug. Estimate full kerf as **(measured opening − measured plug)/2**, separately in X and Y for each stock thickness.
- **Q05_curve_joint_sample / PETG:** print upright like C01, pair with **Q06_curve_wall_sample / 6 mm**, check fingers, an M3 nut and the secondary countersink.
- **Q07_insert_fit / 9 mm:** try an actual M01 in its three holes, 0.10/0.20/0.30 **radial** clearance left to right.

Nominal vertical finger clearances are **0.20 total wood/wood** and **0.30 total wood/print**. The M01 insert OD is 29.2; the floor hole is 29.6, giving 0.20 radial epoxy space. Insert height is 9, with an underside **diameter 25.2 × 5 deep** magnet pocket and 4 mm closed roof. Never enlarge joints or nut traps merely to force assembly. Measure stock and adjust the master design and all affected mirrors when necessary.

## Existing base and central post

**The existing base plate, post and mounting/magnet counterpart geometry were not supplied as CAD and are not included as manufacturing parts.** The four bins and their internal mating geometry have been checked. Match the actual base and post before ordering final parts.

The user confirmed the actual central post diameter is **147.5 mm**. The exposed curve remains **R75 about the global origin**, leaving **1.25 mm nominal radial clearance** around that post. The CAD was preserved as requested. All four assemblies were checked against a centered 147.5 mm cylindrical post over the full 450 mm bin height, with no interference; measured minimum solid distance is recorded per bin in Verification.json. A diameter 149.8 reference gauge also clears. Trial the actual base alignment, post concentricity and magnet engagement before final bonding; the complete base/platform CAD has not been supplied.

## Validation and physical testing

`Verification.json` records **225 new R05 checks, all passing**. These cover reflected source identity, valid single-part solids, STEP round trips, positive watertight STL meshes, four-bin envelope and bin separation, final structural interference, continuous 12 mm insertion sweeps in each mirrored assembly, screw-axis mandrels, all sixteen insert fits, the confirmed 147.5 mm post and a central reference gauge, DWG geometry/unit preservation and independent reading, duplicate cutter-entity checks, and closed cutting contours matching the corresponding solid panel faces. The original **134 R04 checks** are retained separately in `Source/Inherited_R04_Verification.json`; they are inherited evidence, not counted as newly rerun tests.

The guide preserves the **10 kg per-bin design target**, **15 kg/60-minute supported physical proof test**, and **10 kg/ten-cycle handling trial**. These physical tests have **not** been performed. The preliminary floor calculation assumes 9 mm plywood, E=3,000 MPa and 335.5 mm span/width; predicted deflections are 0.79 mm at 10 kg and 1.18 mm at 15 kg. It excludes local holes, wood damage, joint behavior, printed layer defects, moisture and long-term creep. Use the manufactured-part tests and actual material data to establish suitability.

All **73 PDF pages** were rendered for review. The guide's exact manufacturing filenames and set quantities were checked against the delivered package. `Source/guide_verification.json`, `Source/drawing_pages.json`, and `Package_Verification.json` record the document and inventory checks. `SHA256.json` covers delivered files; the ZIP was checked against this manifest.

## Source and regeneration

`Source/build_mirrors.py` rebuilds the reflected production solids, meshes and profiles from **Source/MasterGeometry** and **Source/MasterProfiles**, then performs geometric checks. `Source/verify_profiles.py` compares closed cutter contours with the solid panel faces. To write DWG, set `ODA_CONVERTER` to the installed ODA File Converter executable and have LibreDWG `dwgread` available. The export command is `python Source/build_mirrors.py --convert`, followed by `python Source/verify_profiles.py`. Temporary data defaults to `.build` or the `BIN_R05_BUILD` environment path.

`Source/Parametric_Master/Source/` preserves the original R04 parameter-based generators and reference STL. If measured stock requires changes, regenerate that master in its own work directory first, then refresh the embedded master solids, manufacturing profiles, M01 and common coupons before rebuilding all four mirrors. Update dimensional notes, guide text, manufacturing quantities and validation when parameters change. The supplied guide describes the **delivered nominal 6/9 mm design**.

`render_reference_views.py`, `render_layout.py`, `make_drawings.py` and `make_guide.py` reproduce the illustrations/PDFs from their embedded inputs. Render the reference views before the layout views, so the final illustration index includes both. Regenerated PDFs require a new visual review before release.
