from pathlib import Path
import cadquery as cq,json,math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT
# Only proper upright rotations plus translations are accepted: no reflection or scaling.
TEMPLATES=['B1_W01','B1_W02','B1_W03','B1_W04','B1_F01','B1_C01','B2_C01']
TARGETS=[f'{b}_{p}'for b in ['B1','B2','B3','B4']for p in ['W01','W02','W03','W04','F01','C01']]
S={n:cq.importers.importStep(str(ROOT/'STEP'/f'{n}.step')).val()for n in set(TEMPLATES+TARGETS)}
results=[]
for target in TARGETS:
 part=target.split('_')[1]
 candidates=['B1_W03','B1_W04']if part in ['W03','W04']else(['B1_C01','B2_C01']if part=='C01'else['B1_'+part])
 t=S[target];tb=t.BoundingBox();found=None
 for template in candidates:
  for angle in [0,90,180,270]:
   q=S[template].rotate((0,0,0),(0,0,1),angle);qb=q.BoundingBox()
   if max(abs(qb.xlen-tb.xlen),abs(qb.ylen-tb.ylen),abs(qb.zlen-tb.zlen))>.001:continue
   shift=(tb.xmin-qb.xmin,tb.ymin-qb.ymin,tb.zmin-qb.zmin);q=q.translate(shift)
   diff=q.cut(t).Volume()+t.cut(q).Volume()
   if diff<.02:
    found={'target':target,'order_template':template,'rotate_about_global_Z_degrees':angle,'translate_after_rotation_mm':shift,'symmetric_difference_mm3':diff,'pass':True};break
  if found:break
 assert found,target
 results.append(found);print(target,found['order_template'],found['rotate_about_global_Z_degrees'],found['symmetric_difference_mm3'],flush=True)
# Report exact curve difference if someone tries ordering all curves from only B1.
curve_differences=[]
t=S['B2_C01'];tb=t.BoundingBox()
for angle in [0,90,180,270]:
 q=S['B1_C01'].rotate((0,0,0),(0,0,1),angle);qb=q.BoundingBox();q=q.translate((tb.xmin-qb.xmin,tb.ymin-qb.ymin,tb.zmin-qb.zmin));diff=q.cut(t).Volume()+t.cut(q).Volume()
 curve_differences.append({'angle':angle,'symmetric_difference_mm3':diff})
counts={n:sum(r['order_template']==n for r in results)for n in TEMPLATES}
assert counts=={'B1_W01':4,'B1_W02':4,'B1_W03':4,'B1_W04':4,'B1_F01':4,'B1_C01':2,'B2_C01':2},counts
report={'method':'Complete finished STEP solid comparison, including countersinks and nut pockets. Only rotations about Z and translations permitted; no reflection, scaling or geometry edits.','comparison_tolerance_mm3':.02,'templates':counts,'mappings':results,'all_curves_from_B1_comparison':curve_differences,'physical_tests_performed':False}
(OUT/'Repeat_Part_Verification.json').write_text(json.dumps(report,indent=2));print('FINISHED',counts,flush=True)
