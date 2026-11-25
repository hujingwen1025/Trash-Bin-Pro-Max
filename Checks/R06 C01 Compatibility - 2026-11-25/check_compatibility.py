"""Read-only comparison of the supplied bin STL against released R06 components.
Uses mesh sections and ray intersections; no CAD is regenerated or modified.
"""
from pathlib import Path
import sys,os,json,hashlib,math,shutil
# Restore access to the existing read-only cached CAD-analysis packages on this Mac.
cache=Path('/Users/jingwen.hu/.cache/uv/archive-v0')
if cache.exists():sys.path[:0]=[str(p)for p in cache.iterdir()if p.is_dir()]
import numpy as np
import trimesh
from shapely.geometry import Polygon,box,MultiLineString
from shapely.ops import polygonize,unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=Path('/Users/jingwen.hu/.codex/attachments/744f3622-8c43-43e5-996d-7adc734101a4/Bin Studio - Bin (3).stl')
R06=ROOT/'Rev 06 - 10mm Basswood Hybrid Bins'
REFERENCE=ROOT/'Reference Inputs/744f3622--Bin Studio - Bin (3).stl'
if not REFERENCE.exists():shutil.copy2(SOURCE,REFERENCE)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p)for p in R06.rglob('*')if p.is_file()}
m=trimesh.load_mesh(SOURCE);c=trimesh.load_mesh(R06/'STL/B1_C01.stl');walls=[trimesh.load_mesh(R06/'STL'/f'B1_W0{i}.stl')for i in range(1,5)];floor=trimesh.load_mesh(R06/'STL/B1_F01.stl')
print('Mesh loaded',len(m.faces),m.bounds.tolist(),flush=True)
def planes(mesh,axis):
 sel=np.abs(mesh.face_normals[:,axis])>.999999
 v,idx=np.unique(np.round(mesh.triangles_center[sel,axis],4),return_inverse=True);a=np.bincount(idx,weights=mesh.area_faces[sel])
 return [{'position_mm':float(v[i]),'area_mm2':float(a[i])}for i in np.argsort(-a)[:12]]
def section(mesh,z):
 # Intersect triangles and polygonise their segment network; select material
 # faces with an independent odd/even 2D crossing rule (no graph dependency).
 lines=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,z])[:,:,:2]
 lines=np.round(lines,7);faces=list(polygonize(unary_union(MultiLineString(lines.tolist()))))
 if not faces:return Polygon()
 selected=[];a=lines[:,0];b=lines[:,1]
 for face in faces:
  point=face.representative_point();x,y=point.x,point.y
  valid=(a[:,1]>y)!=(b[:,1]>y);aa=a[valid];bb=b[valid]
  hit=aa[:,0]+(y-aa[:,1])*(bb[:,0]-aa[:,0])/(bb[:,1]-aa[:,1])
  if np.count_nonzero(hit>x)%2:selected.append(face)
 return unary_union(selected)if selected else Polygon()

def rays(mesh,origin,direction):
 # Vectorised Moller-Trumbore ray/triangle intersections, avoiding an R-tree dependency.
 tri=mesh.triangles;d=np.asarray(direction,float);o=np.asarray(origin,float)
 e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p);ok=np.abs(det)>1e-10
 inv=np.zeros(len(det));inv[ok]=1/det[ok];tv=o-tri[:,0];u=np.einsum('ij,ij->i',tv,p)*inv;q=np.cross(tv,e1);v=(q@d)*inv;t=np.einsum('ij,ij->i',e2,q)*inv
 ok&=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>=0)
 return np.unique(np.round(t[ok],5)).tolist()

# Fit cylindrical wall patches away from the top/bottom and tangent fillets.
v=m.vertices;theta=np.degrees(np.arctan2(v[:,1],v[:,0]));rr=np.linalg.norm(v[:,:2],axis=1)
fits=[]
for nominal in [75.,80.]:
 sel=(v[:,2]>20)&(v[:,2]<449)&(theta>15)&(theta<75)&(np.abs(rr-nominal)<.03)
 xy=v[sel,:2];q=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],np.sum(xy**2,axis=1),rcond=None)[0];center=q[:2];r=np.sqrt(q[2]+center@center)
 fits.append({'surface':'post-facing'if nominal==75 else'trash-facing','radius_mm':float(r),'centre_XY_mm':center.tolist(),'max_radial_residual_mm':float(np.max(np.abs(np.linalg.norm(xy-center,axis=1)-r))),'vertices_used':len(xy)})
print('Cylinder fits',fits,flush=True)
# Intersections at the exact released hole axes. Solid material on an intended
# hole axis demonstrates the uploaded monolithic model lacks the required opening.
holes=[]
for z in [81.,225.,369.]:
 for label,o,d,wall in [('front',[120.5,0,z],[0,1,0],walls[2]),('left',[0,120.5,z],[1,0,0],walls[3])]:
  holes.append({'wall':label,'Z_mm':z,'upload_ray_material_boundaries_mm':rays(m,o,d),'R06_wood_wall_boundaries_mm':rays(wall,o,d)})
for a in [22.5,45,67.5]:
 x,y=100*np.cos(np.deg2rad(a)),100*np.sin(np.deg2rad(a))
 holes.append({'floor_M4_angle_deg':a,'XY_mm':[float(x),float(y)],'upload_vertical_ray_boundaries_mm':rays(m,[x,y,-1],[0,0,1]),'R06_floor_vertical_ray_boundaries_mm':rays(floor,[x,y,-1],[0,0,1]),'ray_origin_Z_mm':-1})
print('Hole axes checked',flush=True)
sections={};zlevels=[5.5,15.,45.,180.,225.,405.]
for z in zlevels:
 u=section(m,z);p=section(c,z);w=section(walls[2],z).union(section(walls[3],z));f=section(floor,z)
 sections[str(z)]={'upload_area_mm2':u.area,'C01_area_mm2':p.area,'C01_overlap_upload_mm2':p.intersection(u).area,'C01_overlap_uploaded_floor_zone_mm2':p.intersection(u).intersection(box(-1,-1,351,351)).area if z<10 else 0,'C01_bounds_XY_mm':list(p.bounds),'upload_corner_bounds_mm':list(u.intersection(box(0,0,140,140)).bounds)}
 print('section',z,sections[str(z)],flush=True)

# The original four underside magnet pockets are measured independently at Z2.5.
u=section(m,2.5);mag=[]
for ring in u.interiors if isinstance(u,Polygon)else []:
 p=Polygon(ring);cent=p.centroid
 if any(np.linalg.norm(np.array([cent.x,cent.y])-np.array(xy))<.1 for xy in [(102.5,102.5),(102.5,250),(250,102.5),(250,250)]):
  coords=np.array(ring.coords);rad=np.linalg.norm(coords-np.array([cent.x,cent.y]),axis=1);mag.append({'center_mm':[cent.x,cent.y],'diameter_mm_approx':float(2*np.mean(rad)),'area_mm2':p.area})
variant_meshes={}
for bid,signs in {'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}.items():
 x=trimesh.load_mesh(R06/'STL'/f'{bid}_C01.stl');points=x.vertices*np.array([*signs,1]);bounds=[points.min(0).tolist(),points.max(0).tolist()]
 variant_meshes[bid]={'watertight':bool(x.is_watertight),'winding_consistent':bool(x.is_winding_consistent),'bounds_after_reflection_to_B1_mm':bounds,'B1_envelope_match':bool(np.allclose(bounds,c.bounds,atol=.001))}
 assert variant_meshes[bid]['watertight']and variant_meshes[bid]['winding_consistent']and variant_meshes[bid]['B1_envelope_match']
assert len(holes)==9 and all(q.get('upload_ray_material_boundaries_mm')==[2.5,7.5,345.,350.]for q in holes[:6])
assert all(q['upload_vertical_ray_boundaries_mm']==[1.,11.]for q in holes[6:])
assert all(q['R06_wood_wall_boundaries_mm']==[]for q in holes[:6])and all(q['R06_floor_vertical_ray_boundaries_mm']==[]for q in holes[6:])
assert all(q['upload_area_mm2']>0 and q['C01_area_mm2']>0 for q in sections.values())
report={'date':'2026-11-25','units':'mm; STL assumed millimetres, supported by matching known envelope','input_file':str(SOURCE),'input_sha256':sha(SOURCE),'preserved_input':str(REFERENCE.relative_to(ROOT)),'uploaded_coordinate_variant':'B1 (+X,+Y); the filename suffix (3) is not a bin-variant designation','R06_C01_variant_mesh_checks':variant_meshes,'method':'Fresh mesh topology, planar-face measurements, fitted cylindrical patches, horizontal cross-sections, exact nominal hole-axis ray probes. No BRep conversion or physical trial. No geometry modified.','uploaded_mesh':{'faces':len(m.faces),'vertices':len(m.vertices),'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'bounds_mm':m.bounds.tolist(),'envelope_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'principal_planes':{str(k):planes(m,k)for k in range(3)},'cylinder_fits':fits,'underside_magnet_pockets':mag},'R06_requirements':{'wall_thickness_mm':6,'floor_thickness_mm':10,'height_mm':450,'outside_curve_radius_mm':75,'inside_curve_radius_mm':81,'curve_split_station_mm':102.5,'wall_M3_axes_z_mm':[81,225,369],'floor_M4_axes_radius_mm':100,'floor_M4_axes_angles_deg':[22.5,45,67.5],'C01_floor_pad_underside_mm':10,'C01_floor_pad_top_mm':18,'C01_models':{f'B{i}_C01':{'sha256':sha(R06/'STL'/f'B{i}_C01.stl')}for i in range(1,5)}},'hole_axis_probes':holes,'sections':sections,'verdict':'NOT A DIRECT FIT to the supplied 5 mm-wall monolithic bin. R06 C01 is a replacement corner for the complete R06 6 mm-wall / 10 mm-floor hybrid panel system, not an add-on liner for an intact bin.','compatible_features':['Overall envelope 347.5 x 347.5 x 450','Nominal floor top Z10','Post-facing R75 curve'], 'mismatches':['5 mm uploaded walls versus 6 mm R06 walls','Uploaded trash-facing curve R80 versus R81 released C01; C01 also has internal fastening flanges/pads','No released C01 alternating wall fingers/slots in the monolithic upload','Released side M3 and floor M4 openings absent at their nominal axes','Uploaded underside magnet pockets are not released floor through-holes for separate M01 inserts'],'physical_tests_performed':False,'R06_files_unchanged':all(sha(ROOT/p)==h for p,h in protected.items()),'existing_R06_file_count_checked':len(protected)}
assert report['R06_files_unchanged']
(OUT/'Compatibility_Results.json').write_text(json.dumps(report,indent=2))
# Draw actual STL sections without adding or removing material.
fig,axes=plt.subplots(2,2,figsize=(13,11),facecolor='white')
def paint(ax,poly,color,label,alpha=.5):
 geom=list(poly.geoms)if hasattr(poly,'geoms')else[poly];first=True
 for p in geom:
  if p.is_empty:continue
  x,y=p.exterior.xy;ax.fill(x,y,color=color,alpha=alpha,label=label if first else None);ax.plot(x,y,color=color,lw=1)
  for h in p.interiors:ax.fill(*h.xy,color='white');ax.plot(*h.xy,color=color,lw=.7)
  first=False
for ax,z,title in zip(axes.flat,[180.,45.,5.5,15.],['Smooth wall vs C01 wing','C01 finger-joint level','Floor tabs: slots required in floor','Floor pads above 10 mm floor']):
 paint(ax,section(m,z),'#6b91b9','Uploaded bin',.38);paint(ax,section(c,z),'#d39651','R06 B1_C01',.65)
 ax.set(xlim=(0,140),ylim=(0,140),aspect='equal',xlabel='X / mm',ylabel='Y / mm');ax.set_title(f'{title}\nHorizontal slice Z{z:g} mm',loc='left',fontsize=12);ax.grid(alpha=.16);ax.legend(loc='upper right',fontsize=9)
fig.suptitle('R06 C01 compatibility check - supplied bin has 5 mm walls',fontsize=17,weight='bold');fig.text(.06,.025,'Blue = supplied complete bin; amber = released C01 in its intended B1 location. Overlap is expected for a replacement corner, not an add-on.',fontsize=10);fig.tight_layout(rect=[0,.05,1,.95]);fig.savefig(OUT/'Cross_Section_Comparison.png',dpi=170);plt.close(fig)
print('REPORT',OUT,flush=True)
