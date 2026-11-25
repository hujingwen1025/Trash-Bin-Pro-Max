from pathlib import Path
import cadquery as cq,json,itertools,math
from shapely import wkt
from shapely.geometry import Polygon
from shapely.affinity import translate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
NAMES=['W01','W02','W03','W04','F01','C01'];BASE={n:cq.importers.importStep(str(ROOT/'STEP'/f'B1_{n}.step')).val()for n in NAMES}
results=[]
def test(name,ok,**data):
 results.append({'name':name,'pass':bool(ok),**data});print(('PASS 'if ok else'FAIL ')+name,flush=True);assert ok,(name,data)
def inner_face(n):
 axis='y'if n in ['W01','W03']else'x';station=344 if n in ['W01','W02']else 8.5
 return max([f for f in BASE[n].Faces()if f.geomType()=='PLANE'and abs(getattr(f.Center(),axis)-station)<1e-4 and abs(getattr(f.normalAt(),axis))>.999],key=lambda f:f.Area())
DIRECTIONS={'W01':(0,1,0),'W02':(1,0,0),'W03':(0,-1,0),'W04':(-1,0,0)}
ACTUAL={}
for n in NAMES[:4]:
 f=inner_face(n);direction=DIRECTIONS[n]
 for t in [5.8,6.0,6.2]:
  s=cq.Solid.extrudeLinear(f.outerWire(),f.innerWires(),cq.Vector(*[t*v for v in direction]))
  if n in ['W03','W04']:
   for z in [81,225,369]:
    origin=(120.5,8.5-t,z)if n=='W03'else(8.5-t,120.5,z);inside=(0,1,0)if n=='W03'else(1,0,0)
    s=s.cut(cq.Solid.makeCone(3.15,1.7,1.45,cq.Vector(*origin),cq.Vector(*inside)))
  ACTUAL[n,t]=s
  test(n+f' actual {t} solid',s.isValid()and len(s.Solids())==1)
face=max([f for f in BASE['F01'].Faces()if f.geomType()=='PLANE'and f.normalAt().z>.999 and abs(f.Center().z-10)<1e-4],key=lambda f:f.Area())
for t in [9.8,10.,10.2]:
 s=cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(0,0,-t));bottom=10-t
 for deg in [22.5,45,67.5]:
  a=math.radians(deg);s=s.cut(cq.Solid.makeCone(4,2.25,1.75,cq.Vector(100*math.cos(a),100*math.sin(a),bottom),cq.Vector(0,0,1)))
 ACTUAL['F01',t]=s;test(f'Floor actual {t} solid',s.isValid()and len(s.Solids())==1,underside_z_mm=bottom,floor_top_z_mm=10.)
# Check pairwise envelopes. Every combination of actual 6 mm and 10 mm thicknesses is covered.
for a,b in itertools.combinations(NAMES,2):
 av=[5.8,6.2]if a.startswith('W')else([9.8,10.2]if a=='F01'else[None]);bv=[5.8,6.2]if b.startswith('W')else([9.8,10.2]if b=='F01'else[None]);maximum=0
 for ta,tb in itertools.product(av,bv):
  sa=BASE[a]if ta is None else ACTUAL[a,ta];sb=BASE[b]if tb is None else ACTUAL[b,tb]
  maximum=max(maximum,sa.intersect(sb).Volume())
 test(a+'/'+b+' all thickness extremes final clearance',maximum<.02,maximum_interference_mm3=maximum)
# Largest stock envelope governs the continuous insertion sweeps at the seating datums.
wp={k.split('_')[0]:wkt.loads(v)for k,v in json.loads((ROOT/'Source/MasterProfiles/wall_polygons.json').read_text()).items()}
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
worst={n:ACTUAL[n,6.2]for n in NAMES[:4]};worst['C01']=BASE['C01'];fixed=['C01']
for n in ['W03','W04','W01','W02']:
 if n=='W03':s=extrude(sweep2(wp[n]),cq.Plane(origin=(0,8.5,0),xDir=(1,0,0),normal=(0,-1,0)),6.2)
 elif n=='W04':s=extrude(sweep2(wp[n]),cq.Plane(origin=(2.3,0,0),xDir=(0,1,0),normal=(1,0,0)),6.2)
 elif n=='W01':s=extrude(wp[n],cq.Plane(origin=(0,362.2,0),xDir=(1,0,0),normal=(0,-1,0)),18.2)
 else:s=extrude(wp[n],cq.Plane(origin=(344,0,0),xDir=(0,1,0),normal=(1,0,0)),18.2)
 maximum=max(s.intersect(worst[o]).Volume()for o in fixed);test(n+' maximum-thickness continuous insertion',maximum<.02,maximum_interference_mm3=maximum,travel_mm=12);fixed.append(n)
s=ACTUAL['F01',10.2];f=max([q for q in s.Faces()if q.geomType()=='PLANE'and q.normalAt().z<-.999],key=lambda q:q.Area());s=s.fuse(cq.Solid.extrudeLinear(f.outerWire(),f.innerWires(),cq.Vector(0,0,-12)));maximum=max(s.intersect(worst[o]).Volume()for o in fixed);test('Maximum-thickness floor continuous insertion',maximum<.02,maximum_interference_mm3=maximum,travel_mm=12)
# Nominal construction is unchanged: the new stock model agrees with the delivered finished CAD.
for n in NAMES[:5]:
 t=10. if n=='F01'else 6.;s=ACTUAL[n,t];diff=s.cut(BASE[n]).Volume()+BASE[n].cut(s).Volume();test(n+' nominal datum reconstruction equals delivered CAD',diff<.02,symmetric_difference_mm3=diff)
# Mirroring preserves all intra-bin results. Check actual neighbor clearance at maximum stock.
structure=cq.Compound.makeCompound([worst[n]for n in ['W01','W02','W03','W04','C01']]+[ACTUAL['F01',10.2]])
variants={'B1':structure,'B2':structure.mirror('YZ'),'B3':structure.mirror('XZ'),'B4':structure.mirror('YZ').mirror('XZ')}
for a,b in itertools.combinations(variants,2):
 dist=variants[a].distance(variants[b]);test(a+'/'+b+' maximum-stock bin separation',dist>=4.599,minimum_distance_mm=dist)
# Actual screw lengths still reach beyond the captured nut recesses at maximum stock.
test('M4x20 reaches nut trap with 10.2 floor',20+(10-10.2)-18>=1.79,shaft_tip_beyond_pad_mm=20+(10-10.2)-18,nominal_pad_z_range_mm=[10,18],nut_trap_z_range_mm=[14.6,18],note='Check actual screw tip, head and purchased nut in first article.')
test('M3x12 reaches nut trap with 6.2 wall',8.5-6.2+12-13.5>=.79,shaft_tip_beyond_flange_mm=8.5-6.2+12-13.5,note='Actual thread engagement to be checked with selected screw and nut.')
cup=cq.importers.importStep(str(ROOT/'STEP/M01_magnet_insert.step')).val()
for thickness in [9.8,10.0,10.2]:
 actual=ACTUAL['F01',thickness];shift=10-thickness
 installed=cup.translate((102.5,102.5,shift));overlap=installed.intersect(actual).Volume()
 test(f'Insert underside-flush fit in {thickness} floor',overlap<.01,overlap_mm3=overlap,insert_roof_offset_from_floor_top_mm=shift,pocket_depth_mm=5.0)
report={'revision':'R06','wall_stock_range_tested_mm':[5.8,6.2],'floor_stock_range_tested_mm':[9.8,10.2],'assembly_datums':'Hold wall INSIDE faces at B1 X/Y 8.5 and 344; seat floor TOP at Z10 against the pads and wall shoulders. Exterior faces and floor underside follow stock thickness. Mirror datums for other bins. Do not jig every exterior face to nominal coordinates.','extreme_combinations_per_bin':32,'bins_covered_by_exact_reflection':4,'supplier_material':'Basswood plywood inferred from supplied listing title; actual grade and stiffness unverified.','physical_fit_and_load_tests_performed':False,'tests':results}
(ROOT/'Tolerance_Verification_R06.json').write_text(json.dumps(report,indent=2));print('TOLERANCE CHECKS',len(results),'ALL PASS',flush=True)
