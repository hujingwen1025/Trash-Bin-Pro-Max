"""Rebuild R07 CAD, cutting profiles, named assemblies and geometry manifest.

CadQuery 2.8 / OCP. Purchased items are envelope references, never production CAD.
All part files use their own manufacturing coordinates in millimetres.
"""
from pathlib import Path
import sys,json,math,shutil,hashlib,csv
import numpy as np
import cadquery as cq
import ezdxf
import trimesh
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Software'))
from geometry import Geometry,load_config,tray_polygon,rotation
g=Geometry();c=g.c
CARRIER_Z=c["tray_surface_above_anchor_mm"]-10
TRAY_BOTTOM=c["tray_surface_above_anchor_mm"]-1
RIM_Z=c["tray_surface_above_anchor_mm"]-16
# Socket frames are fixed to the moving carrier and centred on the demanded cone.
SOCKET=[]
for i in range(6):
 dirs=[]
 for bid in c['bin_azimuth_deg']:
  for rr,tt in g.path(bid,17):
   _,hh,pp=g.points(rr,tt);dirs.append(rr.T@((hh[i]-pp[i])/g.d[i]))
 normal=np.mean(dirs,axis=0);normal/=np.linalg.norm(normal)
 radial=g.p[i]/np.linalg.norm(g.p[i]);sx=radial-normal*(radial@normal);sx/=np.linalg.norm(sx)
 angle=np.deg2rad(c['socket_ear_clock_deg']*c['drive_orientation'][i]);sx=sx*np.cos(angle)+np.cross(normal,sx)*np.sin(angle)
 SOCKET.append((sx,np.cross(normal,sx),normal))
for d in ('01_Metal/STEP','01_Metal/STL','01_Metal/DXF','01_Metal/DWG','02_Print/STEP','02_Print/STL','02_Print/DXF','02_Print/DWG','03_Purchase','04_Assembly','Verification'):(ROOT/d).mkdir(parents=True,exist_ok=True)
parts={};instances=[];profiles={}
def vec(x):return cq.Vector(*map(float,x))
def box(x,y,z,center=(0,0,0)):
 return cq.Workplane('XY').box(x,y,z).val().translate(tuple(center))
def cyl(r,h,base=(0,0,0),axis=(0,0,1)):
 return cq.Solid.makeCylinder(float(r),float(h),vec(base),vec(axis))
def sphere(r,p=(0,0,0)):return cq.Solid.makeSphere(r,vec(p),angleDegrees1=-90,angleDegrees2=90)
def poly(pts,h):
 clean=[]
 for p in pts:
  p=np.asarray(p,float)
  if not clean or np.linalg.norm(p-clean[-1])>1e-5:clean.append(p)
 if np.linalg.norm(clean[0]-clean[-1])<1e-5:clean.pop()
 return cq.Workplane('XY').polyline([tuple(p)for p in clean]).close().extrude(h).val()
def drill(s,p,r,h=1000,axis=(0,0,1)):
 p=np.array(p,float);a=np.array(axis,float);return s.cut(cyl(r,h,p-a*h/2,a))
def flat(name,pts,holes,thickness,qty,material,notes=''):
 s=poly(pts,thickness)
 for x,y,r in holes:s=drill(s,[x,y,0],r)
 add(name,s,qty,material,'metal',notes)
 profiles[name]={'outline':[list(map(float,p))for p in pts],'holes':holes,'thickness':thickness,'process':'CUT'}
 return s
def exact_bounds(shape):
 from OCP.Bnd import Bnd_Box
 from OCP.BRepBndLib import BRepBndLib
 b=Bnd_Box();BRepBndLib.AddOptimal_s(shape.wrapped,b,False,False);return list(b.Get())

def add(name,shape,qty,material,kind,notes=''):
 if not shape.isValid():raise ValueError(name+' invalid CAD')
 folder='01_Metal'if kind=='metal'else'02_Print'
 cq.exporters.export(shape,str(ROOT/folder/'STEP'/f'{name}.step'))
 cq.exporters.export(shape,str(ROOT/folder/'STL'/f'{name}.stl'),tolerance=.06,angularTolerance=.10)
 if name=='M12_Ball_Stud' or name.startswith('P09_'):
  mp=ROOT/folder/'STL'/f'{name}.stl';mesh=trimesh.load(mp,force='mesh');mesh.merge_vertices(digits_vertex=5);mesh.update_faces(mesh.nondegenerate_faces(height=1e-8));mesh.remove_unreferenced_vertices();trimesh.repair.fix_normals(mesh,multibody=True);mesh.export(mp)
 bounds=exact_bounds(shape)
 parts[name]={'shape':shape,'quantity':qty,'material':material,'kind':kind,'notes':notes,'bounds':bounds,'volume_mm3':shape.Volume(),'folder':folder}
 return shape
def frame(origin,x,y,z):
 # Basis vectors are matrix columns. Must be a proper rotation.
 T=np.eye(4);T[:3,:3]=np.array([x,y,z]).T;T[:3,3]=origin
 if np.linalg.det(T[:3,:3])<.999:raise ValueError('left-handed frame')
 return T
def placed(shape,T):
 # Rigid transform via OCC gp_Trsf to retain analytic circles.
 from OCP.gp import gp_Trsf
 tr=gp_Trsf();tr.SetValues(*[float(v)for v in T[:3].ravel()])
 return shape.located(cq.Location(tr))
def inst(name,T=np.eye(4),label=None,role='fixed'):
 s=placed(parts[name]['shape'],T);instances.append((label or name,name,s,T.tolist(),role));return s
def orient_z(direction):
 z=np.array(direction,float);z/=np.linalg.norm(z);ref=np.array([1.,0,0])
 if abs(z@ref)>.9:ref=np.array([0.,1,0])
 x=ref-z*(z@ref);x/=np.linalg.norm(x);y=np.cross(z,x);return x,y,z
def tr(p):
 T=np.eye(4);T[:3,3]=p;return T
def circle(r,n=120):return [(r*np.cos(a),r*np.sin(a))for a in np.linspace(0,2*np.pi,n,endpoint=False)]

# Central support: 60 x 3 steel tube + two 6 mm caps, total 512.5.
bolt6=[(50*np.cos(a),50*np.sin(a),3.3)for a in np.arange(6)*np.pi/3]
flat('M01_Post_Endcap',circle(72.5),bolt6+[(20*np.cos(a),20*np.sin(a),2.75)for a in np.arange(3)*2*np.pi/3]+[(12*np.cos(a),12*np.sin(a),1.7)for a in np.pi/3+np.arange(3)*2*np.pi/3],6,2,'S235 steel','Weld concentrically to M02; top/bottom faces remain flat. Six M6 clearance holes PCD100. TOP cap: weld three captive M5 rest-rod nuts and three captive M3 cable-anchor nuts underneath before closing core. Leave bottom cap auxiliary bores unused.')
add('M02_Post_Core',cyl(30,500.5).cut(cyl(27,500.5)),1,'S235 steel tube','metal','60 OD x 3 wall x 500.5 long. Weld to two M01 caps. Weld strength inspection required.')
flat('M03_Base_Backplate',circle(72.5),bolt6,3,1,'S235 steel','Six M6 through bolts with washers/nyloc nuts. Maintain flat base support.')
skin_len=math.pi*(147.5-.8)
flat('M04_Post_Shroud_Blank',[(0,0),(skin_len,0),(skin_len,512.5),(0,512.5)],[],.8,1,'5052-H32 aluminium','ROLL to OD147.5 with BUTT seam, not overlap. Bond internal15 mm splice strip, clear of endcaps. No external seam thickness in147.7 pocket. Sample roundness/seat before finishing.')
flat('M04_Internal_Splice',[(0,0),(15,0),(15,490),(0,490)],[],.8,1,'5052-H32 aluminium','Internal shroud BUTT-seam splice. Bond centred over seam, clear of endcaps. Not structural. Roll and trim on actual jig before coating.')
add('M04_INSTALLED_REFERENCE',cyl(73.75,512.5).cut(cyl(72.95,512.5)),0,'REFERENCE ONLY','metal','Rolled shape reference; cut M04_Post_Shroud_Blank instead.')

# Module coordinates: local x = crank plane horizontal, local y = shaft axis,
# local z = up. Cheeks sit behind the double crank at y=-22/-44.
cheek_outline=[(-18,-114),(-18,42),(18,42),(18,18),(58,-80),(58,-114),(22,-114),(22,-82),(18,-64),(18,-114)]
# Flatten local XZ into manufacturing XY; 8 mm plate thickness becomes local Y.
flat('M05_Bearing_Cheek',cheek_outline,[(0,0,11),(40,-96,11),(-8,-104,2.75),(16,-104,2.75),(40,-74,2.75),(-14,36,1.25),(14,36,1.25)],8,12,'6061-T6 aluminium','Output bearing0/0; input bearing40/-96. Both22 H7. Tall feet keep cranks clear of fixed deck. Guard pilots2.5 tappedM3 in rear cheek only. Common blank; drive-specific STOP holes drilled with template.')
crankpoly=Polygon([(-12,-10),(g.h-20,-10),(g.h-3,-3),(g.h+4,-3),(g.h+4,3),(g.h-3,3),(g.h-20,10),(-12,10)]).union(Point(0,0).buffer(14,quad_segs=40))
flat('M06_Crank_Plate',list(crankpoly.exterior.coords)[:-1],[(0,0,4),(g.h,0,2.1),(-8,0,1.7),(8,0,1.7),(0,-8,1.7),(0,8,1.7)],6,12,'6061-T6 aluminium','8 H7 shaft bore; clamp with8 mm M19 double hub OD24x26/PCD16/fourM3 holes per face. M4 shoulder pin through joint at100.5 mm centre distance. Require supplier drawing confirmingPCD16 before ordering hubs; sample first. No grub-screw-only torque joint.')
adapter=cyl(17,4).fuse(cyl(8,16));adapter=drill(adapter,[0,0,0],4);adapter=adapter.cut(box(2.02,1.0,20,(0,4.3,8)))
add('M07_Servo_Horn_Adapter',adapter,6,'6061-T6 aluminium','metal','8 H7 bore,2 mm keyed collar16 long; shaft key transmits torque. MATCH DRILL actual metal servo horn and retain original centre screw. No spline invented. Prototype one before six. Axial shaft retention by collars. Threaded holes need actual horn pattern.')

# Lower plate at Z520, cheek penetrations and mounts are derived from modules.
plate=cyl(270,6).intersect(poly([(-230*2**.5,0),(0,-230*2**.5),(230*2**.5,0),(0,230*2**.5)],6))
for x,y,r in bolt6:plate=drill(plate,[x,y,0],r)
plate=drill(plate,[0,0,0],8)
for angle in np.arange(3)*2*np.pi/3:plate=drill(plate,[20*np.cos(angle),20*np.sin(angle),0],2.75)
mount_holes=[];slots=[]
for i in range(6):
 B=g.B[i,:2];u=g.u[i,:2]*c['drive_orientation'][i];v=g.v[i,:2]*c['drive_orientation'][i]
 for vv in (-26,-48,26):
  if vv==26:
   # Front output-bearing cheek stops above the fixed deck; no web slot.
   for xx in (-54,-30):
    p=B+u*xx+v*(vv+10);plate=drill(plate,[*p,0],2.75);mount_holes.append((*p,2.75))
   continue
  # At the mounting plate (local z=-50 to -44), diagonal cheek web crosses.
  # Pedestal feet stand ON the deck. No web penetrates this plane.
  for xx in (-8,16):
   p=B+u*xx+v*(vv+10)
   plate=drill(plate,[*p,0],2.75);mount_holes.append((*p,2.75))
 # Cradle four M4 bolts, outside body clamp and clear of belt plane.
 for xx in (-22,59):
  for yy in ((8,15)if xx==59 else(8,59)):
   p=B+u*xx+v*yy;plate=drill(plate,[*p,0],2.25);mount_holes.append((*p,2.25))
 # Only the bottom lip of the belt cover passes this plane; its true
 # clearance port is separate from every structural foot bolt.
 cc=B+u*40+v*(-65.5);P=[cc+u*x+v*y for x,y in [(-21,-16.5),(21,-16.5),(21,16.5),(-21,16.5)]]
 plate=plate.cut(poly(P,8).translate((0,0,-1)));slots.append([list(q)for q in P])
guide_mounts=[]
for az in np.deg2rad(list(c['bin_azimuth_deg'].values())):
 u=np.array([np.cos(az),np.sin(az)]);v=np.array([-np.sin(az),np.cos(az)])
 for yy in (-150,150):
  p=u*205+v*yy;plate=drill(plate,[*p,0],2.75);guide_mounts.append((*p,2.75))
rest_holes=[(20*np.cos(a),20*np.sin(a),2.75)for a in np.arange(3)*2*np.pi/3]
add('M08_Fixed_Deck',plate,1,'6061-T6 aluminium','metal','6 mm,540 maximum OD clipped at diagonal planes230 from centre. Pedestals stand on top. Installed undersideZ520 directly on post cap; no post spacers. Clearance ports for belt guards added after fixed-cell geometry is checked.')
deckprofile=Point(0,0).buffer(270,quad_segs=90).intersection(Polygon([(-230*2**.5,0),(0,-230*2**.5),(230*2**.5,0),(0,230*2**.5)])).difference(unary_union([Polygon(q)for q in slots]))
profiles['M08_Fixed_Deck']={'outline':list(deckprofile.exterior.coords)[:-1],'holes':bolt6+[(0,0,8)]+mount_holes+guide_mounts+rest_holes,'slots':[list(q.coords)[:-1]for q in deckprofile.interiors],'thickness':6,'process':'CUT'}

# Carrier and tray. Radial ears avoid crowding adjacent platform anchors.
spider=[Point(0,0).buffer(32,quad_segs=60),Point(0,0).buffer(94,quad_segs=90).difference(Point(0,0).buffer(81,quad_segs=90))]
for angle,width,length in [(q,18,94)for q in g.pt]+[(q,14,70)for q in np.deg2rad([45,135,225,315])]:
 u=np.array([np.cos(angle),np.sin(angle)]);v=np.array([-np.sin(angle),np.cos(angle)])
 spider.append(Polygon([u*x+v*y for x,y in [(0,-width/2),(length,-width/2),(length,width/2),(0,width/2)]]))
# Positive metal bosses around both ends of every inclined threaded bore.
# The load path must not depend on a tap falling into a lightening window.
for i,p in enumerate(g.p):
 sx,sy,nn=SOCKET[i]
 for off in(-13,13):
  for zz in(CARRIER_Z,CARRIER_Z+4):
   q=p+off*sx;q=q+nn*((zz-q[2])/nn[2]);spider.append(Point(*q[:2]).buffer(5,quad_segs=48))
spider=unary_union(spider).intersection(Point(0,0).buffer(94,quad_segs=90))
carrier=poly(list(spider.exterior.coords)[:-1],4)
carrier_windows=[list(r.coords)[:-1]for r in spider.interiors]
for hole in carrier_windows:carrier=carrier.cut(poly(hole,6).translate((0,0,-1)))
carrier=drill(carrier,[0,0,0],12)
top_holes=[]
for i,p in enumerate(g.p):
 sx,sy,nn=SOCKET[i]
 for off in (-13,13):
  q=p+off*sx;q=q+nn*((CARRIER_Z+2-q[2])/nn[2]);carrier=drill(carrier,q-[0,0,CARRIER_Z],1.25,50,nn);top_holes.append((float(q[0]),float(q[1]),1.25))
brace_holes=[]
for az in np.deg2rad([45,135,225,315]):
 er=np.array([np.cos(az),np.sin(az)])
 for rad in (35,65):
  q=er*rad;carrier=drill(carrier,[*q,0],1.7);brace_holes.append((*q,1.7))
add('M09_Moving_Carrier',carrier,1,'6061-T6 aluminium','metal','4 mm; installed underside13 above joint plane. Drill2.5 and tapM3 along supplied joint axes AFTER laser cutting. P09 wedges guide the drilling; do not laser the REFERENCE circles. Use4 mm thread engagement and trim screw tips flush below carrier top; tighten0.3 Nm with threadlocker.')
profiles['M09_Moving_Carrier']={'outline':list(spider.exterior.coords)[:-1],'holes':[(0,0,12)]+brace_holes,'reference_holes':top_holes,'slots':carrier_windows,'thickness':4,'process':'CUT'}
trayholes=[]
for az in np.deg2rad([45,135,225,315]):
 er=np.array([np.cos(az),np.sin(az)])
 for rad in (35,65,125,155):
  q=er*rad;trayholes.append((*q,1.7))
for az in np.deg2rad([45,135,225,315]):
 u=np.array([np.cos(az),np.sin(az)]);v=np.array([-np.sin(az),np.cos(az)])
 for yy in (-120,0,120):trayholes.append((*(u*172+v*yy),1.7))
flat('M10_Tray',tray_polygon(),trayholes,1.0,1,'5052-H32 aluminium','360 square, corners chamfer15; rotate45deg in cabinet. MUST install M18 perimeter frame plus four M11 braces. Countersink through assembled sheet/support stack for flushM3 heads, not unsupported1 mm sheet. Set items down gently. Free-drop and impact loading are not qualified.')
# Four hat-section aluminium braces: top flange 24, web 8, feet 10 each.
brace=box(160,24,1.5,(80,0,8.25))
for yy in (-11.25,11.25):brace=brace.fuse(box(160,1.5,7.5,(80,yy,3.75)))
brace=brace.cut(box(94,40,4,(47,0,2)));brace=brace.cut(box(18,40,30,(9,0,10)))
for xx in (35,65,125,155):brace=drill(brace,[xx,0,0],1.7)
add('M11_Tray_Hat_Brace',brace,4,'5052-H32 aluminium','metal','FORM1.5 mm sheet, finished width24 and height9. Root begins at fileX18, total142 length. Webs notched4 mm high up to fileX94. Top flange against tray underside. Use3.5 mm spacers at carrier screws. Open bottom. STEP governs finished shape; shop develops blank after bend sample.')
flat('M11_FLAT_BLANK',[(0,0),(160,0),(160,38),(0,38)],[(x,19,1.7)for x in (35,65,125,155)],1.5,0,'REFERENCE ONLY','Bend allowance trial: finished profile M11 governs; neutral K-factor0.4 / inside radius1.5. Shop must develop blank and make one forming sample before four; this blank is reference only.')

# Printed servo cradle. Fits body 65.01 x 47.99 x 30, output close to one end.
cradle=box(74,58,36, (28,32,-96)).cut(box(66.2,49,33,(29.5,32,-96)))
# Open ends allow wires/auxiliary shaft; body is held by two removable straps.
cradle=cradle.cut(box(90,35,50,(28,32,-96)))
for xx in (-6,62):cradle=cradle.fuse(box(6,58,2.5,(xx,32,-112.75)))
for xx in (-12,69):
 for yy in ((8,15)if xx==69 else(8,59)):
  foot=box(10,10,6,(xx,yy,-111));foot=drill(foot,[xx,yy,-111],2.25);cradle=cradle.fuse(foot)
cradle=cradle.cut(box(14,10,10,(35,59,-110)))
cradle=cradle.cut(box(21,19,11,(65.5,56.5,-109.5)))
add('P01_Servo_Cradle',cradle,6,'PETG','print','0.5 mm nominal body clearance per side, thin rubber lining. Mount with four M4 bolts. Two stainless band straps retain body; slide servo to align actual horn, then drill strap anchors on sample. Purchase body/horn sample first.')

# Lower universal joint. Cross centre coincides with crank pin centre.
cross=sphere(9).intersect(box(16,16,16));cross=drill(cross,[0,0,0],2.1,30,(0,1,0))
for sx in (-1,1):cross=cross.cut(cyl(1.6,3,(8*sx,0,0),(-sx,0,0)))
add('P02_U_Joint_Cross',cross,6,'PETG','print','Print solid; main pivot 4.2 through Y; two 3.2 x3 blind dog-point seats along X. Ream to pins. No intersecting full pins. Grease lightly; use smooth shoulder surfaces, not screw threads as bearings.')
fork=box(24.4,10,4,(0,0,16))
for sx in (-1,1):
 ear=box(4,10,24,(sx*10.2,0,6));ear=drill(ear,[sx*10.2,0,0],2.1,40,(1,0,0));fork=fork.fuse(ear)
fork=fork.fuse(cyl(7,28,(0,0,18)))
fork=fork.cut(cyl(4.1,25,(0,0,22)));fork=drill(fork,[0,0,40],1.6,25,(1,0,0))
add('P03_Lower_Rod_Fork',fork,6,'PETG','print','Tube end22 from joint centre; socket8.2 x24. Pin M3 at40 from joint centre. Fit M3 heat-set inserts to fork outer arms for opposing dog-point pivots; adjust to rotate freely with <0.2 axial play. Q01 proves fits before production.')

# High-angle split spherical sockets, upper connection only.
socket=cyl(11,6)
for xx in (-13,13):socket=socket.fuse(box(10,10,6,(xx,0,3)))
socket=socket.cut(sphere(8.15))
socket=socket.cut(cq.Solid.makeCone(6.0,10.586,3.2,vec((0,0,3.0)),vec((0,0,1))))
for xx in (-13,13):socket=drill(socket,[xx,0,0],1.7)
add('P04_Ball_Socket_Half',socket,12,'PETG','print','Two halves enclose one M12 ball stud (ball diameter16, not M12 thread). Ball cavity16.3; neck flare55deg. Three-axis swivel required. Print solid; fit coupon and pull test before use. Identical halves, second flipped.')
stud=sphere(8).fuse(cyl(2,26.5,(0,0,7.5)))
add('M12_Ball_Stud',stud,6,'304 stainless steel','metal','TURN ball16 +/-0.02, neck4, external M4 thread from axial10 to34; root blend radius0.5 minimum. All six identical. STEP thread represented by major diameter only. Deburr/polish sphere. Do not substitute gas-spring studs with thicker neck.')
coupler=cyl(7,32,(0,0,18));coupler=coupler.cut(cyl(2.8,8,(0,0,18))).cut(cyl(4.1,25,(0,0,26)))
coupler=drill(coupler,[0,0,44],1.6,20,(1,0,0))
add('P05_Upper_Rod_Coupler',coupler,6,'PETG','print','M4x8x6 brass heat-set insert18..26 in5.6 pilot bore; tube socket8.2 from26..50; M3 through pin at44. Q01 must verify actual insert. Tube cross holes18 from each end. M4 thin jam nut against face18. Do not rely on adhesive alone.')
tube=cyl(4,c['rod_center_mm']-48).cut(cyl(3,c['rod_center_mm']-48))
for zz in (18,c['rod_center_mm']-66):tube=drill(tube,[0,0,zz],1.6,15,(1,0,0))
add('M13_Link_Tube',tube,6,'6061-T6 aluminium tube','metal',f"8 OD x1 wall x{c['rod_center_mm']-48:.3f} +/-0.10. Cross-drill3.2 at18 from each end, deburr ID. Finished joint-centre length{c['rod_center_mm']:.3f} +/-0.20, with8 mm minimum thread engagement. Same six blanks.")

# Individually labelled socket wedges; these are not arbitrary duplicated brackets.
for i,(sx,sy,nn)in enumerate(SOCKET):
 bottom=[sx*x+sy*y-nn*6 for x,y in [(-18,-5),(18,-5),(18,5),(-18,5)]]
 top=[np.array([q[0],q[1],CARRIER_Z])for q in bottom]
 wires=[cq.Wire.makePolygon([vec(q)for q in pts]+[vec(pts[0])])for pts in (bottom,top)]
 wedge=cq.Solid.makeLoft(wires).cut(sphere(8.3))
 for off in (-13,13):wedge=drill(wedge,off*sx,1.7,60,nn)
 add(f'P09_Socket_Wedge_L{i+1}',wedge,1,'PETG','print',f'Keep labelL{i+1}; flat face mounts under carrier at jointZ+13. Other face matches P04 socket. Do not interchange wedges without verifying pose. Use actual ball-stud sample and articulation test.')

# Guides: 4 identical printed chutes, local X radially outward, Y across.
run=54.;drop=270.;slope=120/40
def guide_z(x):return 750-(x-200)*120/40 if x<=240 else 630-(x-240)*150/14
floor_pts=[(200,-180,750),(240,-180,630),(254,-180,480),(254,180,480),(240,180,630),(200,180,750)]
# Extrude sloped floor vertically3, with 20 mm high side walls.
def prism3(pts,delta):
 wire=cq.Wire.makePolygon([vec(q)for q in pts]+[vec(pts[0])]);return cq.Solid.extrudeLinear(wire,[],vec(delta))
section=LineString([(200,750),(240,630),(254,480)]).buffer(-3,single_sided=True,join_style=2)
guide=prism3([(x,-180,z)for x,z in list(section.exterior.coords)[:-1]],[0,360,0])
for xx in (205,235,253):
 floor_normal=np.array([120/40 if xx<240 else 150/14,0,1.]);floor_normal/=np.linalg.norm(floor_normal)
 pts=[np.array([x,y,guide_z(x)])-3*floor_normal for x,y in [(xx-1.5,-180),(xx+1.5,-180),(xx+1.5,180),(xx-1.5,180)]]
 # Raise the rib root0.2 into the floor to avoid a disconnected tangent face.
 pts=[p+floor_normal*.2 for p in pts]
 guide=guide.fuse(prism3(pts,[0,0,-12]))
for sy in (-1,1):guide=guide.fuse(prism3([(200,sy*179,747),(240,sy*179,627),(254,sy*179,477),(254,sy*179,500),(240,sy*179,650),(210,sy*179,guide_z(210)+20),(200,sy*179,750)],[0,sy*3,0]))
# Pair of bolt ears at inlet; guide attaches to independent cross rails, not bins.
for yy in (-150,150):
 # Vertical 2020 post at radius198.2, foot atZ660. Sloped boss joins floor.
 xx=205.;zfoot=620.
 boss=prism3([(200,yy-12,zfoot),(220,yy-12,zfoot),(220,yy-12,750-(220-200)*slope),(200,yy-12,750) ],[0,24,0])
 boss=boss.cut(cyl(3.15,8,[xx,yy,620]));guide=guide.fuse(boss)
# Local file origin at inlet centre for easier slicer placement.
guide=guide.translate((-200,0,-477))
add('P06_Discharge_Guide',guide,4,'PETG','print','True3 mm floor thickness NORMAL to slope; three12 mm underside ribs. One piece. Bosses extend2 mm inward from inlet. Use0.3 PET/PP smooth liner. M5x8x7 inserts in6.3 blind pilots, M5x20 studs into2020 posts. Remove whole guide/post module via twoM5 thumb bolts beneath fixed deck. InletR200/Z750; kneeR240/Z630; outletR254/Z480; boss footZ620.')

# Guide support: four legs off fixed deck to a rail across each guide.
# Purchased 2020 profiles are represented here; printed caps attach via T-nuts.
cap=box(30,30,12).cut(box(20.4,20.4,10,(0,0,-1)))
cap=drill(cap,[0,0,0],2.75)
add('P07_Guide_Post_Cap',cap,8,'PETG','print','Fits2020 profile20.0 nominal,0.2 per side. Centre5.5 clearance forM5 stud; profile4.2 bore tappedM5. Fit actual extrusion sample first.')
rest=cyl(10,12);rest=drill(rest,[0,0,0],2.75);rest=rest.cut(cyl(5.25,8,(0,0,4)))
add('P08_Rest_Pad',rest,3,'TPU95A','print','M5 adjustable support pad, resting contact only; not structural fastener. Three pads on independent support tower at radius20.')

# Angle feet, tensioner arms, and custom smooth-tip pivots.
foot=box(40,12,3,(0,6,-112.5)).fuse(box(40,3,20,(0,1.5,-104)))
for xx in (-8,16):
 foot=drill(foot,[xx,6,-114],2.75);foot=drill(foot,[xx,0,-104],2.75,40,(0,1,0))
add('M14_Angle_Foot',foot,18,'6061-T6 aluminium angle','metal','40 length,20 vertical x12 horizontal x3 angle, cut down20x20 stock. Two5.5 holes in each leg. One foot per cheek. Purchase angle stock then drill, or machine from STEP. Keep inside corner radius clear of cheek.')
flat('M17_Front_Output_Cheek',[(-64,-114),(-24,-114),(-24,-42),(18,-42),(18,42),(-64,42)],[(0,0,11),(-54,-104,2.75),(-30,-104,2.75)],8,6,'6061-T6 aluminium','Tall front bearing/hard-stop pedestal.22 H7 bore. FinishedD1-D6 versions govern stop holes.')
tension=poly([(13,-81),(63,-81),(63,-30),(30,-30),(13,-54)],4)
for xx,yy,rr in [(40,-74,2.75),(50.3,-44,4.25)]:tension=drill(tension,[xx,yy,0],rr)
# Arc clamp slot around the existing cheek mounting hole16/-34.
slotpts=[]
for radius,angles in [(37.0,np.linspace(150,174,30)),(31.5,np.linspace(174,150,30))]:
 for aa in np.deg2rad(angles):slotpts.append((50+radius*np.cos(aa),-48+radius*np.sin(aa)))
# A tensioner is match-clamped on sample; don't invent a nonmatching final hole.
add('M15_Belt_Tensioner',tension,6,'6061-T6 aluminium','metal','4 mm plate. Pivot5.5 at40/-74, idler8.5 at50.3/-44. Match drill clamp hole against actual sample cheek after setting360-5M-15 belt tension; no automatic fabrication release for that finishing operation.')
profiles['M15_Belt_Tensioner']={'outline':[(13,-81),(63,-81),(63,-30),(30,-30),(13,-54)],'holes':[(40,-74,2.75),(50.3,-44,4.25)],'thickness':4,'process':'CUT'}
pivot=cyl(1.5,12,axis=(1,0,0))
add('M16_Smooth_Tip_Pivot',pivot,12,'304 stainless steel','metal','M3 external thread first9 mm, final3 mm smooth diameter3.0 -0.03. Slot head or wrench flats at outer end. Adjust tip2.5 mm into P02 blind seat, secure M3 jam nut; never clamp cross solid.')

# Lightweight closed perimeter frame prevents unsupported tray edges bending.
outer=Polygon(tray_polygon()).buffer(-1,join_style=2);inner=Polygon(tray_polygon()).buffer(-16,join_style=2);webinner=Polygon(tray_polygon()).buffer(-2,join_style=2)
rim=poly(list(outer.exterior.coords)[:-1],15).cut(poly(list(webinner.exterior.coords)[:-1],14))
rim=rim.cut(poly(list(inner.exterior.coords)[:-1],17).translate((0,0,-1)))
for x,y,rr in trayholes[16:]:rim=drill(rim,[x,y,0],rr)
add('M18_Tray_Perimeter_Frame',rim,1,'6063-T5 aluminium','metal','Eight mitred15x15x1 angle segments, jig to STEP and weld/join into one ring. Four long and four short segments;22.5deg end mitres. Test one frame before tray batch. Finished top face15 above local underside, installed7 above joint plane. Top holes match tray. Do not print this frame.')

# Belt cases cover pulley/idler pinch points; open only toward the fixed cheek.
casepoly=unary_union([Point(0,0).buffer(34,quad_segs=60),Point(40,-96).buffer(23,quad_segs=60),Point(50.3,-44).buffer(24,quad_segs=60),Point(-14,36).buffer(5,quad_segs=30),Point(14,36).buffer(5,quad_segs=30)]).convex_hull
case=poly(list(casepoly.exterior.coords)[:-1],27);void=casepoly.buffer(-2.4,join_style=2)
case=case.cut(poly(list(void.exterior.coords)[:-1],24.6))
for x,y in [(-14,36),(14,36)]:case=case.fuse(cyl(4,27,(x,y,0)));case=drill(case,[x,y,0],1.7)
for x,y in [(0,0),(40,-96)]:case=drill(case,[x,y,0],6)
add('P10_Belt_Guard',case,6,'PETG','print','Two M3x35 screws into tapped rear cheek;27 mm spacers are integral. Guard before powered tests. Ventilation open toward cheek. Use20T TOOTHED inside idler, never small smooth backside idler. Inspect belt/idler clearances with power disconnected.')

# Hard-stop drill templates: paired cheeks are match-drilled, common blanks remain identical.
allalph=np.array([g.ik(R,t)for b in c['bin_azimuth_deg']for R,t in g.path(b,161)])
STOP=[]
for i in range(6):
 coords=[]
 for angle,side in [(allalph[:,i].min()-np.deg2rad(3),-1),(allalph[:,i].max()+np.deg2rad(3),1)]:
  xy=28*np.array([np.cos(angle),np.sin(angle)])+side*13*np.array([-np.sin(angle),np.cos(angle)])
  coords.append((float(xy[0]*c['drive_orientation'][i]),float(xy[1]),3.1))
 STOP.append(coords)
 templ=poly([(-18,-42),(18,-42),(18,42),(-18,42)],2)
 for x,y,r in [(0,0,4.1)]+coords:templ=drill(templ,[x,y,0],r)
 add(f'Q02_Stop_Template_D{i+1}',templ,1,'PETG','print',f'DriveD{i+1} only. Locate on8 mm output shaft; clamp/template zero to cheek vertical. Drill6.2 through FRONT M05 and M17 pair. Two diameter6 shoulder stops supported at both ends; test without power. Template not a working stop.')
 for base in ('M05_Bearing_Cheek','M17_Front_Output_Cheek'):
  shape=parts[base]['shape'];pf={**profiles[base]}
  if base=='M17_Front_Output_Cheek':
   # The rod passes near the offset auxiliary pedestal in some tilted poses.
   # Relieve its projected swept tube envelope, not merely a single pose.
   cuts=[];mu=g.u[i]*c['drive_orientation'][i];mv=g.v[i]*c['drive_orientation'][i]
   for bid in c['bin_azimuth_deg']:
    for rr,tt in g.path(bid,61):
     _,hh,pp=g.points(rr,tt);direction=(pp[i]-hh[i])/g.d[i]
     aa=hh[i]+22*direction-g.B[i];bb=pp[i]-26*direction-g.B[i]
     va,vb=aa@mv,bb@mv
     if abs(vb-va)<1e-9:
      if not 14<=va<=38:continue
      left,right=0.,1.
     else:
      vals=sorted(((14-va)/(vb-va),(38-va)/(vb-va)));left=max(0.,vals[0]);right=min(1.,vals[1])
      if left>right:continue
     a1=aa+(bb-aa)*left;b1=aa+(bb-aa)*right
     cuts.append(LineString([(a1@mu,a1[2]),(b1@mu,b1[2])]).buffer(6,quad_segs=12))
   if cuts:
    footprint=Polygon(pf['outline']).difference(unary_union(cuts)).simplify(.02,preserve_topology=True).buffer(0)
    if footprint.geom_type!='Polygon' or not footprint.buffer(.001).covers(Point(0,0).buffer(14,quad_segs=60)):
     raise ValueError('Auxiliary pedestal relief breaks minimum bearing web; redesign required')
    shape=poly(list(footprint.exterior.coords)[:-1],8)
    for ring in footprint.interiors:shape=shape.cut(poly(list(ring.coords)[:-1],10).translate((0,0,-1)))
    for xx,yy,rad in pf['holes']:shape=drill(shape,[xx,yy,0],rad)
    pf['outline']=list(footprint.exterior.coords)[:-1];pf['slots']=[list(q.coords)[:-1]for q in footprint.interiors]
  for xx,yy,rr in coords:shape=drill(shape,[xx,yy,0],rr)
  key=f'{base}_D{i+1}_FINISHED'
  add(key,shape,1,'6061-T6 aluminium','metal',f'DriveD{i+1} finished stop bores. Same outline as common blank; finishing holes make this handed/label-specific. Do not order extra blank on top of this finished part.')
  profiles[key]={**pf,'holes':pf['holes']+coords}
parts['M05_Bearing_Cheek']['quantity']=6
parts['M05_Bearing_Cheek']['notes']+=' Order6 rear blanks plus six separately labelled finished FRONT versions, not12+6.'
parts['M17_Front_Output_Cheek']['quantity']=0
parts['M17_Front_Output_Cheek']['notes']+=' Blank reference only; order six finishedD1-D6 versions instead.'

# Positive keyed torque transmission; shaft collars only retain axially.
hub=cyl(12,26,(0,0,-13));hub=drill(hub,[0,0,0],4);hub=hub.cut(box(2.02,1.0,30,(0,4.3,0)))
for xx,yy in [(-8,0),(8,0),(0,-8),(0,8)]:
 hub=hub.cut(cyl(1.25,6,(xx,yy,-13))).cut(cyl(1.25,6,(xx,yy,13),(0,0,-1)))
add('M19_Double_Crank_Hub',hub,6,'C45 quenched/tempered steel','metal','Yield>=500 MPa with supplier certificate. OD24 x26; bore8 H7,2 H9 keyway0.8 deep. FourM3 blind taps6 deep PCD16 at EACH end, pilot2.5 shown. Two crank plates share one hub. M3x10 screws with1 mm washers engage3 mm minimum; blue threadlocker.')
for name,length in [('M20_Output_Shaft',124.),('M21_Input_Shaft',82.)]:
 shaft=cyl(4,length).cut(box(2,2, length+2,(0,3.8,length/2)))
 add(name,shaft,6,'C45 quenched/tempered steel','metal',f'Yield>=500 MPa. OD8 h6 x{length:g}, keyseat2 P9 width x1.2 deep, full length as STEP. Deburr slot lips, polish bearing seats. Axial collars both ends. Keys transmit torque; no set-screw-only drive.')
key=box(2,2,14,(0,3.8,0))
add('M22_Parallel_Key',key,24,'C45 steel','metal','2 h9 x2 x14 standard parallel key. Prototype actual2 mm key/keyway fit. Four per drive: two output shaft seats, two input shaft seats. Same24 parts; buy stock keys rather than print.')

# Independent padded backstops catch ballistic overshoot; bins carry no impact fixtures.
flat('M23_Frame_Outrigger',[(0,0),(70,0),(70,70),(0,70)],[(x,y,3.3)for x in (15,35)for y in (15,35)]+[(60,60,2.75),(45,60,2.75),(60,45,2.75)],6,4,'S235 steel','Four identical corner plates. Installed under original base at corner; fourM6 flush-head through bolts into base plus post centreM5 and two reinforced feet. Mirror plate placement by rotating aboutZ; hole pattern symmetric underX/Y exchange.')
flat('M24_Backstop_Panel',[(-180,0),(180,0),(180,300),(-180,300)],[(x,y,2.75)for x in(-155,155)for y in(30,140,250)],2,4,'5052-H32 aluminium','Same four360x300 panels. Installed radial planeR300, bottomZ500, topZ800. Bond20 mmEVA foam on bin-facing surface; trim foam around screws and radius all edges. Four instrumented physical impact trials before service.')
near=365-(312+155)/np.sqrt(2);far=365-(312-155)/np.sqrt(2)
for name,distance,qty in [('M25_Short_Backstop_Bridge',near,16),('M26_Anti_Rack_Bridge',far,8)]:
 flat(name,[(-12,-15),(distance+10,-15),(distance+10,15),(-12,15)],[(0,0,2.75),(distance,0,2.75)],3,qty,'S235 steel','Upper/lower bridges bolt to2020 end taps and outer railT-nuts. Long bridge stacks with short bridge at one upright per panel; use3 mm spacers at its outer rail end. This triangle prevents free racking; do not omit long bridge.')

flat('M28_Radial_Deck_Rib',[(0,0),(140,0),(140,20),(0,20)],[],3,6,'6061-T6 aluminium','Six140x20x3 ribs beneath M08, radius75..215, upper edgeZ520. Shop weld3 mm fillets both sides, stagger30 mm welds/15 mm gaps; jig deck flat, inspect welds and final anchor planes. Weld before final precision holes/reaming. As-welded aluminium strength governs; verify deck deflection physically. Do not omit ribs.')

# Cable attachment holes, deliberately close to central disk to avoid trash paths.
for name,radius in [('M08_Fixed_Deck',12),('M09_Moving_Carrier',25)]:
 for aa in np.pi/3+np.arange(3)*2*np.pi/3:
  q=radius*np.array([np.cos(aa),np.sin(aa)]);parts[name]['shape']=drill(parts[name]['shape'],[*q,0],1.7);profiles[name]['holes'].append((*q,1.7))
 # Refresh modified part files and mass metadata after drilling.
 p=parts[name];p['volume_mm3']=p['shape'].Volume()
 cq.exporters.export(p['shape'],str(ROOT/p['folder']/'STEP'/f'{name}.step'))
 cq.exporters.export(p['shape'],str(ROOT/p['folder']/'STL'/f'{name}.stl'),tolerance=.06,angularTolerance=.10)

# Coupons combine actual bearing/shaft/ball/tube interfaces; no full expensive set first.
coupon=box(90,28,8,(45,0,4))
for x,r in [(12,4.0),(32,4.1),(56,11),(79,2.1)]:coupon=drill(coupon,[x,0,0],r)
add('Q01_Fit_Ladder',coupon,1,'PETG','print','Extra sample: bores8.0,8.2,22.0,4.2 left to right. Also print2xP04 and1xP02/P03/P05 before six sets. Heat-set insert bores must be sized to actual insert datasheet, sample first.')

# Generate flat cutting/reference drawings. CUT only on truly planar cut parts.
for name,info in profiles.items():
 folder=parts[name]['folder'];d=ezdxf.new('R2000');d.units=4
 for lay,col in [('CUT',1),('REFERENCE',5)]:d.layers.new(lay,dxfattribs={'color':col})
 m=d.modelspace();layer='REFERENCE'if 'REFERENCE'in name or 'FLAT_BLANK'in name else'CUT'
 m.add_lwpolyline(info['outline'],close=True,dxfattribs={'layer':layer})
 # Leave machining stock on precision bores: these are ROUGH cut profiles.
 info['cut_holes']=[(float(x),float(y),10.75 if abs(r-11)<1e-8 and name.startswith(('M05','M17')) else 3.75 if abs(r-4)<1e-8 and name=='M06_Crank_Plate' else float(r))for x,y,r in info['holes']]
 for x,y,r in info['cut_holes']:m.add_circle((float(x),float(y)),float(r),dxfattribs={'layer':layer})
 for x,y,r in info.get('reference_holes',[]):m.add_circle((float(x),float(y)),float(r),dxfattribs={'layer':'REFERENCE'})
 for pts in info.get('slots',[]):m.add_lwpolyline(pts,close=True,dxfattribs={'layer':layer})
 m.add_text(name+' | mm 1:1 | ROUGH precision bores21.5 to22H7,7.5 to8H7 as applicable; kerf once | '+layer,dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-240 if name=='M08_Fixed_Deck'else -22))
 d.saveas(ROOT/folder/'DXF'/f'{name}.dxf')

# Stock/purchased references are not manufacture instructions.
purchase={
 'Servo_Envelope':box(65.01,47.99,30,(29.5,32,0)),
 '608_Bearing':cyl(11,7,axis=(0,1,0)).cut(cyl(4,7,axis=(0,1,0))),
 'Pulley36':cyl(30,15,(0,-72.5,0),(0,1,0)).cut(cyl(4,15,(0,-72.5,0),(0,1,0))),
 'Pulley20':cyl(18,15,(0,-72.5,0),(0,1,0)).cut(cyl(4,15,(0,-72.5,0),(0,1,0))),
 '2020_Extrusion':box(20,20,92,(0,0,46)),
 'Rest_Tower':cyl(2.5,c['rest_height_mm']+140),
 'Post_Spacer':cyl(6,50).cut(cyl(3.3,50)),
 'Idler':cyl(18,16,(0,-73,0),(0,1,0)).cut(cyl(4,16,(0,-73,0),(0,1,0))),
 'Stop_Pin':cyl(3,60,(0,-30,0),(0,1,0)),
 'Outer_Post_820':box(20,20,820,(0,0,410)),
 'Outer_Rail_710':box(710,20,20),
 'Backstop_Upright_320':box(20,20,320,(0,0,160)),
 'Backstop_Rib_290':box(20,290,20),
 'Foam_Pad':box(20,358,298,(0,0,149)),
 'Rubber_Foot':box(40,40,20,(0,0,-10)).cut(box(18,18,10,(-10,-10,-5)))}
for name,s in purchase.items():cq.exporters.export(s,str(ROOT/'03_Purchase'/f'{name}_REFERENCE.step'))

for key in ('Pulley36','Pulley20'):
 purchase[key]=purchase[key].cut(box(1.0,20,2.02,(4.3,-65,0)))
 cq.exporters.export(purchase[key],str(ROOT/'03_Purchase'/f'{key}_REFERENCE.step'))

def build_assembly(R,t,label,export=True):
 global instances
 instances=[];z0=c['crank_axis_global_z_mm'];azero=np.array([0,0,z0]);a,H,P=g.points(R,t)
 inst('M01_Post_Endcap',tr([0,0,7.5]),'post bottom')
 inst('M02_Post_Core',tr([0,0,13.5]),'post core')
 inst('M01_Post_Endcap',tr([0,0,514]),'post top')
 inst('M03_Base_Backplate',tr([0,0,-3]),'base backplate')
 inst('M04_INSTALLED_REFERENCE',tr([0,0,7.5]),'shroud')
 inst('M08_Fixed_Deck',tr([0,0,520]),'fixed deck')
 for aa in np.deg2rad(c['deck_rib_phase_deg'])+np.arange(6)*np.pi/3:
  u=np.array([np.cos(aa),np.sin(aa),0]);v=np.array([-np.sin(aa),np.cos(aa),0])
  inst('M28_Radial_Deck_Rib',frame(u*75+v*1.5+[0,0,500],u,[0,0,1],-v),f'deck rib {aa}')
 refs=[]
 def ref(n,T,l):refs.append((l,n,placed(purchase[n],T),T.tolist(),'reference'))
 # No post spacers in final arrangement.
 for i in range(6):
  u,v=g.u[i],g.v[i];B=g.B[i]+azero
  mu,mv=u*c['drive_orientation'][i],v*c['drive_orientation'][i]
  F=frame(B,mu,mv,[0,0,1])
  inst('P01_Servo_Cradle',F@tr([-10,0,0]),f'D{i+1} cradle')
  # Plate manufacturing XY -> module XZ, thickness goes toward -Y.
  for vv in (-22,-44):
   key=f'M05_Bearing_Cheek_D{i+1}_FINISHED'if vv==-22 else'M05_Bearing_Cheek'
   inst(key,frame(B+mv*vv,mu,[0,0,1],-mv),f'D{i+1} cheek{vv}')
   inst('M14_Angle_Foot',F@tr([0,vv,0]),f'D{i+1} foot{vv}')
  ref('Servo_Envelope',F@tr([-10,0,-96]),f'D{i+1} servo')
  hx=np.cos(a[i])*u+np.sin(a[i])*np.array([0,0,1])
  # Keyway is along local +Y in turned-part files.
  kx=np.cross(hx,mv);ky=hx
  inst('M20_Output_Shaft',frame(B-mv*82,kx,ky,mv),f'D{i+1} output shaft','moving')
  inst('M19_Double_Crank_Hub',frame(B,kx,ky,mv),f'D{i+1} crank hub','moving')
  inst('M21_Input_Shaft',frame(B+mu*40+[0,0,-96]-mv*82,[0,0,1],mu,mv),f'D{i+1} input shaft')
  for vv in (-65,0):inst('M22_Parallel_Key',frame(B+mv*vv,kx,ky,mv),f'D{i+1} output key{vv}','moving')
  for vv in (-65,-8):inst('M22_Parallel_Key',frame(B+mu*40+[0,0,-96]+mv*vv,[0,0,1],mu,mv),f'D{i+1} input key{vv}')
  for vv in (-29.5,-51.5):
   ref('608_Bearing',F@tr([0,vv,0]),f'D{i+1} output bearing {vv}')
   ref('608_Bearing',F@tr([40,vv,-96]),f'D{i+1} input bearing {vv}')
  ref('Pulley36',frame(B,hx,mv,kx),f'D{i+1}36T');ref('Pulley20',F@tr([40,0,-96]),f'D{i+1}20T')
  inst(f'M17_Front_Output_Cheek_D{i+1}_FINISHED',frame(B+mv*30,mu,[0,0,1],-mv),f'D{i+1} front cheek')
  inst('M14_Angle_Foot',F@tr([-46,30,0]),f'D{i+1} front foot')
  ref('608_Bearing',F@tr([0,22.5,0]),f'D{i+1} front bearing')
  inst('M15_Belt_Tensioner',frame(B-mv*52,mu,[0,0,1],-mv),f'D{i+1} tensioner')
  inst('P10_Belt_Guard',frame(B-mv*52,mu,[0,0,1],-mv),f'D{i+1} belt guard')
  ref('Idler',F@tr([50.3,0,-44]),f'D{i+1} idler')
  for k,(xx,zz,rr)in enumerate(STOP[i]):ref('Stop_Pin',F@tr([xx,0,zz]),f'D{i+1} stop{k}')
  # Crank local X points to H. Plate normal +Y, two identical side plates.
  hx=np.cos(a[i])*u+np.sin(a[i])*np.array([0,0,1]);hy=np.cross(v,hx)
  for vv in (-16,16):inst('M06_Crank_Plate',frame(B+v*(vv-3),hx,hy,v),f'D{i+1} crank{vv}','moving')
  inst('M07_Servo_Horn_Adapter',frame(B+mu*40+[0,0,-96],np.array([0,0,-1]),mu,-mv),f'D{i+1} horn adapter')
  rod=(P[i]-H[i])/g.d[i]
  # U joint primary Y follows crank shaft. Secondary X lies perpendicular to rod/Y.
  xx=np.cross(v,rod);xx/=np.linalg.norm(xx);zz=np.cross(xx,v)
  inst('P02_U_Joint_Cross',frame(H[i]+azero,xx,v,zz),f'L{i+1} cross','moving')
  yy=np.cross(rod,xx)
  inst('P03_Lower_Rod_Fork',frame(H[i]+azero,xx,yy,rod),f'L{i+1} lower fork','moving')
  for sx in (-1,1):inst('M16_Smooth_Tip_Pivot',frame(H[i]+azero+sx*17.5*xx,-sx*xx,-sx*yy,rod),f'L{i+1} pivot{sx}','moving')
  inst('M13_Link_Tube',frame(H[i]+azero+22*rod,xx,yy,rod),f'L{i+1} tube','moving')
  inst('M12_Ball_Stud',frame(P[i]+azero,*orient_z(-rod)),f'L{i+1} ball stud','moving')
  inst('P05_Upper_Rod_Coupler',frame(P[i]+azero,xx,-yy,-rod),f'L{i+1} upper coupler','moving')
  # Socket orientation centred on its full demanded articulation cone.
  sx,sy,mean=SOCKET[i]
  sock=frame(P[i]+azero,R@sx,R@sy,R@mean)
  inst('P04_Ball_Socket_Half',sock,f'L{i+1} socket a','moving')
  inst('P04_Ball_Socket_Half',sock@frame([0,0,0],[1,0,0],[0,-1,0],[0,0,-1]),f'L{i+1} socket b','moving')
  inst(f'P09_Socket_Wedge_L{i+1}',frame(P[i]+azero,R[:,0],R[:,1],R[:,2]),f'L{i+1} wedge','moving')
 inst('M09_Moving_Carrier',frame(np.asarray(t)+azero+R@np.array([0,0,CARRIER_Z]),R[:,0],R[:,1],R[:,2]),'carrier','moving')
 inst('M10_Tray',frame(np.asarray(t)+azero+R@np.array([0,0,TRAY_BOTTOM]),R[:,0],R[:,1],R[:,2]),'tray','moving')
 inst('M18_Tray_Perimeter_Frame',frame(np.asarray(t)+azero+R@np.array([0,0,RIM_Z]),R[:,0],R[:,1],R[:,2]),'perimeter frame','moving')
 for az in np.deg2rad([45,135,225,315]):
  ux=np.array([np.cos(az),np.sin(az),0]);vy=np.array([-np.sin(az),np.cos(az),0]);inst('M11_Tray_Hat_Brace',frame(np.asarray(t)+azero+R@np.array([0,0,CARRIER_Z]),R@ux,R@vy,R[:,2]),f'brace{az}','moving')
 for bid,az in c['bin_azimuth_deg'].items():
  aa=np.deg2rad(az);u=np.array([np.cos(aa),np.sin(aa),0]);v=np.array([-np.sin(aa),np.cos(aa),0]);
  inst('P06_Discharge_Guide',frame(u*200+[0,0,477],u,v,[0,0,1]),bid+' guide')
  for yy in (-150,150):
   pos=u*205+v*yy
   ref('2020_Extrusion',frame(pos+[0,0,526],u,v,[0,0,1]),f'{bid} guide post{yy}')
   inst('P07_Guide_Post_Cap',frame(pos+[0,0,614],u,v,[0,0,1]),f'{bid} guide cap{yy}')
 for aa in np.arange(3)*2*np.pi/3:
  pos=np.array([20*np.cos(aa),20*np.sin(aa),0]);ref('Rest_Tower',tr(pos+[0,0,510]),f'rest tower {aa}')
  inst('P08_Rest_Pad',tr(pos+[0,0,z0+c['rest_height_mm']+CARRIER_Z-12]),f'rest pad {aa}')
 # Outer frame is750 square; rails leave clearance for bins to slide out belowZ490.
 for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
  # Proper rotations preserve the symmetric outrigger hole pattern.
  angle=np.arctan2(sy,sx)-np.pi/4;rot=rotation([0,0,1],angle)
  inst('M23_Frame_Outrigger',frame(rot@np.array([305,305,-6.]),rot[:,0],rot[:,1],rot[:,2]),f'corner outrigger{sx}/{sy}')
  ref('Outer_Post_820',tr([sx*365,sy*365,0]),f'frame post{sx}/{sy}')
  ref('Rubber_Foot',frame([sx*350,sy*350,-6],rot[:,0],rot[:,1],rot[:,2]),f'foot{sx}/{sy}')
 for zz in (500,800):
  for sign in (-1,1):
   ref('Outer_Rail_710',tr([0,sign*365,zz]),f'frame X rail{sign}/{zz}')
   ref('Outer_Rail_710',frame([sign*365,0,zz],[0,1,0],[-1,0,0],[0,0,1]),f'frame Y rail{sign}/{zz}')
 for bid,az in c['bin_azimuth_deg'].items():
  az=np.deg2rad(az);n=np.array([np.cos(az),np.sin(az),0]);tan=np.array([-np.sin(az),np.cos(az),0])
  inst('M24_Backstop_Panel',frame(n*300+[0,0,500],tan,[0,0,1],n),bid+' backstop')
  ref('Foam_Pad',frame(n*290+[0,0,501],n,tan,[0,0,1]),bid+' foam')
  for side in (-1,1):
   p=n*312+tan*155*side;ref('Backstop_Upright_320',frame(p+[0,0,490],n,tan,[0,0,1]),f'{bid} upright{side}')
   dominant=int(np.argmax(np.abs(p[:2])));axis=np.zeros(3);axis[dominant]=np.sign(p[dominant]);across=np.cross([0,0,1],axis)
   for zz in (487,810):inst('M25_Short_Backstop_Bridge',frame(p+[0,0,zz],axis,across,[0,0,1]),f'{bid} short bridge{side}/{zz}')
   if side==1:
    longaxis=np.zeros(3);longaxis[1-dominant]=np.sign(p[1-dominant]);crossaxis=np.cross([0,0,1],longaxis)
    for zz in (484,813):inst('M26_Anti_Rack_Bridge',frame(p+[0,0,zz],longaxis,crossaxis,[0,0,1]),f'{bid} long bridge{zz}')
  ref('Backstop_Rib_290',frame(n*312+[0,0,640],n,tan,[0,0,1]),bid+' backstop middle rail')
 ass=cq.Assembly(name=label)
 colors={'metal':cq.Color(.65,.70,.75),'print':cq.Color(.16,.58,.62)}
 for n,key,s,T,role in instances:ass.add(s,name=n,color=colors[parts[key]['kind']])
 for n,key,s,T,role in refs:ass.add(s,name=n,color=cq.Color(.35,.37,.42))
 if export:
  ass.save(str(ROOT/'04_Assembly'/f'{label}.step'))
  cq.exporters.export(cq.Compound.makeCompound([s for _,_,s,_,_ in instances+refs]),str(ROOT/'04_Assembly'/f'{label}.stl'),tolerance=.15,angularTolerance=.15)
 return instances,refs

if __name__=='__main__':
 home,refs=build_assembly(np.eye(3),[0,0,c['rest_height_mm']],'R07_Level_Assembly')
 # One complete system with exact R06 bin solids and reconstructed base interface.
 base=box(700,700,20,(0,0,10)).cut(cyl(73.85,12.5,(0,0,7.5)))
 for xx in (-250,-102.5,102.5,250):
  for yy in (-250,-102.5,102.5,250):base=base.cut(cyl(12.6,5,(xx,yy,15)))
 # Newly authorized mounting holes through the 7.5 mm pocket floor.
 cornerholes=[(sx*x,sy*y,3.3)for sx in(-1,1)for sy in(-1,1)for x in(320,340)for y in(320,340)]
 for xx,yy,rr in bolt6+cornerholes:
  base=drill(base,[xx,yy,0],rr)
  if (xx,yy,rr)in cornerholes:base=base.cut(cq.Solid.makeCone(3.3,6.5,3.2,vec((xx,yy,16.8)),vec((0,0,1))))
 cq.exporters.export(base,str(ROOT/'04_Assembly'/'Base_Interface_With_Mounting_Holes.step'))
 # Drill template is not a replacement base cutting outline.
 d=ezdxf.new('R2000');d.units=4;d.layers.new('DRILL',dxfattribs={'color':1});d.layers.new('REFERENCE',dxfattribs={'color':5});m=d.modelspace();m.add_circle((0,0),73.85,dxfattribs={'layer':'REFERENCE'})
 for xx,yy,rr in bolt6+cornerholes:m.add_circle((xx,yy),rr,dxfattribs={'layer':'DRILL'})
 m.add_text('BASE MODIFICATION ONLY | six6.6 PCD100 + sixteen6.6 corner holes CSK13x90deg | centre on pocket',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((-80,-90))
 d.saveas(ROOT/'01_Metal'/'DXF'/'BASE_Drill_Template.dxf')
 system=cq.Assembly(name='R07 with R06 bins');system.add(base,name='base interface reference',color=cq.Color(.70,.61,.43))
 allsystem=[base]
 for n,key,s,T,role in home:system.add(s,name=n,color=cq.Color(.15,.55,.60)if parts[key]['kind']=='print'else cq.Color(.65,.7,.74));allsystem.append(s)
 for n,key,shape,T,role in refs:
  system.add(shape,name=n,color=cq.Color(.35,.37,.42));allsystem.append(shape)
 for bid in c['bin_azimuth_deg']:
  bp=ROOT.parent/'Rev 06 - 10mm Basswood Hybrid Bins'/'STEP'/f'{bid}_Assembly.step'
  bs=cq.importers.importStep(str(bp)).val().translate((0,0,20));system.add(bs,name=bid+' R06 reference',color=cq.Color(.80,.71,.53));allsystem.append(bs)
 system.save(str(ROOT/'04_Assembly'/'R07_Complete_System.step'))
 cq.exporters.export(cq.Compound.makeCompound(allsystem),str(ROOT/'04_Assembly'/'R07_Complete_System.stl'),tolerance=.15,angularTolerance=.15)
 (ROOT/'Verification'/'instance_transforms.json').write_text(json.dumps([{'instance':n,'part':key,'transform':T,'role':role}for n,key,s,T,role in home],indent=2))
 for bid in c['bin_azimuth_deg']:
  R,t=list(g.path(bid,2))[-1];build_assembly(R,t,'R07_Dump_'+bid)

 # Machining coordinates: all upper holes are inclined, not vertical cutouts.
 with (ROOT/'01_Metal'/'Carrier_Joint_Hole_Axes.csv').open('w',newline='')as f:
  w=csv.writer(f);w.writerow(['joint','hole','X_mm','Y_mm','Z_mm_carrier_local','axis_X','axis_Y','axis_Z','pilot_mm','thread','minimum_engagement_mm','screw_underhead_to_carrier_top_mm'])
  for i,p in enumerate(g.p):
   sx,sy,nn=SOCKET[i]
   for k,off in enumerate((-13,13),1):
    start=p+sx*off+nn*6
    distance=(CARRIER_Z+4-start[2])/(-nn[2])
    w.writerow([f'L{i+1}',k,*[round(float(x),6)for x in (start-[0,0,CARRIER_Z])],*[round(float(x),8)for x in -nn],2.5,'M3',4,round(float(distance),3)])
 # Expanded assembly has real rigid part transforms, not a printable fused model.
 ex=cq.Assembly(name='R07 exploded reference');exsolids=[]
 for name,key,shape,T,role in home+refs:
  T=np.array(T);delta=np.zeros(3)
  if name.startswith('D'):i=int(name[1])-1;delta=g.B[i]/np.linalg.norm(g.B[i])*90
  elif name.startswith('L'):delta=np.array([0,0,160.])
  elif role=='moving':delta=np.array([0,0,250.])
  elif name.endswith('guide'):delta=T[:3,0]*100
  T[:3,3]+=delta
  original=parts[key]['shape']if key in parts else purchase[key]
  shape=placed(original,T);ex.add(shape,name=name);exsolids.append(shape)
 ex.save(str(ROOT/'04_Assembly'/'R07_Exploded_Reference.step'))
 cq.exporters.export(cq.Compound.makeCompound(exsolids),str(ROOT/'04_Assembly'/'R07_Exploded_Reference.stl'),tolerance=.15,angularTolerance=.15)
 meta={name:{k:v for k,v in p.items()if k!='shape'}for name,p in parts.items()}
 (ROOT/'Verification'/'parts.json').write_text(json.dumps(meta,indent=2))
 (ROOT/'Verification'/'profiles.json').write_text(json.dumps(profiles,indent=2))
 inputs=[ROOT/'Source/build_cad.py',ROOT/'Software/geometry.py',ROOT/'Software/configuration.json']
 (ROOT/'Verification/Build_Fingerprint.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs},indent=2))
 print('Exported',len(parts),'unique CAD parts and five assemblies')
