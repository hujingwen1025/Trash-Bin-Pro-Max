"""R04 hybrid bin. Run with Python 3.11 and the packages listed in README.md."""
from pathlib import Path
import json, math, itertools, subprocess, shutil, hashlib, os
import numpy as np
import cadquery as cq
import trimesh
import ezdxf
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = Path(os.environ.get('BIN_BUILD_DIR',str(ROOT/'.build')))
INTERNAL.mkdir(exist_ok=True)
P = json.loads((ROOT/'Source/parameters.json').read_text())
TW, TF = P['sheet_wall'], P['sheet_floor']
CW, CP = P['wood_joint_gap'], P['printed_joint_gap']
LOW, HIGH, H, R, SEAM = 2.5, 350., 450., 75., P['curve_split_station']
BANDS = [(z-P['vertical_finger_height']/2,z+P['vertical_finger_height']/2) for z in P['joint_centers_z']]
COMP = list(zip([TF]+[b for a,b in BANDS],[a for a,b in BANDS]+[H]))
SHAPES, PROFILES, META, PLANES = {}, {}, {}, {}
POLYGONS = {}
FIT_REPORT = {'parameters':P, 'tests':[], 'physical_tests_performed':False}


def test(name, passed, **data):
    FIT_REPORT['tests'].append({'name':name,'pass':bool(passed),**data})
    print(('PASS ' if passed else 'FAIL ')+name, flush=True)


def cuboid(x1,y1,z1,x2,y2,z2):
    return cq.Solid.makeBox(x2-x1,y2-y1,z2-z1,cq.Vector(x1,y1,z1))


def cyl(radius,height,base,axis=(0,0,1)):
    return cq.Solid.makeCylinder(radius,height,cq.Vector(*base),cq.Vector(*axis))


def prism(poly,plane,depth):
    assert poly.geom_type == 'Polygon', poly.geom_type
    wp=cq.Workplane(plane).polyline(list(poly.exterior.coords)[:-1]).close()
    for ring in poly.interiors:
        wp=wp.polyline(list(ring.coords)[:-1]).close()
    return wp.extrude(depth).val()


def add(name,shape,kind,description,qty=1,plane=None):
    shape=shape.clean()
    SHAPES[name]=shape
    bb=shape.BoundingBox()
    META[name]={'kind':kind,'description':description,'quantity_per_bin':qty,
                'bounds':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],
                'volume_mm3':shape.Volume()}
    if plane: PLANES[name]=plane
    return shape


def floor_centers(a,b,n):
    margin=28
    return np.linspace(a+margin+15,b-margin-15,n).tolist()


def notch_edge(poly,u,side,owner,gap):
    """The male occupies the corner during BANDS, the mate during COMP."""
    span=(u-.01,u+TW+gap/2) if side=='start' else (u-TW-gap/2,u+.01)
    if owner:
        poly=poly.difference(box(span[0],TF-.01,span[1],H+.01))
        for a,b in BANDS:
            poly=poly.union(box(span[0]+(.01 if side=='start' else 0),a+gap/4,
                                span[1]-(0 if side=='start' else .01),b-gap/4))
    else:
        for a,b in BANDS:
            poly=poly.difference(box(span[0],a-gap/4,span[1],b+gap/4))
    return poly


WALL_INFO = {
 'W01_rear':('X',LOW,HIGH,HIGH, [('start',True),('end',True)],4),
 'W02_right':('Y',LOW,HIGH,HIGH-TW,[('start',True),('end',False)],4),
 'W03_front':('X',SEAM,HIGH,LOW+TW,[('end',False)],3),
 'W04_left':('Y',SEAM,HIGH,LOW,[('end',False)],3),
}
FLOOR_NOTCHES=[]
for name,(axis,a,b,offset,corners,nf) in WALL_INFO.items():
    poly=box(a,TF,b,H)
    for side,owner in corners:
        poly=notch_edge(poly,a if side=='start' else b,side,owner,CW)
    if a==SEAM:
        for start,end in BANDS:
            poly=poly.difference(box(SEAM-.01,start-CP/4,SEAM+TW+CP/2,end+CP/4))
        for start,end in COMP:
            if end-start>CP:
                poly=poly.union(box(SEAM-TW,start+CP/4,SEAM+.01,end-CP/4))
    centers=floor_centers(a,b,nf)
    for u in centers:
        poly=poly.union(box(u-15,0,u+15,TF+.01))
        if axis=='X':
            y1,y2=(HIGH-TW,HIGH) if name=='W01_rear' else (LOW,LOW+TW)
            FLOOR_NOTCHES.append((u-15-CW/2,y1-CW,u+15+CW/2,y2+CW))
        else:
            x1,x2=(HIGH-TW,HIGH) if name=='W02_right' else (LOW,LOW+TW)
            FLOOR_NOTCHES.append((x1-CW,u-15-CW/2,x2+CW,u+15+CW/2))
    # Laser holes are through cuts. Countersinks are a separate drill operation.
    plane=cq.Plane(origin=(0,offset,0),xDir=(1,0,0),normal=(0,-1,0)) if axis=='X' else cq.Plane(origin=(offset,0,0),xDir=(0,1,0),normal=(1,0,0))
    shape=prism(poly,plane,TW)
    if a==SEAM:
        for z in [81,225,369]:
            base=(120.5,LOW-.1,z) if axis=='X' else (LOW-.1,120.5,z)
            direction=(0,1,0) if axis=='X' else (1,0,0)
            shape=shape.cut(cyl(1.7,TW+.2,base,direction))
            cone_base=(120.5,LOW,z) if axis=='X' else (LOW,120.5,z)
            shape=shape.cut(cq.Solid.makeCone(3.15,1.7,1.45,cq.Vector(*cone_base),cq.Vector(*direction)))
    PROFILES[name]=poly
    POLYGONS[name]=poly.wkt
    add(name,shape,'plywood_wall',f'{TW:g} mm plywood wall, {nf} floor fingers',plane=plane)
    META[name]['floor_finger_centers']=centers
    test(name+' planar profile',poly.is_valid and poly.geom_type=='Polygon')

# An exact analytic circular cutout matches the faceted R75 source envelope.
v=math.sqrt(R*R-LOW*LOW)
floor=(cq.Workplane('XY').moveTo(LOW,v).lineTo(LOW,HIGH).lineTo(HIGH,HIGH)
       .lineTo(HIGH,LOW).lineTo(v,LOW).threePointArc((R/math.sqrt(2),R/math.sqrt(2)),(LOW,v))
       .close().extrude(TF).val())
for x1,y1,x2,y2 in FLOOR_NOTCHES:
    floor=floor.cut(cuboid(x1,y1,-.01,x2,y2,TF+.01))

# Curved corner plus straight wings, all within the original outside perimeter.
outer=box(LOW,LOW,SEAM,SEAM)
base_curve=(cq.Workplane('XY').box(SEAM-LOW,SEAM-LOW,H-TF,centered=(False,False,False))
            .translate((LOW,LOW,TF)).val().cut(cyl(R,H+2,(0,0,0))))
inner_box=cuboid(LOW+TW,LOW+TW,TF-1,SEAM+1,SEAM+1,H+1)
inner_box=inner_box.cut(cyl(R+TW,H+4,(0,0,TF-2)))
curve=base_curve.cut(inner_box)
for axis in ['X','Y']:
    for start,end in BANDS:
        ext=(SEAM,LOW,start+CP/4,SEAM+TW,LOW+TW,end-CP/4) if axis=='X' else (LOW,SEAM,start+CP/4,LOW+TW,SEAM+TW,end-CP/4)
        curve=curve.fuse(cuboid(*ext))
    for start,end in COMP:
        cut=(SEAM-TW-CP/2,LOW-.01,start-CP/4,SEAM+.1,LOW+TW+.01,end+CP/4) if axis=='X' else (LOW-.01,SEAM-TW-CP/2,start-CP/4,LOW+TW+.01,SEAM+.1,end+CP/4)
        curve=curve.cut(cuboid(*cut))

# Three coarse curved floor tabs, each 16 mm arc width at radius 78.
for deg in [22.5,45,67.5]:
    dtheta=16/(R+TW/2)
    angles=np.linspace(math.radians(deg)-dtheta/2, math.radians(deg)+dtheta/2,13)
    tab=Polygon([(R*math.cos(t),R*math.sin(t)) for t in angles]+
                [((R+TW)*math.cos(t),(R+TW)*math.sin(t)) for t in angles[::-1]])
    curve=curve.fuse(prism(tab,cq.Plane.XY(),TF+.02).translate((0,0,0)))
    # The floor notch reaches the exact outside edge; no enclosed hairline sliver.
    grown=tab.buffer(CP/2,join_style='mitre')
    floor=floor.cut(prism(grown,cq.Plane.XY(),TF+.1).translate((0,0,-.05)))

# Integral interior fixing flanges, away from the R75 outside face.
curve=curve.fuse(cuboid(81,LOW+TW,TF,132.5,LOW+TW+5,H))
curve=curve.fuse(cuboid(LOW+TW,81,TF,LOW+TW+5,132.5,H))
# Flanges touch the wings along the inner faces. Give each a 1 mm inward root overlap.
# The flanges share a face with the surviving wing roots and leave every finger notch clear.
# M3 nut cavities are cut from the inside; through holes use the same centers as wood.
for z in [81,225,369]:
    for axis in ['Y','X']:
        if axis=='Y':
            curve=curve.cut(cyl(1.7,9,(120.5,LOW+TW-1,z),(0,1,0)))
            plane=cq.Plane(origin=(120.5,LOW+TW+5,z),xDir=(1,0,0),normal=(0,-1,0))
        else:
            curve=curve.cut(cyl(1.7,9,(LOW+TW-1,120.5,z),(1,0,0)))
            plane=cq.Plane(origin=(LOW+TW+5,120.5,z),xDir=(0,1,0),normal=(-1,0,0))
        hexcut=cq.Workplane(plane).polygon(6,5.8/math.cos(math.pi/6)).extrude(2.6).val()
        curve=curve.cut(hexcut)
# Three bolted floor pads support the curve/floor seam at the 10 kg design target.
for deg in [22.5,45,67.5]:
    a=math.radians(deg)
    ux,uy=math.cos(a),math.sin(a)
    tx,ty=-uy,ux
    neck=Polygon([(r*ux+d*tx,r*uy+d*ty) for r,d in [(80,-7),(100,-7),(100,7),(80,7)]])
    boss=prism(neck,cq.Plane.XY(),8).translate((0,0,TF)).fuse(cyl(10,8,(100*ux,100*uy,TF)))
    curve=curve.fuse(boss)
    curve=curve.cut(cyl(2.25,8.2,(100*ux,100*uy,TF-.1)))
    nut=cq.Workplane('XY',origin=(100*ux,100*uy,TF+8)).polygon(6,7.2/math.cos(math.pi/6)).extrude(-3.4).val()
    curve=curve.cut(nut)
    floor=floor.cut(cyl(2.25,TF+.2,(100*ux,100*uy,-.1)))
    floor=floor.cut(cq.Solid.makeCone(4.,2.25,1.75,cq.Vector(100*ux,100*uy,0),cq.Vector(0,0,1)))
add('C01_curved_corner',curve,'printed','PETG, R75 outside / R81 inside; six fingers per wing and three M4 floor pads')

# Four identical Ø29.2 inserts keep the original Ø25.2 x 5 underside pockets.
insert_r=P['magnet_insert_diameter']/2
hole_r=insert_r+P['magnet_insert_radial_gap']
for x,y in itertools.product([102.5,250.], repeat=2):
    floor=floor.cut(cyl(hole_r,TF+.2,(x,y,-.1)))
add('F01_floor',floor,'plywood_floor',f'{TF:g} mm plywood, four insert holes',plane=cq.Plane.XY())
insert=cyl(insert_r,TF,(0,0,0)).cut(cyl(12.6,5.001,(0,0,-.001)))
add('M01_magnet_insert',insert,'printed','PETG; pocket Ø25.2 x 5 underside',4)


def project_face(name):
    shape=SHAPES[name]
    plane=PLANES[name]
    normal=plane.zDir
    faces=[f for f in shape.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().dot(normal))>.99999]
    face=max(faces,key=lambda f:f.Area())
    wires=[]
    for wire in [face.outerWire()]+face.innerWires():
        entities=[]
        for e in wire.Edges():
            def xy(point):
                v=plane.toLocalCoords(point)
                return (float(v.x),float(v.y))
            if e.geomType()=='LINE':
                entities.append({'type':'LINE','start':xy(e.startPoint()),'end':xy(e.endPoint())})
            elif e.geomType()=='CIRCLE':
                center=xy(e.arcCenter()); radius=e.radius()
                if abs(e.Length()-2*math.pi*radius)<1e-4:
                    entities.append({'type':'CIRCLE','center':center,'radius':radius})
                else:
                    start,end,mid=xy(e.startPoint()),xy(e.endPoint()),xy(e.positionAt(.5))
                    a,b,m=[math.degrees(math.atan2(q[1]-center[1],q[0]-center[0]))%360 for q in [start,end,mid]]
                    if (m-a)%360>(b-a)%360: a,b=b,a
                    entities.append({'type':'ARC','center':center,'radius':radius,'start_angle':a,'end_angle':b})
            else:
                points=[xy(e.positionAt(t)) for t in np.linspace(0,1,12)]
                entities.extend({'type':'LINE','start':a,'end':b} for a,b in zip(points,points[1:]))
        wires.append(entities)
    return wires


def write_dxf(name,wires):
    doc=ezdxf.new('R2000')
    doc.units=4
    doc.header['$MEASUREMENT']=1
    doc.layers.new('CUT',dxfattribs={'color':1})
    msp=doc.modelspace()
    for wire in wires:
        for e in wire:
            attr={'layer':'CUT'}
            if e['type']=='LINE':msp.add_line(e['start'],e['end'],dxfattribs=attr)
            elif e['type']=='CIRCLE':msp.add_circle(e['center'],e['radius'],dxfattribs=attr)
            else:msp.add_arc(e['center'],e['radius'],e['start_angle'],e['end_angle'],dxfattribs=attr)
    doc.saveas(INTERNAL/(name+'.dxf'))


# Export CAD solids and independent component meshes from the same BREP shapes.
assembly=cq.Assembly(name='HybridBin_R04_10kg_target')
mesh_parts=[]
for name,shape in SHAPES.items():
    test(name+' valid single solid',shape.isValid() and len(shape.Solids())==1)
    cq.exporters.export(shape,str(ROOT/'STEP'/f'{name}.step'))
    cq.exporters.export(shape,str(ROOT/'STL'/f'{name}.stl'),tolerance=.035,angularTolerance=.08)
    mesh=trimesh.load(ROOT/'STL'/f'{name}.stl',force='mesh')
    test(name+' watertight mesh',mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0)
    if name=='M01_magnet_insert':
        for i,(x,y) in enumerate(itertools.product([102.5,250.],repeat=2)):
            moved=shape.translate((x,y,0))
            assembly.add(moved,name=f'M01_insert_{i+1}')
            mm=mesh.copy();mm.apply_translation([x,y,0]);mesh_parts.append(mm)
    else:
        assembly.add(shape,name=name)
        mesh_parts.append(mesh)
    if name in PLANES:
        wires=project_face(name)
        PROFILES[name]=wires
        write_dxf(name,wires)
    print('Exported '+name,flush=True)
assembly.export(str(ROOT/'STEP/Assembly_R04.step'))
# Fuse only the touching structural surfaces for a watertight viewing STL.
# The assembly STEP retains every individual component.
frame=SHAPES['F01_floor']
for name,part in SHAPES.items():
    if name not in ['F01_floor','M01_magnet_insert']:
        frame=frame.fuse(part).clean()
view_shapes=[frame]+[SHAPES['M01_magnet_insert'].translate((x,y,0))for x,y in itertools.product([102.5,250.],repeat=2)]
cq.exporters.export(cq.Compound.makeCompound(view_shapes),str(ROOT/'STL/Assembly_R04.stl'),tolerance=.035,angularTolerance=.08)
view_mesh=trimesh.load(ROOT/'STL/Assembly_R04.stl',force='mesh')
test('Assembly viewing STL watertight',view_mesh.is_watertight and view_mesh.is_winding_consistent)

# Geometric tests and export fidelity.
for name,shape in SHAPES.items():
    reimport=cq.importers.importStep(str(ROOT/'STEP'/f'{name}.step')).val()
    rel=abs(reimport.Volume()-shape.Volume())/shape.Volume()
    test(name+' STEP round-trip',reimport.isValid() and rel<1e-7,relative_volume_error=rel)

names=[n for n in SHAPES if n!='M01_magnet_insert']
for a,b in itertools.combinations(names,2):
    volume=SHAPES[a].intersect(SHAPES[b]).Volume()
    test(a+' / '+b+' interference',volume<.01,overlap_mm3=volume)
for x,y in itertools.product([102.5,250.],repeat=2):
    cup=SHAPES['M01_magnet_insert'].translate((x,y,0))
    volume=cup.intersect(SHAPES['F01_floor']).Volume()
    test(f'Insert ({x},{y}) clearance',volume<.01,radial_gap_mm=P['magnet_insert_radial_gap'],overlap_mm3=volume)

from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
exact_box=Bnd_Box()
BRepBndLib.AddOptimal_s(cq.Compound.makeCompound([SHAPES[n] for n in names]).wrapped,exact_box,False,False)
limits=exact_box.Get()
allbb=type('Bounds',(),dict(xlen=limits[3]-limits[0],ylen=limits[4]-limits[1],zlen=limits[5]-limits[2]))()
test('Original exterior envelope retained',abs(allbb.xlen-347.5)<.01 and abs(allbb.ylen-347.5)<.01 and abs(allbb.zlen-450)<.01,
     exterior_mm=[allbb.xlen,allbb.ylen,allbb.zlen])

# Conservative beam-strip screen for floor carrying a uniform payload.
# Model full width as one simply supported beam. This is a screen, not a load rating.
span=335.5; width=335.5; E=3000.; I=width*TF**3/12
screens=[]
for kg in [P['working_load_kg'],P['proof_load_kg']]:
    force=kg*9.81
    q=force/span
    delta=5*q*span**4/(384*E*I)
    stress=(q*span**2/8)*(TF/2)/I
    screens.append({'payload_kg':kg,'deflection_mm':delta,'bending_stress_MPa':stress,'E_assumption_MPa':E})
FIT_REPORT['floor_screen']=screens
FIT_REPORT['load_status']='10 kg target, pending physical validation; no certified load rating'
FIT_REPORT['source_reference']={'envelope':[347.5,347.5,450.], 'wall':6.,'floor':9.,'curve_radii':[75.,81.],
    'magnet_pockets':{'diameter':25.2,'depth':5.,'centers':list(itertools.product([102.5,250.],repeat=2))}}

(ROOT/'Source/model_metadata.json').write_text(json.dumps(META,indent=2))
(INTERNAL/'wall_polygons.json').write_text(json.dumps(POLYGONS,indent=2))
(INTERNAL/'profiles.json').write_text(json.dumps(PROFILES,indent=2))
(INTERNAL/'initial_tests.json').write_text(json.dumps(FIT_REPORT,indent=2))
failed=[t['name'] for t in FIT_REPORT['tests'] if not t['pass']]
print('FAILED TESTS',failed,flush=True)
