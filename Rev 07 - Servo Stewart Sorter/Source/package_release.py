"""Create a checked prototype archive; never imply physical/procurement release."""
from pathlib import Path
import json,hashlib,zipfile,csv
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'Verification'/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
g=read('Geometry_Verification.json');d=read('DWG_Verification.json');c=read('Cutting_Files_Verification.json');e=read('Final_Export_Verification.json');s=read('Software_Verification.json');p=read('PDF_QA.json')
assert g['digital_tests_passed']and not g['collisions']
assert d['all_passed']and c['all_passed']and e['all_passed']and p['all_passed']
assert s['failures']==0 and s['errors']==0 and s['hardware_used']is False
for name,value in s['source_sha256'].items():assert sha(ROOT/name)==value,name+' software evidence stale'
assert sha(ROOT/'Software/configuration.json')==s['configuration_sha256']
for name,value in read('Build_Fingerprint.json').items():assert sha(ROOT/name)==value,name+' build fingerprint stale'
# The two post-validation changes affect only annotation/measurement metadata.
recorded_source=next(t for t in g['tests']if t['name']=='Build source/config freshness')['source_sha256']['Source/build_cad.py']
if recorded_source!=sha(ROOT/'Source/build_cad.py'):
 annotation=read('Post_Validation_Annotation.json');measurements=read('Post_Validation_Measurements.json')
 assert annotation['current_build_source_sha256']==measurements['previous_build_source_sha256']
 assert sha(ROOT/'Source/build_cad.py')==measurements['current_build_source_sha256']
 assert measurements['all_exact_bounds_inside_prior_conservative_boxes']
 for q in measurements['parts']:
  m=json.loads((ROOT/'Verification/parts.json').read_text())[q['part']];assert sha(ROOT/m['folder']/'STEP'/(q['part']+'.step'))==q['STEP_sha256_unchanged']
for q in p['files']:assert sha(ROOT/q['file'])==q['sha256'],'PDF QA stale'
config=json.loads((ROOT/'Software/configuration.json').read_text());assert not config['calibrated']and not config['physical_qualification_passed']
meta=json.loads((ROOT/'Verification/parts.json').read_text());order=list(csv.DictReader((ROOT/'Manufacture_List.csv').open(encoding='utf-8-sig')));assert len(order)==sum(m['quantity']>0 for m in meta.values())
for row in order:
 assert int(row['quantity'])==meta[row['part']]['quantity']
 for key in('step','stl'):assert(ROOT/row[key]).is_file()
status={'revision':'R07','release':'PROTOTYPE REVIEW / SAMPLE QUOTING ONLY','manufacturing_release':False,'procurement_release':False,'physical_tests_performed':False,'budget_cap_CNY':3000,'accepted_quotes':0,'payload_target_kg':2,'moving_hardware_model_kg':config['moving_mass_limit_kg'],'CAD_engineering_checks':len(g['tests']),'sampled_distinct_solid_poses':g['sampling']['collision_poses'],'individual_part_export_checks':len(e['tests']),'DWG_checks':len(d['tests']),'cut_reference_checks':len(c['tests']),'software_tests':s['tests_run'],'PDF_pages':sum(q['pages']for q in p['files']),'unresolved':['Actual servo/horn/bearing/belt/key/insert and fastener sample interfaces','Printed strength/creep, full loads, thermal duty and wire/cable routing','Bin impact cushioning, real-item routing, restrained power-loss and removal tests','Accepted all-in quotations within hard CNY3000 cap'],'post_validation_metadata':'Annotation and exact envelope corrections only; unchanged solids and conservative original collision bounds are evidenced in Verification.'}
if (ROOT/'Verification/Visual_Update_Verification.json').exists():
 v=read('Visual_Update_Verification.json')
 assert v['all_passed']and not v['engineering_file_differences']
 for relative,digest in v['engineering_sha256'].items():assert sha(ROOT/relative)==digest,relative+' visual-update preservation evidence stale'
 for relative,digest in v['visual_file_sha256'].items():assert sha(ROOT/relative)==digest,relative+' visual-update evidence stale'
 status['visual_update']='A: 13 labelled assembly illustrations, component colours and colour key; unchanged engineering files/software'
 status['visual_update_evidence']='Verification/Visual_Update_Verification.json'
(ROOT/'Package_Status.json').write_text(json.dumps(status,indent=2))
excluded={'03_Purchase/Post_Spacer_REFERENCE.step','SHA256SUMS.txt','Manifest.json'}
files=[q for q in sorted(ROOT.rglob('*'))if q.is_file()and'__pycache__'not in q.parts and q.suffix!='.pyc'and q.name!='.DS_Store'and str(q.relative_to(ROOT))not in excluded]
manifest=[{'file':str(q.relative_to(ROOT)),'bytes':q.stat().st_size,'sha256':sha(q)}for q in files]
(ROOT/'Manifest.json').write_text(json.dumps({'files':manifest,'omitted_unused_reference':['03_Purchase/Post_Spacer_REFERENCE.step']},indent=2))
(ROOT/'SHA256SUMS.txt').write_text(''.join(v['sha256']+'  '+v['file']+'\n'for v in manifest))
archive=ROOT.parent/'Trash_Bin_R07_Servo_Stewart_Prototype.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for q in files+[ROOT/'Manifest.json',ROOT/'SHA256SUMS.txt']:z.write(q,str(Path(ROOT.name)/q.relative_to(ROOT)))
with zipfile.ZipFile(archive)as z:assert z.testzip()is None
print('ARCHIVE',archive,'MB',round(archive.stat().st_size/1e6,1),'files',len(files)+2)
