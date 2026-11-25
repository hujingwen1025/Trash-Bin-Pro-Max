from pathlib import Path
import cadquery as cq,math,json,trimesh,ezdxf,numpy as np
ROOT=Path(__file__).resolve().parents[1]
curve=cq.importers.importStep(str(ROOT/'STEP/B1_C01.step')).val();floor=cq.importers.importStep(str(ROOT/'STEP/B1_F01.step')).val()
parts={'Q09_curve_floor_sample':curve.intersect(cq.Solid.makeBox(140,140,24,cq.Vector(0,0,0))).clean(),'Q10_floor_corner_sample':floor.intersect(cq.Solid.makeBox(180,180,10,cq.Vector(0,0,0))).clean()}
R=json.loads((ROOT/'Verification.json').read_text())
def test(name,ok,**data):
 R['tests'].append({'name':name,'pass':bool(ok),**data});print(('PASS 'if ok else'FAIL ')+name,flush=True);assert ok,name
for n,s in parts.items():
 for folder,ext in [('STEP','step'),('STL','stl')]:cq.exporters.export(s,str(ROOT/folder/f'{n}.{ext}'),tolerance=.035,angularTolerance=.06)
 m=trimesh.load(ROOT/'STL'/f'{n}.stl',force='mesh');re=cq.importers.importStep(str(ROOT/'STEP'/f'{n}.step')).val();test(n+' actual crop solid and export integrity',s.isValid()and len(s.Solids())==1 and re.isValid()and abs(re.Volume()-s.Volume())<.01 and m.is_watertight and m.is_winding_consistent and m.volume>0)
s=parts['Q10_floor_corner_sample'];face=max([f for f in s.Faces()if f.geomType()=='PLANE'and f.normalAt().z>.999],key=lambda f:f.Area())
d=ezdxf.new('R2000');d.units=4;d.header['$MEASUREMENT']=1;d.layers.new('CUT',dxfattribs={'color':1});d.layers.new('REFERENCE',dxfattribs={'color':5});m=d.modelspace()
for wire in [face.outerWire(),*face.innerWires()]:
 for e in wire.Edges():
  attr={'layer':'CUT'}
  def xy(p):return(p.x,p.y)
  if e.geomType()=='LINE':m.add_line(xy(e.startPoint()),xy(e.endPoint()),dxfattribs=attr)
  else:
   cc=e.arcCenter();r=e.radius()
   if abs(e.Length()-2*math.pi*r)<1e-4:m.add_circle(xy(cc),r,dxfattribs=attr)
   else:
    a,b,mid=[math.degrees(math.atan2(p.y-cc.y,p.x-cc.x))%360 for p in [e.startPoint(),e.endPoint(),e.positionAt(.5)]]
    if(mid-a)%360>(b-a)%360:a,b=b,a
    m.add_arc(xy(cc),r,a,b,dxfattribs=attr)
m.add_text('Q10 | 10 mm PLYWOOD | FIT SAMPLE | mm',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-12));d.saveas(ROOT/'DXF/Q10_floor_corner_sample.dxf')
test('Q09/Q10 floor pad assembly interference',parts['Q09_curve_floor_sample'].intersect(parts['Q10_floor_corner_sample']).Volume()<.02)
for deg in [22.5,45,67.5]:
 a=math.radians(deg);shaft=cq.Solid.makeCylinder(2,18,cq.Vector(100*math.cos(a),100*math.sin(a),0),cq.Vector(0,0,1));v=sum(shaft.intersect(p).Volume()for p in parts.values());test(f'Q09/Q10 M4 {deg} shaft alignment',v<.01,overlap_mm3=v)
cup=cq.importers.importStep(str(ROOT/'STEP/M01_magnet_insert.step')).val().translate((102.5,102.5,0));test('Q10 actual insert fit',cup.intersect(parts['Q10_floor_corner_sample']).Volume()<.01,radial_gap_mm=.2)
(ROOT/'Verification.json').write_text(json.dumps(R,indent=2))
