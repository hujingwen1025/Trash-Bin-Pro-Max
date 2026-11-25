"""Independent export, load, tolerance and collision verification for R07.

Run after build_cad.py. Reports failures without relabelling them as passes.
--sweep N checks N points per path segment; --coarse checks only five endpoints.
Physical commissioning and supplier quotations are never inferred from CAD.
"""
import sys,json,argparse,itertools,time,hashlib,csv
from pathlib import Path
import numpy as np
import cadquery as cq
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Software'))
from geometry import Geometry,load_config,tray_polygon
REPORT={'revision':'R07','physical_tests_performed':False,'tests':[],'collisions':[],'manufacturing_release':'HOLD - physical prototype and supplier interfaces/quotes required'}
def check(name,ok,**data):
 REPORT['tests'].append({'name':name,'pass':bool(ok),**data})
 print(('PASS 'if ok else'FAIL ')+name,flush=True)
def segdist(p1,q1,p2,q2):
 u=q1-p1;v=q2-p2;w=p1-p2;a=u@u;b=u@v;cc=v@v;d=u@w;e=v@w;den=a*cc-b*b
 s=np.clip((b*e-cc*d)/den if den>1e-10 else 0,0,1);t=np.clip((b*s+e)/cc,0,1);s=np.clip((b*t-d)/a,0,1)
 return np.linalg.norm(w+s*u-t*v)

def obb_separated(ca,aa,ha,cb,ab,hb):
 # Full15-axis separating-axis test. Boxes enclose local analytic CAD, with
 # epsilon inflation. A rejection is conservative; remaining pairs use BRep.
 R=aa.T@ab;Q=np.abs(R)+1e-9;t=aa.T@(cb-ca)
 if np.any(np.abs(t)>ha+Q@hb+1e-6):return True
 if np.any(np.abs(t@R)>ha@Q+hb+1e-6):return True
 for i in range(3):
  p,q=(i+1)%3,(i+2)%3
  for j in range(3):
   k,l=(j+1)%3,(j+2)%3
   if abs(t[q]*R[p,j]-t[p]*R[q,j])>ha[p]*Q[q,j]+ha[q]*Q[p,j]+hb[k]*Q[i,l]+hb[l]*Q[i,k]+1e-6:return True
 return False

def common_volume(a,b):return a._bool_op((a,),(b,),BRepAlgoAPI_Common(),parallel=False).Volume()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--fail-fast',action='store_true');parser.add_argument('--coarse',action='store_true');parser.add_argument('--sweep',type=int,default=61);args=parser.parse_args()
 g=Geometry();c=g.c
 meta=json.loads((ROOT/'Verification/parts.json').read_text());mass=0;actual={}
 for name,m in meta.items():
  path=ROOT/m['folder']/'STEP'/f'{name}.step';s=cq.importers.importStep(str(path)).val();actual[name]=s
  mesh=trimesh.load(ROOT/m['folder']/'STL'/f'{name}.stl',force='mesh')
  check(name+' solid and export',s.isValid()and len(s.Solids())==1 and mesh.is_watertight and mesh.is_winding_consistent and abs(s.Volume()-mesh.volume)/s.Volume()<.01,solid_count=len(s.Solids()),step_volume_mm3=s.Volume(),stl_volume_mm3=float(mesh.volume))
 inst=json.loads((ROOT/'Verification/instance_transforms.json').read_text())
 for v in inst:
  if v['role']=='moving'and not v['instance'].startswith('D'):
   m=meta[v['part']];density=7.9e-6 if 'steel'in m['material']else 2.7e-6 if m['kind']=='metal'else 1.27e-6
   mass+=m['volume_mm3']*density
 REPORT['moving_mass']={'all_moving_CAD_including_full_rods_kg':mass,'unmodelled_fasteners_allowance_kg':.20,'total_budgeted_kg':mass+.20}
 check('Moving hardware mass allowance',mass+.20<=c['moving_mass_limit_kg'],**REPORT['moving_mass'])
 closure=0;servo=[];mins=1e6;trans=1e6;maxt=0;maxf=0;rodclear=1e6;crankclear=1e6;cones=[[]for _ in range(6)];allposes=[]
 for bid in c['bin_azimuth_deg']:
  for R,t in g.path(bid,161):
   a,H,P=g.points(R,t);allposes.append((bid,R,t));servo.append(g.servo_angles(a));closure=max(closure,float(np.max(abs(np.linalg.norm(P-H,axis=1)-g.d))))
   result=g.statics(R,t,[0,0,50]);mins=min(mins,float(result['singular_values'][-1]));trans=min(trans,float(min(result['transmission'])))
   for i in range(6):
    cones[i].append(R.T@((H[i]-P[i])/g.d[i]))
    for j in range(i):
     rodclear=min(rodclear,segdist(H[i],P[i],H[j],P[j])-8)
     crankclear=min(crankclear,segdist(g.B[i],H[i],g.B[j],H[j]))
   for az in np.linspace(0,2*np.pi,24,endpoint=False):
    # CG radius245 covers entire tray; CG60 is the centre height of a120 mm paper ball, plus23 mm surface offset.
    q=g.statics(R,t,[245*np.cos(az),245*np.sin(az),83],factor=1.5)
    maxt=max(maxt,float(max(abs(q['motor_torque_Nm']))));maxf=max(maxf,float(max(abs(q['rod_force_N']))))
 check('All four complete paths close',closure<1e-6,max_closure_error_mm=closure,sampled_poses=len(allposes))
 servo=np.array(servo)
 check('Guarded servo travel',servo.min()>=10 and servo.max()<=230,min_deg=servo.min().item(),max_deg=servo.max().item())
 check('Normalized Jacobian conditioning',mins>.06,minimum_singular_value=mins,normalizing_radius_mm=100)
 check('Crank transmission away from singularity',trans>.20,minimum_normalized_transmission=trans)
 check('Rod tube centre-line envelope',rodclear>2,minimum_centreline_distance_minus_8mm=rodclear)
 check('Neighbouring crank line separation',crankclear>30,minimum_centreline_mm=crankclear)
 coneangles=[]
 for directions in cones:
  a=np.array(directions);n=a.mean(0);n/=np.linalg.norm(n);coneangles.append(float(np.rad2deg(np.arccos(np.clip(a@n,-1,1))).max()))
 check('Upper socket demanded cone',max(coneangles)<50,per_joint_max_deg=coneangles,designed_neck_flare_deg=55)
 # These are engineering design screens, NOT a manufacturer continuous rating.
 # 0.12 Nm added for crank/rod own weight and friction; already1.5x gravity.
 peak=maxt+.12;static=maxt/1.5+.08
 check('Peak torque below stall with factor',peak<85*.0980665,calculated_factored_peak_Nm=peak,static_plus_allowance_Nm=static,manufacturer_stall_Nm=85*.0980665,continuous_rating='NOT PUBLISHED; thermal qualification REQUIRED')
 REPORT['loads']={'payload_kg':2,'payload_CG_radius_mm':245,'CG_height_above_joint_plane_mm':83,'dynamic_factor':1.5,'motor_factored_peak_Nm':peak,'motor_static_Nm':static,'max_factored_link_force_N':maxf,'moving_hardware_model_kg':c['moving_mass_limit_kg'],'continuous_rating_proven':False}
 I=np.pi*(8**4-6**4)/64;Pcrit=np.pi**2*69000*I/c['rod_center_mm']**2
 check('Link Euler buckling screen',Pcrit/maxf>3,euler_N=float(Pcrit),factor_against_factored_force=float(Pcrit/maxf),boundary='pinned-pinned, no defects; joint proof still required')

 # Bounded manufacturing perturbations, reproducible sampling, not an interval proof.
 rng=np.random.default_rng(707);bad=0;tmin=1e9;tmax=-1e9
 for k in range(512):
  gg=Geometry();gg.B+=rng.uniform(-.2,.2,(6,3));gg.p+=rng.uniform(-.2,.2,(6,3));gg.d+=rng.uniform(-.2,.2,6);gg.h+=rng.uniform(-.1,.1)
  bid=list(c['bin_azimuth_deg'])[k%4];R,t=list(g.path(bid,33))[k%65]
  try:
   a=gg.ik(R,t);angles=gg.servo_angles(a);tmin=min(tmin,float(min(angles)));tmax=max(tmax,float(max(angles)))
  except ValueError:bad+=1
 check('512 sampled dimensional perturbations',bad==0,failures=bad,anchor_coordinate_tolerance_mm=.2,rod_length_tolerance_mm=.2,crank_tolerance_mm=.1,min_servo_deg=tmin,max_servo_deg=tmax,scope='sampled closure/travel only, not proof of physical clearance')
 # Shaft material must be certified; conservative factor2 torsion concentration.
 output_torque=peak*c['reduction']*c['belt_efficiency'];tau=2*16*output_torque*1000/(np.pi*8**3);vm=np.sqrt(3)*tau
 check('Keyed shaft torsion screen',vm<250,factored_output_torque_Nm=output_torque,keyway_stress_multiplier=2,equivalent_stress_MPa=vm,minimum_material_yield_MPa=500,screen_factor=500/vm,scope='torsion only; supplier sample checks bending and key retention')
 # Belt length with a positive toothed idler: convex tangent path, no back bend.
 radii=[36*5/(2*np.pi),20*5/(2*np.pi),20*5/(2*np.pi)]
 lengths=[]
 for angle in(-4,4):
  a=np.deg2rad(angle);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
  C=rot@np.array([10.3,30])+[40,-74]
  length=unary_union([Point(*q).buffer(r,quad_segs=2048)for q,r in zip(([0,0],[40,-96],C),radii)]).convex_hull.length
  lengths.append(length)
 check('360 HTD5M belt tension adjustment screen',min(lengths)<360<max(lengths),tangent_path_length_range_mm=lengths,belt_length_mm=360,idler='20T toothed INSIDE, no small backside idler',scope='pitch geometry; actual belt tooth engagement/tension approval required')

 # Metal post screen, including conservative lateral force equal to1.5g load.
 Ipost=np.pi*(60**4-54**4)/64;Fpost=(c['moving_mass_limit_kg']+2)*9.81*1.5;Mpost=Fpost*(512.5+330)
 poststress=Mpost*30/Ipost;postdeflection=Fpost*512.5**3/(3*200000*Ipost)
 check('Steel post cantilever screen',poststress<235/2 and postdeflection<.5,stress_MPa=poststress,tip_deflection_mm=postdeflection,force_N=Fpost,minimum_yield_MPa=235,scope='tube only; cap welds, bolts and base require physical proof')
 # Preserve bolt-head/tool clearance below the ribbed fixed deck.
 ph=json.loads((ROOT/'Verification/profiles.json').read_text())['M08_Fixed_Deck']['holes'];pp=np.array([p[:2]for p in ph])
 aa=np.deg2rad(c['deck_rib_phase_deg'])+np.arange(6)*np.pi/3;uu=np.c_[np.cos(aa),np.sin(aa)];near=pp[:,None,:]-np.clip(pp@uu.T,75,215)[:,:,None]*uu[None,:,:]
 edgegap=np.linalg.norm(near,axis=2).min()-1.5-5
 check('Deck rib fastener access screen',edgegap>2,minimum_bolt_head_to_rib_gap_mm=float(edgegap),bolt_head_envelope_radius_mm=5,rib_phase_deg=c['deck_rib_phase_deg'])

 zz=np.linspace(0,6,20001);cavity=np.sqrt(8.15**2-zz**2);flare=np.where(zz>=3,6+(zz-3)*(10.586-6)/3.2,0);throat=float(np.maximum(cavity,flare).min());lip=8-throat
 check('Upper ball geometric retention overlap',lip>=.75,ball_diameter_mm=16,cavity_diameter_mm=16.3,minimum_throat_radius_mm=throat,radial_retaining_overlap_mm=lip,scope='geometry only, not printed strength;200 N physical joint proof required')
 # One-piece guide at45 degree yaw, before slicer/support-specific clearance.
 bm=meta['P06_Discharge_Guide']['bounds'];sx,sy,sz=[bm[k+3]-bm[k]for k in range(3)];xy=(sx+sy)/np.sqrt(2)
 check('One-piece guide nominal print envelope',xy+10<=320 and sz<=320,yaw_deg=45,part_rotated_XY_mm=xy,height_mm=sz,assumed_brim_allowance_each_side_mm=5,screen_build_volume_mm=[320,320,320],scope='bounding box only; confirm actual printer/slicer supports before printing')
 # Inspect actual inclined tap tracks through the whole carrier thickness.
 pr=json.loads((ROOT/'Verification/profiles.json').read_text())['M09_Moving_Carrier'];region=Polygon(pr['outline'],pr['slots']);rows=list(csv.DictReader((ROOT/'01_Metal/Carrier_Joint_Hole_Axes.csv').open()));tracks=[];ligaments=[]
 for row in rows:
  origin=np.array([float(row[k])for k in('X_mm','Y_mm','Z_mm_carrier_local')]);axis=np.array([float(row[k])for k in('axis_X','axis_Y','axis_Z')]);track=[]
  for z in(0,4):
   q=origin+axis*((z-origin[2])/axis[2]);track.append(q);point=Point(*q[:2]);signed=region.boundary.distance(point)*(1 if region.contains(point)else -1);ligaments.append(signed-1.5/abs(axis[2]))
  tracks.append(track)
 check('Inclined carrier tap metal ligament',min(ligaments)>2,minimum_ligament_mm=min(ligaments),thread_major_diameter_mm=3,scope='both faces, conservative projected thread radius')
 gaps=[segdist(*a,*b)-3 for i,a in enumerate(tracks)for b in tracks[:i]]
 check('Inclined carrier taps do not intersect',min(gaps)>2,minimum_thread_to_thread_clearance_mm=float(min(gaps)))
 # Actual hardware dimensions, not generic frictionless virtual joints.
 print('Loading parametric solids for collision checks',flush=True)
 sys.path.insert(0,str(ROOT/'Source'));import build_cad as model
 basescenes=[]
 if args.coarse:
  basescenes=[('REST',np.eye(3),[0,0,c['rest_height_mm']])]+[(b,*list(g.path(b,2))[-1])for b in c['bin_azimuth_deg']]
 else:
  for b in c['bin_azimuth_deg']:
   route=list(g.path(b,args.sweep))
   basescenes.extend((b,R,t)for R,t in(route if not basescenes else route[args.sweep:]))
 checked=0;seen_fixed=set();relative_seen=set();min_external=1e6;obb_rejected=0
 local_bounds={k:np.array(v['bounds'])for k,v in meta.items()}
 for key,shape in model.purchase.items():
  b=shape.BoundingBox();local_bounds[key]=np.array([b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax])
 for idx,(bid,R,t)in enumerate(basescenes):
  members,refs=model.build_assembly(R,t,'verification',export=False)
  # Purchased envelopes included. They must be proven by a physical sample too.
  objects=members+refs
  oriented=[]
  for name,key,shape,T,role in objects:
   T=np.array(T);bb=local_bounds[key];oriented.append((T[:3,:3]@((bb[:3]+bb[3:])/2)+T[:3,3],T[:3,:3],(bb[3:]-bb[:3])/2))
  bounds=np.array([[s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax]for _,_,s,_,_ in objects])
  lo=bounds[:,:3];hi=bounds[:,3:];sep=np.maximum(0,np.maximum(lo[:,None,:]-hi[None,:,:],lo[None,:,:]-hi[:,None,:]));near=np.sum(sep**2,axis=2)<.01
  pairs=np.transpose(np.nonzero(np.triu(near,k=1)))
  for i,j in pairs:
   na,ka,sa,_,ra=objects[i];nb,kb,sb,_,rb=objects[j]
   # Joint metal inserts/screw threads are intentionally schematic. Only named
   # reference fasteners that occupy their machined bores are included.
   if ra!='moving'and rb!='moving':
    pair=tuple(sorted((na,nb)))
    if pair in seen_fixed:continue
    seen_fixed.add(pair)
   # Assembly-contact surfaces may touch, but positive material overlap is invalid.
   Ta=np.array(objects[i][3]);Tb=np.array(objects[j][3]);relative=np.c_[Ta[:3,:3].T@Tb[:3,:3],Ta[:3,:3].T@(Tb[:3,3]-Ta[:3,3])]
   if obb_separated(*oriented[i],*oriented[j]):obb_rejected+=1;continue
   cachekey=(na,nb,tuple(np.round(relative,7).ravel()))
   if cachekey in relative_seen:continue
   relative_seen.add(cachekey)
   checked+=1
   vol=common_volume(sa,sb)
   if vol>.10:
    issue={'pose':bid,'sample':idx,'part_a':na,'part_b':nb,'overlap_mm3':round(vol,4)}
    REPORT['collisions'].append(issue)
    if len(REPORT['collisions'])<=60:print('COLLISION',issue,flush=True)
  if args.fail_fast and REPORT['collisions']:
   check('CAD solid interference sweep',False,poses_completed=idx+1,planned_poses=len(basescenes),collision_count=len(REPORT['collisions']))
   REPORT['digital_tests_passed']=False
   (ROOT/'Verification/Geometry_Verification.json').write_text(json.dumps(REPORT,indent=2));return
  if idx%5==0:print('Collision pose',idx+1,'/',len(basescenes),'pairs',checked,flush=True)
 check('CAD solid interference sweep',not REPORT['collisions'],poses=len(basescenes),boolean_pairs=checked,collision_count=len(REPORT['collisions']))
 # Independent R06 bin-reference checks: fixed solids once and five moving poses.
 bins=[cq.importers.importStep(str(ROOT.parent/'Rev 06 - 10mm Basswood Hybrid Bins'/'STEP'/f'{b}_Assembly.step')).val().translate((0,0,20))for b in c['bin_azimuth_deg']]
 bc=0;binissues=[]
 for k,(bid,R,t)in enumerate([('REST',np.eye(3),[0,0,c['rest_height_mm']])]+[(b,*list(g.path(b,2))[-1])for b in c['bin_azimuth_deg']]):
  members,refs=model.build_assembly(R,t,'bin reference verification',export=False)
  for name,key,shape,T,role in members+refs:
   if k and role!='moving':continue
   bb=shape.BoundingBox()
   for j,bs in enumerate(bins):
    b=bs.BoundingBox()
    if min(bb.xmax,b.xmax)-max(bb.xmin,b.xmin)<=0 or min(bb.ymax,b.ymax)-max(bb.ymin,b.ymin)<=0 or min(bb.zmax,b.zmax)-max(bb.zmin,b.zmin)<=0:continue
    bc+=1;vol=common_volume(shape,bs)
    if vol>.1:binissues.append({'part':name,'bin':j+1,'pose':bid,'overlap_mm3':vol})
 check('Exact R06 bin reference at five poses',not binissues,boolean_pairs=bc,collisions=binissues,scope='nominal bins only; removal and stock tolerances require samples')
 REPORT['sampling']={'sweep_points_per_segment':args.sweep,'collision_poses':len(basescenes),'collision_scope':'nominal CAD plus purchased envelopes; invariant rigid-pair contacts cached; sampled, not continuous collision proof','overlap_reporting_threshold_mm3':0.1,'OBB_separating_axis_rejections':obb_rejected}
 fingerprint=json.loads((ROOT/'Verification/Build_Fingerprint.json').read_text())
 check('Build source/config freshness',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in fingerprint.items()),source_sha256=fingerprint)
 REPORT['digital_tests_passed']=all(q['pass']for q in REPORT['tests'])
 out=ROOT/'Verification'/('Coarse_Verification.json'if args.coarse else'Geometry_Verification.json');out.write_text(json.dumps(REPORT,indent=2))
 print('REPORT',out,'PASS',REPORT['digital_tests_passed'],flush=True)

if __name__=='__main__':main()
