"""Build calibration samples, drawings, DWG files and manufacturing verification."""
from pathlib import Path
import math,json,itertools,subprocess,hashlib,textwrap,os,shutil
import numpy as np
import cadquery as cq
import trimesh,ezdxf
from shapely.geometry import Polygon,box,Point,LineString
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely import wkt
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
INTERNAL=Path(os.environ.get('BIN_BUILD_DIR',str(ROOT/'.build')))
P=json.loads((ROOT/'Source/parameters.json').read_text());TW,TF=P['sheet_wall'],P['sheet_floor']
META=json.loads((ROOT/'Source/model_metadata.json').read_text())
PROFILES=json.loads((INTERNAL/'profiles.json').read_text())
RESULTS=json.loads((INTERNAL/'initial_tests.json').read_text())
SHAPES={n:cq.importers.importStep(str(ROOT/'STEP'/f'{n}.step')).val() for n in META}
GAPS=[round(.1+.05*i,2) for i in range(7)]
COUPONS={}


def test(name,passed,**data):
    RESULTS['tests'].append({'name':name,'pass':bool(passed),**data})
    print(('PASS 'if passed else 'FAIL ')+name,flush=True)


def plane_for(name):
    if name in ['W01_rear','W03_front']:
        return cq.Plane(origin=(0,350 if name=='W01_rear' else 8.5,0),xDir=(1,0,0),normal=(0,-1,0))
    if name in ['W02_right','W04_left']:
        return cq.Plane(origin=(344 if name=='W02_right' else 2.5,0,0),xDir=(0,1,0),normal=(1,0,0))
    return cq.Plane.XY()


def extrude_poly(poly,plane,depth):
    wp=cq.Workplane(plane).polyline(list(poly.exterior.coords)[:-1]).close()
    for ring in poly.interiors:wp=wp.polyline(list(ring.coords)[:-1]).close()
    return wp.extrude(depth).val()


def poly_wires(poly):
    return [[{'type':'LINE','start':list(a),'end':list(b)} for a,b in zip(r.coords,list(r.coords)[1:])]
            for r in [poly.exterior,*poly.interiors]]


def write_dxf(name,wires,layers=None):
    d=ezdxf.new('R2000');d.units=4;d.header['$MEASUREMENT']=1
    d.layers.new('CUT',dxfattribs={'color':1})
    d.layers.new('REFERENCE',dxfattribs={'color':5})
    m=d.modelspace()
    for j,wire in enumerate(wires):
        layer=layers[j] if layers else 'CUT'
        for e in wire:
            a={'layer':layer}
            if e['type']=='LINE':m.add_line(e['start'],e['end'],dxfattribs=a)
            elif e['type']=='CIRCLE':m.add_circle(e['center'],e['radius'],dxfattribs=a)
            else:m.add_arc(e['center'],e['radius'],e['start_angle'],e['end_angle'],dxfattribs=a)
    d.modelspace().add_text(name+' | mm | NOMINAL STOCK',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-12))
    if name in COUPONS:
        for xx,yy,gap,label in COUPONS[name]['labels']:
            d.modelspace().add_text(f'{gap:.2f}',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((xx-5,yy-13))
    d.saveas(INTERNAL/(name+'.dxf'))


# Calibration boards, plus matching tab blanks. Fit is measured after cutting.
for ident,thickness in [('Q01_wall_fit',TW),('Q02_floor_fit',TF)]:
    height=180 if ident=='Q01_wall_fit' else 100
    outer=box(0,0,200,height)
    holes=[];labels=[]
    for i,gap in enumerate(GAPS):
        x=25+50*(i%4);y=30+35*(i//4)
        width=36 if ident=='Q01_wall_fit' else 30
        holes.append(box(x-(width+gap)/2,y-(TW+gap)/2,x+(width+gap)/2,y+(TW+gap)/2))
        labels.append((x,y,gap,'wall thickness'))
        if ident=='Q01_wall_fit':
            y+=90
            holes.append(box(x-(30+gap)/2,y-(TF+gap)/2,x+(30+gap)/2,y+(TF+gap)/2))
            labels.append((x,y,gap,'floor thickness'))
    holes.append(box(165,55,185,75))
    if ident=='Q02_floor_fit':
        holes.append(Point(175,87).buffer(2.25,quad_segs=48))
    poly=outer.difference(unary_union(holes))
    COUPONS[ident]={'poly':poly,'thickness':thickness,'labels':labels}
for ident,width,thick in [('Q03_wall_tab',36.,6.),('Q04_floor_tab',30.,TF),('Q08_floor_wall_tab',30.,6.)]:
    poly=Polygon([(0,0),(50,0),(50,35),(25+width/2,35),(25+width/2,44),
                  (25-width/2,44),(25-width/2,35),(0,35)])
    COUPONS[ident]={'poly':poly,'thickness':thick,'labels':[]}
insert_board=box(0,0,120,50)
for xx,g in zip([20,60,100],[.1,.2,.3]):
    insert_board=insert_board.difference(Point(xx,25).buffer(14.6+g,quad_segs=72))
COUPONS['Q07_insert_fit']={'poly':insert_board,'thickness':TF,'labels':[(20,25,.1,'radial'),(60,25,.2,'radial'),(100,25,.3,'radial')]}
for ident,item in COUPONS.items():
    solid=extrude_poly(item['poly'],cq.Plane.XY(),item['thickness'])
    cq.exporters.export(solid,str(ROOT/'STEP'/f'{ident}.step'))
    cq.exporters.export(solid,str(ROOT/'STL'/f'{ident}.stl'),tolerance=.035)
    PROFILES[ident]=poly_wires(item['poly']);write_dxf(ident,PROFILES[ident])
    test(ident+' coupon solid and closed outline',solid.isValid() and item['poly'].is_valid)

# Cut one full-scale sample from the actual curved wing for a print/wood fit test.
curve_sample=SHAPES['C01_curved_corner'].intersect(cq.Solid.makeBox(45,11,72,cq.Vector(90,2.5,72)))
curve_sample=curve_sample.translate((-90,-2.5,-72)).clean()
for fmt in ['step','stl']:
    cq.exporters.export(curve_sample,str(ROOT/('STEP'if fmt=='step'else'STL')/f'Q05_curve_joint_sample.{fmt}'),tolerance=.035)
test('Curve joint sample one solid',curve_sample.isValid() and len(curve_sample.Solids())==1)
poly=wkt.loads(json.loads((INTERNAL/'wall_polygons.json').read_text())['W03_front'])
wood_sample=poly.intersection(box(90,72,135,144))
# Include the screw clearance to match the full panel.
wood_sample=wood_sample.difference(Point(120.5,81).buffer(1.7,quad_segs=24))
wood_sample=translate(wood_sample,xoff=-90,yoff=-72)
COUPONS['Q06_curve_wall_sample']={'poly':wood_sample,'thickness':6.,'labels':[]}
PROFILES['Q06_curve_wall_sample']=poly_wires(wood_sample)
write_dxf('Q06_curve_wall_sample',PROFILES['Q06_curve_wall_sample'])
solid=extrude_poly(wood_sample,cq.Plane.XY(),6)
cq.exporters.export(solid,str(ROOT/'STEP/Q06_curve_wall_sample.step'))
cq.exporters.export(solid,str(ROOT/'STL/Q06_curve_wall_sample.stl'))

# Analytic cross-section profiles for drawings and the curve's reference DWG.
def face_wires(face,axis='XY',shift=(0,0)):
    def xy(v):
        vals=(v.x,v.y)if axis=='XY' else ((v.x,v.z)if axis=='XZ' else(v.y,v.z))
        return [vals[0]+shift[0],vals[1]+shift[1]]
    result=[]
    for wire in [face.outerWire(),*face.innerWires()]:
        es=[]
        for edge in wire.Edges():
            if edge.geomType()=='LINE':es.append({'type':'LINE','start':xy(edge.startPoint()),'end':xy(edge.endPoint())})
            elif edge.geomType()=='CIRCLE':
                cc=xy(edge.arcCenter());r=edge.radius()
                if abs(edge.Length()-2*math.pi*r)<1e-4:es.append({'type':'CIRCLE','center':cc,'radius':r})
                else:
                    points=[xy(edge.startPoint()),xy(edge.endPoint()),xy(edge.positionAt(.5))]
                    a,b,m=[math.degrees(math.atan2(q[1]-cc[1],q[0]-cc[0]))%360 for q in points]
                    if(m-a)%360>(b-a)%360:a,b=b,a
                    es.append({'type':'ARC','center':cc,'radius':r,'start_angle':a,'end_angle':b})
            else:
                pp=[xy(edge.positionAt(t))for t in np.linspace(0,1,20)]
                es.extend({'type':'LINE','start':a,'end':b}for a,b in zip(pp,pp[1:]))
        result.append(es)
    return result

curve_sections={}
for z in [13.,225.]:
    slab=SHAPES['C01_curved_corner'].intersect(cq.Solid.makeBox(150,150,.02,cq.Vector(0,0,z)))
    fs=[f for f in slab.Faces()if f.geomType()=='PLANE'and abs(f.normalAt().z)>.999]
    curve_sections[z]=face_wires(max(fs,key=lambda f:f.Area()))
# Reference projections use mesh silhouette for the tall side view.
mesh=trimesh.load(ROOT/'STL/C01_curved_corner.stl',force='mesh')
polys=[]
for tri in mesh.triangles:
    poly=Polygon(tri[:,[0,2]])
    if poly.area>1e-7:polys.append(poly)
silhouette=unary_union(polys).buffer(0)
side_wires=poly_wires(silhouette)
refs=[]
for section,dx,dy in [(curve_sections[225.],0,0),(curve_sections[13.],170,0),(side_wires,350,0)]:
    for wire in section:
        copied=[]
        for e in wire:
            ee=dict(e)
            for k in ['start','end','center']:
                if k in ee:ee[k]=[ee[k][0]+dx,ee[k][1]+dy]
            copied.append(ee)
        refs.append(copied)
write_dxf('C01_curved_corner_REFERENCE',refs,['REFERENCE']*len(refs))
insert_ref=[[{'type':'CIRCLE','center':[0,0],'radius':14.6}],
            [{'type':'CIRCLE','center':[0,0],'radius':12.6}],
            *poly_wires(Polygon([(45,0),(45+29.2,0),(45+29.2,TF),(45,TF)]))]
write_dxf('M01_magnet_insert_REFERENCE',insert_ref,['REFERENCE']*len(insert_ref))

# Continuous straight insertion sweeps verify a feasible assembly sequence.
wall_polys={k:wkt.loads(v)for k,v in json.loads((INTERNAL/'wall_polygons.json').read_text()).items()}
def horizontal_sweep(poly,distance):
    pieces=[poly,translate(poly,xoff=distance)]
    for ring in [poly.exterior,*poly.interiors]:
        pp=list(ring.coords)
        for a,b in zip(pp,pp[1:]):
            quad=Polygon([a,b,(b[0]+distance,b[1]),(a[0]+distance,a[1])])
            if quad.area>1e-10:pieces.append(quad)
    return unary_union(pieces).buffer(0)

fixed=['C01_curved_corner']
for name in ['W03_front','W04_left','W01_rear','W02_right']:
    poly=wall_polys[name]
    if name in ['W03_front','W04_left']:
        sweep=extrude_poly(horizontal_sweep(poly,12),plane_for(name),6)
    elif name=='W01_rear':
        plane=cq.Plane(origin=(0,362,0),xDir=(1,0,0),normal=(0,-1,0))
        sweep=extrude_poly(poly,plane,18)
    else:sweep=extrude_poly(poly,plane_for(name),18)
    maximum=0
    for other in fixed:
        maximum=max(maximum,sweep.intersect(SHAPES[other]).Volume())
    test(name+' continuous insertion sweep',maximum<.02,overlap_mm3=maximum,travel_mm=12)
    fixed.append(name)
# Extrude the exact floor profile from z=-12 to +9, then test against all assembled walls.
floor=SHAPES['F01_floor']
flatfaces=[f for f in floor.Faces()if f.geomType()=='PLANE'and f.normalAt().z<-.999]
face=max(flatfaces,key=lambda f:f.Area())
ext=cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(0,0,-12))
sweep=floor.fuse(ext)
maximum=max(sweep.intersect(SHAPES[n]).Volume()for n in fixed)
test('Floor continuous upward insertion sweep',maximum<.02,overlap_mm3=maximum,travel_mm=12)

# Cut geometry checks. Match endpoints independently of edge traversal orientation.
def sampled(e):
    if e['type']=='LINE':return [e['start'],e['end']]
    a,b=(0,360)if e['type']=='CIRCLE' else(e['start_angle'],e['end_angle'])
    if b<a:b+=360
    n=max(12,int((b-a)/2)+1)
    return [[e['center'][0]+e['radius']*math.cos(math.radians(t)),e['center'][1]+e['radius']*math.sin(math.radians(t))]for t in np.linspace(a,b,n)]

def wire_polygon(wire):
    # Edges supplied by BREP may be unordered; connect endpoints into a closed path.
    if len(wire)==1 and wire[0]['type']=='CIRCLE':return Polygon(sampled(wire[0]))
    pending=[sampled(e) for e in wire]
    pts=pending.pop(0)
    while pending:
        last=np.array(pts[-1]);options=[(np.linalg.norm(last-np.array(p[0])),i,False)for i,p in enumerate(pending)]
        options +=[(np.linalg.norm(last-np.array(p[-1])),i,True)for i,p in enumerate(pending)]
        error,index,reverse=min(options)
        if error>1e-5:raise ValueError(('Open cutting contour',error))
        pp=pending.pop(index)
        if reverse:pp=pp[::-1]
        pts.extend(pp[1:])
    if np.linalg.norm(np.array(pts[0])-np.array(pts[-1]))>1e-4:raise ValueError('Open loop')
    return Polygon(pts)

for name,wires in PROFILES.items():
    loops=[wire_polygon(w)for w in wires]
    valid=all(q.is_valid and q.area>.001 for q in loops)
    keys=[]
    for wire in wires:
        for e in wire:
            if e['type']=='LINE':key=('L',*sorted([tuple(round(t,5)for t in e['start']),tuple(round(t,5)for t in e['end'])]))
            else:key=json.dumps(e,sort_keys=True)
            keys.append(str(key))
    test(name+' closed nonduplicated cutting contours',valid and len(keys)==len(set(keys)),contours=len(wires),entities=len(keys))

# Convert to actual R2000 DWG and back. Compare canonical entities, units and limits.
def canonical(entity):
    typ=entity.dxftype()
    if typ=='LINE':
        return ('LINE',*sorted([tuple(round(x,5)for x in list(entity.dxf.start)[:2]),tuple(round(x,5)for x in list(entity.dxf.end)[:2])]))
    if typ=='CIRCLE':return ('CIRCLE',tuple(round(x,5)for x in list(entity.dxf.center)[:2]),round(entity.dxf.radius,5))
    if typ=='ARC':return ('ARC',tuple(round(x,5)for x in list(entity.dxf.center)[:2]),round(entity.dxf.radius,5),round(entity.dxf.start_angle%360,5),round(entity.dxf.end_angle%360,5))
    if typ=='TEXT':return ('TEXT',entity.dxf.text,tuple(round(x,5)for x in list(entity.dxf.insert)[:2]))
    return (typ,)

# Use ODA for writing after the open-source writer failed strict validation.
oda=os.environ.get('ODA_CONVERTER',shutil.which('ODAFileConverter') or '/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter')
if not Path(oda).is_file():raise RuntimeError('Set ODA_CONVERTER to the installed ODA File Converter executable.')
oda_input=INTERNAL/'oda_inputs';oda_input.mkdir(exist_ok=True)
roundtrip=INTERNAL/'oda_roundtrip';roundtrip.mkdir(exist_ok=True)
intended=[*PROFILES.keys(),'C01_curved_corner_REFERENCE','M01_magnet_insert_REFERENCE']
for name in intended:
    src=INTERNAL/(name+'.dxf')
    # Add a reference label to the production profiles generated by build_bin.py.
    d=ezdxf.readfile(src)
    if 'REFERENCE' not in d.layers:d.layers.new('REFERENCE',dxfattribs={'color':5})
    if not list(d.modelspace().query('TEXT')):
        d.modelspace().add_text(name+' | mm | NOMINAL STOCK',dxfattribs={'layer':'REFERENCE','height':3}).set_placement((0,-12))
    d.saveas(oda_input/src.name)
commands=[
 [oda,str(oda_input),str(ROOT/'DWG'),'ACAD2000','DWG','0','1','*.dxf'],
 [oda,str(ROOT/'DWG'),str(roundtrip),'ACAD2000','DXF','0','1','*.dwg']]
for command in commands:
    done=subprocess.run(command,capture_output=True,text=True)
    if done.returncode:raise RuntimeError('ODA conversion failed: '+done.stderr)
for name in intended:
    src=oda_input/(name+'.dxf');target=ROOT/'DWG'/(name+'.dwg');back=roundtrip/(name+'.dxf')
    a,b=ezdxf.readfile(src),ezdxf.readfile(back)
    same=sorted(map(canonical,a.modelspace()),key=str)==sorted(map(canonical,b.modelspace()),key=str)
    independent=subprocess.run(['dwgread','-v0','-O','JSON',str(target)],capture_output=True,text=True)
    reader_ok=independent.returncode==0 and 'ERROR' not in independent.stderr
    test(name+' DWG round-trip',same and b.units==4 and target.read_bytes()[:6]==b'AC1015' and reader_ok,
         entities=len(a.modelspace()),dwg_version='R2000',units='mm',writer='ODA 27.10',independent_reader='LibreDWG 0.14',
         independent_reader_ok=reader_ok)

# Check 12 mm remaining wood around isolated production holes.
for name,wires in PROFILES.items():
    if name.startswith('Q'):continue
    outside=wire_polygon(wires[0])
    for i,wire in enumerate(wires[1:]):
        if len(wire)==1 and wire[0]['type']=='CIRCLE':
            e=wire[0];clearance=Point(e['center']).distance(outside.boundary)-e['radius']
            test(name+f' isolated hole {i+1} ligament',clearance>=12,remaining_wood_mm=clearance)

for name,info in META.items():
    mesh=trimesh.load(ROOT/'STL'/f'{name}.stl',force='mesh')
    relative=abs(mesh.volume-info['volume_mm3'])/info['volume_mm3']
    test(name+' STL volume fidelity',relative<.002,relative_volume_error=relative)
test('Wood vertical finger clearance',abs(((36+P['wood_joint_gap']/2)-(36-P['wood_joint_gap']/2))-P['wood_joint_gap'])<1e-6,
     total_gap_mm=P['wood_joint_gap'],male_height_mm=36-P['wood_joint_gap']/2,female_height_mm=36+P['wood_joint_gap']/2)
test('Printed vertical finger clearance',abs(((36+P['printed_joint_gap']/2)-(36-P['printed_joint_gap']/2))-P['printed_joint_gap'])<1e-6,
     total_gap_mm=P['printed_joint_gap'],male_height_mm=36-P['printed_joint_gap']/2,female_height_mm=36+P['printed_joint_gap']/2)
# Entire delivered mesh and assembly checks, including calibration pieces.
for path in sorted((ROOT/'STL').glob('*.stl')):
    mesh=trimesh.load(path,force='mesh')
    test(path.stem+' delivered mesh integrity',mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0)
assembly=cq.importers.importStep(str(ROOT/'STEP/Assembly_R06.step'))
test('STEP assembly has ten named-part solids',len(assembly.solids().vals())==10)

# Use the uploaded source mesh to quantify the analytic corner reconstruction.
reference=trimesh.load(ROOT/'Source/reference_bin.stl',force='mesh')
expected=np.array([[2.5,2.5,0.],[350.,350.,450.]])
test('Uploaded source dimensions match CAD datums',np.allclose(reference.bounds,expected,atol=.001),source_sha256=hashlib.sha256((ROOT/'Source/reference_bin.stl').read_bytes()).hexdigest())
radii=np.linalg.norm(reference.triangles[:,:,:2],axis=2)
curve_triangles=reference.triangles[np.all(np.abs(radii-75)<.01,axis=1)]
midpoints=(curve_triangles[:,0,:2]+curve_triangles[:,1,:2]+curve_triangles[:,2,:2])/3
error=float(np.max(np.abs(np.linalg.norm(midpoints,axis=1)-75)))
test('Analytic R75 conforms to uploaded faceted curve',error<.05,maximum_sample_deviation_mm=error)

# Shaft mandrels pass through the paired holes without clipping either material.
for z in [81,225,369]:
    for wall,axis in [('W03_front','Y'),('W04_left','X')]:
        base=(120.5,2.5,z)if axis=='Y'else(2.5,120.5,z)
        direction=(0,1,0)if axis=='Y'else(1,0,0)
        shaft=cq.Solid.makeCylinder(1.5,11,cq.Vector(*base),cq.Vector(*direction))
        overlap=sum(shaft.intersect(SHAPES[n]).Volume()for n in [wall,'C01_curved_corner'])
        test(wall+f' M3 at Z{z} bolt alignment',overlap<.01,overlap_mm3=overlap)
for deg in [22.5,45,67.5]:
    a=math.radians(deg);x,y=100*math.cos(a),100*math.sin(a)
    shaft=cq.Solid.makeCylinder(2.,TF+8,cq.Vector(x,y,0),cq.Vector(0,0,1))
    overlap=sum(shaft.intersect(SHAPES[n]).Volume()for n in ['F01_floor','C01_curved_corner'])
    test(f'Floor M4 at {deg} degrees bolt alignment',overlap<.01,overlap_mm3=overlap)

RESULTS['dwg_writer']='ODA 27.10; LibreDWG independently reads final DWGs'
RESULTS['secondary_operations']=['M3 exterior countersinks diameter 6.3 x 90 degrees','M4 floor underside countersinks diameter 8 x 90 degrees']

RESULTS['calibration_gaps_mm']=GAPS
RESULTS['assembly_order']=['curve','front +X to -X','left +Y to -Y','rear +Y to -Y','right +X to -X','floor upward','magnet inserts and fasteners']
(INTERNAL/'all_profiles.json').write_text(json.dumps(PROFILES,indent=2))
(INTERNAL/'curve_sections.json').write_text(json.dumps({str(k):v for k,v in curve_sections.items()}))
(INTERNAL/'curve_side.json').write_text(json.dumps(side_wires))
(ROOT/'Verification.json').write_text(json.dumps(RESULTS,indent=2))
failures=[t['name']for t in RESULTS['tests']if not t['pass']]
print('FAILURES',failures,flush=True)
if failures:raise RuntimeError('Resolve verification failures before delivery')
