# Reproduction and evidence

Use Python3.11 and requirements-build.txt in a dedicated environment. Preserve any completed physical test records before rebuilding.

1. Run build_cad.py for individual STEP/STL, rough cutting profiles, named assemblies, machining axes and the build fingerprint. Drawing envelopes use exact analytic bounds, excluding cached mesh inflation.
2. Run verify_geometry.py --sweep 61. This checks exports, kinematics/statics, reproducible dimensional perturbations, material around carrier taps and exact sampled BRep interference. Fixed/rigid-invariant pairs and conservative bounding boxes accelerate the checks; this is not continuous collision detection.
3. Run render_previews.py and wiring_diagram.py. Set MPLCONFIGDIR/XDG_CACHE_HOME to writable directories if needed.
4. Run make_records.py for software tests, simulation, provenance, coordinate/finishing CSVs and final reference-only layers on zero-quantity blanks. CAD imports can regenerate rough profiles; always finalize records/layers after the CAD rendering/verification steps. Existing physical acceptance records are preserved.
5. Run convert_dwg.py. Install ODA File Converter separately; set ODA_CONVERTER and DWG_READER (LibreDWG dwgread) if needed. macOS may require desktop access. No converter binary is bundled. DWGs are R2000, independently read, then round-tripped; units, geometry within1e-6mm, layers and closed flags are checked.
6. Run verify_cutting_files.py and verify_final_exports.py against the final files.
7. Run make_documents.py for the three PDFs and final order/purchase tables. On other systems, set R07_CJK_FONT to a TrueType font containing Chinese; the macOS default is STHeiti. PDF subsets are embedded.
8. Render and visually inspect every PDF page before packaging. Run package_release.py after the QA report is current.

Complete-system reconstruction reads the sibling R06 STEP directory; R06 is not edited. Individual files use local manufacturing coordinates. The final source uses shared configuration dimensions, socket orientation and supplied machining-axis CSVs.

No physical material certification, servo continuous rating, actual belt approval, load/thermal/routing/power-loss result or accepted quote is implied. Geometry/config hashes identify the calculation build; later annotation/measurement-only corrections are separately recorded. All CAD geometry remained unchanged by those corrections. Purchased CAD is schematic envelope data; finishing instructions and actual supplier samples govern.
