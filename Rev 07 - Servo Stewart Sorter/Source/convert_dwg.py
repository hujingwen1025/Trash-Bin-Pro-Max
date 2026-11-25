"""Generate reference projections and genuine R2000 DWGs; round-trip check."""
from pathlib import Path
import json,os,subprocess,shutil,math
import numpy as np
import cadquery as cq
import ezdxf
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'Verification/parts.json').read_text());flat_profiles=json.loads((ROOT/'Verification/profiles.json').read_text())
for name,m in meta.items():
 folder=ROOT/m['folder'];target=folder/'DXF'/f'{name}.dxf'
 if name in flat_profiles and target.exists():continue
 shape=cq.importers.importStep(str(folder/'STEP'/f'{name}.step')).val();bb=shape.BoundingBox()
 d=ezdxf.new('R2000');d.units=4;d.layers.new('REFERENCE',dxfattribs={'color':5});space=d.modelspace()
 for title,axes,off in [('TOP',(0,1),(0,0)),('FRONT',(0,2),(bb.xlen+35,0)),('RIGHT',(1,2),(2*(bb.xlen+35),0))]:
  arrays=[]
  for edge in shape.Edges():
   if edge.geomType()=='LINE':pts=np.array([edge.startPoint().toTuple(),edge.endPoint().toTuple()])
   else:
    n=min(256,max(12,math.ceil(edge.Length()/3)));pts=np.array([edge.positionAt(float(u)).toTuple()for u in np.linspace(0,1,n)])
   arrays.append(pts[:,axes])
  points=np.concatenate(arrays);minimum=points.min(0)
  for pts in arrays:
   q=pts-minimum+off
   if len(q)==2:space.add_line(q[0],q[1],dxfattribs={'layer':'REFERENCE'})
   else:space.add_lwpolyline(q,dxfattribs={'layer':'REFERENCE'})
  space.add_text(title,dxfattribs={'layer':'REFERENCE','height':3}).set_placement((off[0],-8))
 space.add_text(name+' | REFERENCE VIEWS ONLY - NOT A CUT PROFILE | mm | STEP governs',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-20));d.saveas(target)

oda=os.environ.get('ODA_CONVERTER')or shutil.which('ODAFileConverter')or'/Volumes/ODA ODAFileConverter sample/ODAFileConverter.app/Contents/MacOS/ODAFileConverter'
if not Path(oda).is_file():raise RuntimeError('Install ODA File Converter and set ODA_CONVERTER to its executable.')
reader=os.environ.get('DWG_READER')or shutil.which('dwgread')or'/opt/homebrew/bin/dwgread'
checks=[]
def equivalent(a,b):
 # Exact structure/layers with a small numerical tolerance for floating-point
 # storage. Decimal rounding at a half-way value can differ by1e-5 despite a
 # true coordinate difference below1e-14; compare the numbers directly.
 if a.dxftype()!=b.dxftype()or a.dxf.layer!=b.dxf.layer:return False
 t=a.dxftype()
 def close(x,y):return np.shape(x)==np.shape(y)and np.allclose(x,y,atol=1e-6,rtol=0)
 def pt(x):return tuple(x)[:2]
 if t=='LINE':
  x=[pt(a.dxf.start),pt(a.dxf.end)];y=[pt(b.dxf.start),pt(b.dxf.end)];return close(x,y)or close(x,y[::-1])
 if t=='CIRCLE':return close([*pt(a.dxf.center),a.dxf.radius],[*pt(b.dxf.center),b.dxf.radius])
 if t=='LWPOLYLINE':return a.closed==b.closed and close(a.get_points('xyb'),b.get_points('xyb'))
 if t=='TEXT':return a.dxf.text==b.dxf.text and close(pt(a.dxf.insert),pt(b.dxf.insert))
 return False
for folder in ('01_Metal','02_Print'):
 src=ROOT/folder/'DXF';dst=ROOT/folder/'DWG';back=ROOT/'Verification'/'DWG_Roundtrip'/folder;dst.mkdir(exist_ok=True);back.mkdir(parents=True,exist_ok=True)
 for cmd in [[oda,str(src),str(dst),'ACAD2000','DWG','0','1','*.dxf'],[oda,str(dst),str(back),'ACAD2000','DXF','0','1','*.dwg']]:
  p=subprocess.run(cmd,capture_output=True,text=True)
  if p.returncode:raise RuntimeError('ODA conversion failed: '+p.stderr[-2000:])
 for path in sorted(src.glob('*.dxf')):
  target=dst/(path.stem+'.dwg');roundtrip=back/path.name
  a=ezdxf.readfile(path);b=ezdxf.readfile(roundtrip)
  source_entities=list(a.modelspace());roundtrip_entities=list(b.modelspace());same=len(source_entities)==len(roundtrip_entities)and all(equivalent(x,y)for x,y in zip(source_entities,roundtrip_entities))
  p=subprocess.run([reader,'-v0','-O','JSON',str(target)],capture_output=True,text=True)
  ok=same and b.units==4 and target.read_bytes()[:6]==b'AC1015'and p.returncode==0 and'ERROR'not in p.stderr
  checks.append({'file':str(target.relative_to(ROOT)),'pass':ok,'entities':len(a.modelspace()),'roundtrip_equal':same,'coordinate_tolerance_mm':1e-6,'layers_and_closed_flags_verified':True,'units':b.units,'independent_reader_returncode':p.returncode})
  print(('PASS 'if ok else'FAIL ')+str(target.relative_to(ROOT)),flush=True)
(ROOT/'Verification/DWG_Verification.json').write_text(json.dumps({'writer':'ODA File Converter','independent_reader':'LibreDWG','format':'R2000 AC1015','tests':checks,'all_passed':all(x['pass']for x in checks)},indent=2))
if not all(x['pass']for x in checks):raise SystemExit('DWG verification failed; do not release')
