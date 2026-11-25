from pathlib import Path
import os,json,math,shutil,itertools,subprocess,sys,hashlib
import numpy as np
import cadquery as cq
import trimesh,ezdxf
from ezdxf.math import Matrix44
from shapely import wkt
from shapely.geometry import Polygon
from shapely.affinity import translate
from shapely.ops import unary_union

ROOT=Path(os.environ.get('BIN_R05_ROOT',str(Path(__file__).resolve().parents[1])))
INTERNAL=Path(os.environ.get('BIN_R05_BUILD',str(ROOT/'.build')));INTERNAL.mkdir(exist_ok=True)
MASTER=ROOT/'Source/MasterGeometry';PROFILES=ROOT/'Source/MasterProfiles'
NAMES=['W01_rear','W02_right','W03_front','W04_left','F01_floor','C01_curved_corner']
IDS={n:n.split('_')[0] for n in NAMES}
VARIANTS={'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}
REPORT={'revision':'R05','physical_tests_performed':False,'variant_convention':'B1 +X/+Y; B2 -X/+Y; B3 +X/-Y; B4 -X/-Y. Labels assigned by this package, not read from hidden screenshot geometry.','tests':[],'inherited_R04_checks':134}
META={}
def test(name,ok,**data):
 REPORT['tests'].append({'name':name,'pass':bool(ok),**data});print(('PASS 'if ok else'FAIL ')+name,flush=True)
def mirror(s,sx,sy):
 if sx<0:s=s.mirror('YZ')
 if sy<0:s=s.mirror('XZ')
 return s

BASE={n:cq.importers.importStep(str(MASTER/f'{n}.step')).val() for n in NAMES}
BASE_ASSEMBLY=cq.importers.importStep(str(MASTER/'Assembly_R04.step')).val()

# A drawing profile uses U=X for W01/W03, U=Y for W02/W04 and XY for the floor.
def profile_scales(n,sx,sy):
 return (sx,sy) if n=='F01_floor'else((sx,1)if n in ['W01_rear','W03_front']else(sy,1))
def normalize_planar(d):
 m=d.modelspace()
 for e in list(m):
  if e.dxftype() not in ['ARC','CIRCLE'] or e.dxf.extrusion.z>=0:continue
  center=e.ocs().to_wcs(e.dxf.center);attrs={'layer':e.dxf.layer}
  if e.dxftype()=='CIRCLE':m.add_circle(center,e.dxf.radius,dxfattribs=attrs)
  else:
   a,b=e.end_point,e.start_point
   angle=lambda p:math.degrees(math.atan2(p.y-center.y,p.x-center.x))%360
   m.add_arc(center,e.dxf.radius,angle(a),angle(b),dxfattribs=attrs)
  m.delete_entity(e)
def flat_dxf(n,bid,sx,sy):
 d=ezdxf.readfile(PROFILES/f'{n}.dxf');m=d.modelspace()
 for e in list(m):
  if e.dxf.layer!='CUT':m.delete_entity(e)
 for e in m:e.transform(Matrix44.scale(*profile_scales(n,sx,sy),1))
 d.units=4;d.header['$MEASUREMENT']=1
 if 'REFERENCE' not in d.layers:d.layers.new('REFERENCE',dxfattribs={'color':5})
 m.add_text(f'{bid}_{IDS[n]} | mm | NOMINAL STOCK | NO KERF OFFSET',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-16))
 normalize_planar(d);d.saveas(ROOT/'DXF'/f'{bid}_{IDS[n]}.dxf')

def write_reference(bid,sx,sy):
 d=ezdxf.new('R2000');d.units=4;d.layers.new('REFERENCE',dxfattribs={'color':5});m=d.modelspace()
 sections=json.loads((PROFILES/'curve_sections.json').read_text());side=json.loads((PROFILES/'curve_side.json').read_text())
 for idx,(label,wires,ax,ay)in enumerate([('XY section Z225',sections['225.0'],sx,sy),('XY section Z13',sections['13.0'],sx,sy),('XZ elevation',side,sx,1)]):
  temp=ezdxf.new('R2000');tm=temp.modelspace()
  for wire in wires:
   for e in wire:
    if e['type']=='LINE':tm.add_line(e['start'],e['end'])
    elif e['type']=='CIRCLE':tm.add_circle(e['center'],e['radius'])
    else:tm.add_arc(e['center'],e['radius'],e['start_angle'],e['end_angle'])
  for e in tm:e.transform(Matrix44.scale(ax,ay,1))
  from ezdxf import bbox
  bb=bbox.extents(tm);off=(idx*185-bb.extmin.x,-bb.extmin.y)
  for e in tm:
   ent=e.copy();ent.transform(Matrix44.translate(*off,0));ent.dxf.layer='REFERENCE';m.add_entity(ent)
  m.add_text(label,dxfattribs={'layer':'REFERENCE','height':3}).set_placement((idx*185,-10))
 m.add_text(f'{bid}_C01 | PRINTED PETG | mm | REFERENCE ONLY',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-22))
 normalize_planar(d);d.saveas(ROOT/'DXF'/f'{bid}_C01_REFERENCE.dxf')

SHAPES={};ASSEMBLIES={};all_mesh=[]
if '--dwg-only' not in sys.argv and '--profiles-only' not in sys.argv:
 for bid,(sx,sy)in VARIANTS.items():
  SHAPES[bid]={}
  for n in NAMES:
   key=f'{bid}_{IDS[n]}';s=mirror(BASE[n],sx,sy);SHAPES[bid][n]=s
   out=ROOT/'STEP'/f'{key}.step';cq.exporters.export(s,str(out));cq.exporters.export(s,str(ROOT/'STL'/f'{key}.stl'),tolerance=.035,angularTolerance=.06)
   re=cq.importers.importStep(str(out)).val();mesh=trimesh.load(ROOT/'STL'/f'{key}.stl',force='mesh')
   bb=s.BoundingBox();vol=s.Volume();back=mirror(re,sx,sy)
   test(key+' solid, STEP and mesh',s.isValid()and len(s.Solids())==1 and re.isValid()and abs(re.Volume()-vol)<.01 and mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0 and abs(mesh.volume-vol)/vol<.002,volume_mm3=vol)
   test(key+' reflected source identity',abs(back.Volume()-BASE[n].Volume())<.01 and back.cut(BASE[n]).Volume()<.01 and BASE[n].cut(back).Volume()<.01)
   META[key]={'bin':bid,'master_part':n,'signs':[sx,sy],'bounds':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],'volume_mm3':vol,'quantity':1}
   if n!='C01_curved_corner':flat_dxf(n,bid,sx,sy)
  write_reference(bid,sx,sy)
  ass=mirror(BASE_ASSEMBLY,sx,sy);ASSEMBLIES[bid]=ass;cq.exporters.export(ass,str(ROOT/'STEP'/f'{bid}_Assembly.step'))
  mesh=trimesh.load(MASTER/'Assembly_R04.stl',force='mesh');transform=np.diag([sx,sy,1,1]);mesh.apply_transform(transform);mesh.export(ROOT/'STL'/f'{bid}_Assembly.stl');all_mesh.append(mesh)
  test(bid+' assembly ten STEP solids and watertight mesh',len(ass.Solids())==10 and mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0)
  # Exact final interference, including every wall, floor and curved part.
  overlaps=[SHAPES[bid][a].intersect(SHAPES[bid][b]).Volume()for a,b in itertools.combinations(NAMES,2)]
  test(bid+' structural final-fit interference',max(overlaps)<.02,maximum_mm3=max(overlaps))
  # Complete continuous 12 mm insertion sweeps, reflected with the production solids.
  wp={n:wkt.loads(v)for n,v in json.loads((PROFILES/'wall_polygons.json').read_text()).items()}
  def extrude(poly,plane,depth):
   work=cq.Workplane(plane).polyline(list(poly.exterior.coords)[:-1]).close()
   for ring in poly.interiors:work=work.polyline(list(ring.coords)[:-1]).close()
   return work.extrude(depth).val()
  def sweep2(poly):
   pieces=[poly,translate(poly,xoff=12)]
   for ring in [poly.exterior,*poly.interiors]:
    pp=list(ring.coords)
    for a,b in zip(pp,pp[1:]):
     q=Polygon([a,b,(b[0]+12,b[1]),(a[0]+12,a[1])])
     if q.area>1e-10:pieces.append(q)
   return unary_union(pieces).buffer(0)
  fixed=['C01_curved_corner']
  for n in ['W03_front','W04_left','W01_rear','W02_right']:
   if n=='W03_front':sw=extrude(sweep2(wp[n]),cq.Plane(origin=(0,8.5,0),xDir=(1,0,0),normal=(0,-1,0)),6)
   elif n=='W04_left':sw=extrude(sweep2(wp[n]),cq.Plane(origin=(2.5,0,0),xDir=(0,1,0),normal=(1,0,0)),6)
   elif n=='W01_rear':sw=extrude(wp[n],cq.Plane(origin=(0,362,0),xDir=(1,0,0),normal=(0,-1,0)),18)
   else:sw=extrude(wp[n],cq.Plane(origin=(344,0,0),xDir=(0,1,0),normal=(1,0,0)),18)
   sw=mirror(sw,sx,sy);over=max(sw.intersect(SHAPES[bid][a]).Volume()for a in fixed)
   test(bid+' '+IDS[n]+' continuous insertion sweep',over<.02,travel_mm=12,maximum_mm3=over);fixed.append(n)
  floor=BASE['F01_floor'];face=max([f for f in floor.Faces()if f.geomType()=='PLANE'and f.normalAt().z<-.999],key=lambda f:f.Area());sw=floor.fuse(cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(0,0,-12)));sw=mirror(sw,sx,sy)
  over=max(sw.intersect(SHAPES[bid][a]).Volume()for a in fixed);test(bid+' floor continuous insertion sweep',over<.02,travel_mm=12,maximum_mm3=over)
  # Shafts through both mating parts, with their axes mirrored into this bin.
  for z in [81,225,369]:
   for wall,base,direction in [('W03_front',(120.5*sx,2.5*sy,z),(0,sy,0)),('W04_left',(2.5*sx,120.5*sy,z),(sx,0,0))]:
    shaft=cq.Solid.makeCylinder(1.5,11,cq.Vector(*base),cq.Vector(*direction));over=sum(shaft.intersect(SHAPES[bid][n]).Volume()for n in [wall,'C01_curved_corner']);test(bid+' '+IDS[wall]+f' M3 Z{z} alignment',over<.01,overlap_mm3=over)
  for deg in [22.5,45,67.5]:
   a=math.radians(deg);shaft=cq.Solid.makeCylinder(2,17,cq.Vector(sx*100*math.cos(a),sy*100*math.sin(a),0),cq.Vector(0,0,1));over=sum(shaft.intersect(SHAPES[bid][n]).Volume()for n in ['F01_floor','C01_curved_corner']);test(bid+f' floor M4 {deg} alignment',over<.01,overlap_mm3=over)
  for x,y in itertools.product([102.5,250],repeat=2):
   cup=cq.importers.importStep(str(ROOT/'STEP/M01_magnet_insert.step')).val().translate((sx*x,sy*y,0));over=cup.intersect(SHAPES[bid]['F01_floor']).Volume();test(bid+f' insert at {sx*x},{sy*y} fit',over<.01,radial_gap_mm=.2)
 full=cq.Compound.makeCompound(list(ASSEMBLIES.values()));cq.exporters.export(full,str(ROOT/'STEP/Four_Bin_Layout_R05.step'));tm=trimesh.util.concatenate(all_mesh);tm.export(ROOT/'STL/Four_Bin_Layout_R05.stl')
 bb=full.BoundingBox();test('Four-bin layout 700 x 700 x 450 and forty solids',np.allclose([bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],[-350,-350,0,350,350,450],atol=.001)and len(full.Solids())==40)
 test('Full layout STEP reimport and mesh integrity',len(cq.importers.importStep(str(ROOT/'STEP/Four_Bin_Layout_R05.step')).val().Solids())==40 and tm.is_watertight and tm.is_winding_consistent and tm.volume>0)
 for a,b in itertools.combinations(VARIANTS,2):
  # Independent bin envelopes are disjoint: structural CAD and insert bodies all stay inside these extents.
  distance=ASSEMBLIES[a].distance(ASSEMBLIES[b]);test(a+' / '+b+' separate-bin clearance',distance>=4.999,minimum_distance_mm=distance)
 # All radial surfaces and floor locators remain clear of an R74.9 reference gauge. Actual platform not supplied.
 gauge=cq.Solid.makeCylinder(74.9,450,cq.Vector(0,0,0));over=sum(gauge.intersect(s).Volume()for parts in SHAPES.values()for s in parts.values());test('Central R74.9 reference gauge clearance',over<.02,overlap_mm3=over,note='Reference gauge only. Existing platform dimensions and mounting were not supplied.')
 post=cq.Solid.makeCylinder(73.75,450,cq.Vector(0,0,0))
 for bid,ass in ASSEMBLIES.items():
  over=ass.intersect(post).Volume();gap=ass.distance(post)
  test(bid+' confirmed diameter 147.5 central post clearance',over<.02 and gap>=1.20,post_diameter_mm=147.5,nominal_radial_gap_mm=1.25,minimum_solid_distance_mm=gap,overlap_mm3=over)
 REPORT['confirmed_post_diameter_mm']=147.5;REPORT['nominal_post_radial_gap_mm']=1.25
 (ROOT/'Source/model_metadata.json').write_text(json.dumps(META,indent=2));(ROOT/'Source/variants.json').write_text(json.dumps(VARIANTS,indent=2));(ROOT/'Verification.json').write_text(json.dumps(REPORT,indent=2))
else:REPORT=json.loads((ROOT/'Verification.json').read_text())

if '--profiles-only' in sys.argv:
 for bid,(sx,sy)in VARIANTS.items():
  for n in NAMES:
   if n!='C01_curved_corner':flat_dxf(n,bid,sx,sy)
  write_reference(bid,sx,sy)

if '--convert' in sys.argv or '--dwg-only'in sys.argv:
 oda=os.environ['ODA_CONVERTER'];back=INTERNAL/'roundtrip';back.mkdir(exist_ok=True)
 for cmd in [[oda,str(ROOT/'DXF'),str(ROOT/'DWG'),'ACAD2000','DWG','0','1','*.dxf'],[oda,str(ROOT/'DWG'),str(back),'ACAD2000','DXF','0','1','*.dwg']]:
  r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
 def canonical(e):
  typ=e.dxftype()
  def pt(v):return tuple(round(float(x),5)for x in list(v)[:2])
  if typ=='LINE':return (typ,*sorted([pt(e.dxf.start),pt(e.dxf.end)]))
  if typ=='CIRCLE':return (typ,pt(e.dxf.center),round(e.dxf.radius,5))
  if typ=='ARC':return (typ,pt(e.dxf.center),round(e.dxf.radius,5),round(e.dxf.start_angle%360,5),round(e.dxf.end_angle%360,5),round(e.dxf.extrusion.z))
  if typ=='TEXT':return (typ,e.dxf.text,pt(e.dxf.insert))
  return (typ,)
 for p in sorted((ROOT/'DXF').glob('*.dxf')):
  path=ROOT/'DWG'/f'{p.stem}.dwg';a=ezdxf.readfile(p);b=ezdxf.readfile(back/p.name);r=subprocess.run(['/opt/homebrew/bin/dwgread','-v0','-O','JSON',str(path)],capture_output=True,text=True)
  same=sorted(map(canonical,a.modelspace()),key=str)==sorted(map(canonical,b.modelspace()),key=str)
  test(p.stem+' R2000 DWG roundtrip and independent read',same and b.units==4 and path.read_bytes()[:6]==b'AC1015'and r.returncode==0 and 'ERROR'not in r.stderr,entities=len(a.modelspace()))
  # Planar finished outlines should have no duplicate cutter entities.
  keys=[canonical(e)for e in a.modelspace()if e.dxf.layer=='CUT'];test(p.stem+' no duplicate CUT entities',len(keys)==len(set(keys)))
 (ROOT/'Verification.json').write_text(json.dumps(REPORT,indent=2))
failures=[t['name']for t in REPORT['tests']if not t['pass']];print('CHECKS',len(REPORT['tests']),'FAILURES',failures,flush=True)
assert not failures,failures
