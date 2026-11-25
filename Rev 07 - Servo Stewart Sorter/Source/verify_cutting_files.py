"""Validate final DXF process layers, closed profiles and rough precision bores."""
from pathlib import Path
import json
import numpy as np
import ezdxf
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'Verification/parts.json').read_text());profiles=json.loads((ROOT/'Verification/profiles.json').read_text());checks=[]
for name,m in meta.items():
 path=ROOT/m['folder']/'DXF'/f'{name}.dxf';doc=ezdxf.readfile(path);entities=list(doc.modelspace());cut=[e for e in entities if e.dxf.layer=='CUT'];ok=doc.units==4
 if name not in profiles or m['quantity']==0:ok=ok and not cut
 else:
  info=profiles[name];holes=info.get('cut_holes',info['holes']);polys=[e for e in cut if e.dxftype()=='LWPOLYLINE'];circles=[e for e in cut if e.dxftype()=='CIRCLE'];outlines=[info['outline']]+info.get('slots',[])
  ok=ok and len(cut)==len(outlines)+len(holes)and len(polys)==len(outlines)and len(circles)==len(holes)
  for entity,coords in zip(polys,outlines):
   actual=np.array(entity.get_points('xy'));expected=np.array(coords);ok=ok and entity.closed and actual.shape==expected.shape and np.allclose(actual,expected,atol=1e-6,rtol=0)
  for entity,(x,y,r)in zip(circles,holes):ok=ok and np.allclose([entity.dxf.center.x,entity.dxf.center.y,entity.dxf.radius],[x,y,r],atol=1e-6,rtol=0)
 checks.append({'file':str(path.relative_to(ROOT)),'pass':bool(ok),'units':doc.units,'CUT_entities':len(cut),'quantity':m['quantity'],'role':'production rough cut'if cut and m['quantity']else'reference only'})
base=ezdxf.readfile(ROOT/'01_Metal/DXF/BASE_Drill_Template.dxf');n=sum(e.dxf.layer=='DRILL'and e.dxftype()=='CIRCLE'for e in base.modelspace());checks.append({'file':'01_Metal/DXF/BASE_Drill_Template.dxf','pass':base.units==4 and n==22,'DRILL_holes':n})
result={'all_passed':all(q['pass']for q in checks),'tests':checks,'precision_bores':'21.5 rough to22H7;7.5 rough to8H7; STEP finished sizes','kerf':'apply once at actual machine'}
(ROOT/'Verification/Cutting_Files_Verification.json').write_text(json.dumps(result,indent=2))
print('Cut/reference files',len(checks),'PASS',result['all_passed'])
if not result['all_passed']:raise SystemExit('Cutting-file checks failed')
