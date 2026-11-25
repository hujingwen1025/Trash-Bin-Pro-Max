"""Recheck the final individual STEP/STL files after all CAD rendering exports."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
import trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
ROOT=Path(__file__).resolve().parents[1];meta=json.loads((ROOT/'Verification/parts.json').read_text());tests=[]
for name,m in meta.items():
 s=cq.importers.importStep(str(ROOT/m['folder']/'STEP'/f'{name}.step')).val();mesh=trimesh.load(ROOT/m['folder']/'STL'/f'{name}.stl',force='mesh');box=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,box,False,False);bounds=list(box.Get())
 ok=s.isValid()and len(s.Solids())==1 and mesh.is_watertight and mesh.is_winding_consistent and abs(mesh.volume-s.Volume())/s.Volume()<.01 and np.allclose(bounds,m['bounds'],atol=1e-4,rtol=0)and np.isclose(s.Volume(),m['volume_mm3'],atol=1e-3,rtol=1e-7)
 tests.append({'part':name,'pass':bool(ok),'step_volume_mm3':s.Volume(),'mesh_watertight':mesh.is_watertight})
result={'all_passed':all(t['pass']for t in tests),'tests':tests,'scope':'final individual exports only; assembly meshes are viewing compounds, not fused printable objects'};(ROOT/'Verification/Final_Export_Verification.json').write_text(json.dumps(result,indent=2));print('Final STEP/STL exports',len(tests),'PASS',result['all_passed'])
if not result['all_passed']:raise SystemExit('Final export check failed')
