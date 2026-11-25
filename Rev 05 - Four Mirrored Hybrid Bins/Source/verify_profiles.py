from pathlib import Path
import json,math
import numpy as np,cadquery as cq,ezdxf
from shapely.geometry import Polygon,Point
ROOT=Path(__file__).resolve().parents[1];report=json.loads((ROOT/'Verification.json').read_text())
for path in sorted((ROOT/'DXF').glob('B*_*.dxf')):
 if 'REFERENCE'in path.stem:continue
 d=ezdxf.readfile(path);curves=[];loops=[]
 for e in d.modelspace():
  if e.dxf.layer!='CUT':continue
  if e.dxftype()=='LINE':curves.append([tuple(e.dxf.start)[:2],tuple(e.dxf.end)[:2]])
  elif e.dxftype()=='CIRCLE':loops.append(Point(tuple(e.dxf.center)[:2]).buffer(e.dxf.radius,quad_segs=512))
  elif e.dxftype()=='ARC':curves.append([tuple(p)[:2] for p in e.flattening(.001)])
 while curves:
  points=curves.pop(0)
  while np.linalg.norm(np.array(points[-1])-np.array(points[0]))>1e-5:
   options=[(np.linalg.norm(np.array(points[-1])-np.array(c[0])),i,False)for i,c in enumerate(curves)]+[(np.linalg.norm(np.array(points[-1])-np.array(c[-1])),i,True)for i,c in enumerate(curves)]
   error,i,rev=min(options);assert error<1e-5,(path,error);c=curves.pop(i);points.extend((c[::-1]if rev else c)[1:])
  loops.append(Polygon(points))
 loops.sort(key=lambda p:p.area,reverse=True);poly=loops[0]
 for hole in loops[1:]:poly=poly.difference(hole)
 s=cq.importers.importStep(str(ROOT/'STEP'/f'{path.stem}.step')).val();part=path.stem.split('_')[1];axis='z'if part=='F01'else('y'if part in ['W01','W03']else'x')
 faces=[f for f in s.Faces()if f.geomType()=='PLANE'and abs(getattr(f.normalAt(),axis))>.999]
 target=max(f.Area()for f in faces);error=abs(poly.area-target)
 ok=poly.is_valid and all(q.is_valid for q in loops)and error<.05
 print(path.stem,ok,'area error',error,flush=True);report['tests'].append({'name':path.stem+' closed cutter contours match solid panel face','pass':bool(ok),'area_error_mm2':error,'loops':len(loops)})
 assert ok,(path,error)
(ROOT/'Verification.json').write_text(json.dumps(report,indent=2))
