from pathlib import Path
import csv,json,hashlib,subprocess,sys,re
r=Path(__file__).resolve().parents[1];v=r/'Verification'
result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(r/'Software/tests'),'-v'],capture_output=True,text=True)
if result.returncode:raise RuntimeError(result.stdout+result.stderr)
test_output=result.stdout+result.stderr
test_count=int(re.search(r"Ran (\d+) tests",test_output).group(1))
(v/'Software_Test_Output.txt').write_text(test_output)
sources={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((r/'Software').rglob('*.py'))}
(v/'Software_Verification.json').write_text(json.dumps({'tests_run':test_count,'failures':0,'errors':0,'hardware_used':False,'method':'unittest with fake serial bus/clock plus numerical kinematics','source_sha256':sources,'configuration_sha256':hashlib.sha256((r/'Software/configuration.json').read_bytes()).hexdigest()},indent=2))
p=subprocess.run([sys.executable,str(r/'Software/sorter.py'),'simulate'],capture_output=True,text=True,check=True)
(v/'Dry_Run.jsonl').write_text(p.stdout)
if not (v/'Physical_Acceptance_Record.csv').exists():
 with (v/'Physical_Acceptance_Record.csv').open('w',newline='')as f:
  w=csv.writer(f);w.writerow(['test','specimen_or_pose','target','measured_result','pass_fail','date_operator','evidence_file'])
  for name,target in [('Quotes','All-in purchased/new manufactured mechanism <=3000CNY'),('R06 fits','Existing R06 stock coupons/prototype/load procedure'),('Servo and horn sample','Matched horn, body, protocol, direction'),('Bearing and shaft fit','22H7 and8h6; retaining compound cured and proofed'),('One belt cell','360-5M15,20T toothed idler, supplier tension/tooth engagement approval'),('One rod proof','200N axial60s, <=0.2mm permanent length change'),('Moving mass','<=1.3kg including all wires/fasteners'),('Deck loaded deflection','<1mm measured change of shaft centres under2kg'),('Unloaded motion','10 cycles per bin; no contact/binding'),('Incremental payload','0.25/0.5/1/2kg, centre and off-centre'),('Thermal qualification','30cycles>=30s interval,ambient>=30C,all<55C,last10rise<=2C'),('Wire/cable sweep','No taut cables/snags in any transition'),('Power-loss catch','Restrained,level/mid/dump,unloaded then progressive load'),('Bin removal','Guide module removable; extraction without structural impact')]:
   w.writerow([name,'',target,'','NOT RUN','',''])
  for b in ('B1','B2','B3','B4'):
   for n in range(1,21):w.writerow(['Routing '+str(n),b,'Record real item/mass/orientation; no escape,bridge,wrong-bin rebound','','NOT RUN','',''])
(v/'Reference_Provenance.json').write_text(json.dumps({'input_files':[{'file':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted((r/'Reference Inputs').iterdir())if p.is_file()],'sources':[{'url':'https://www.hiwonder.com/products/htd-85h','use':'Servo dimensions,85kg.cm stall at11.1V,115200UART; not continuous rating'},{'url':'https://www.hiwonder.com/products/buslinker','use':'USB/UART adapter; verify legacy HTD protocol on sample'},{'url':'https://display.meanwell.com/Upload/PDF/LRS-350/LRS-350-SPEC.PDF','use':'12V29A supply specification; purchase prewired enclosed mains assembly'},{'url':'https://raw.org/research/inverse-kinematics-of-a-stewart-platform/','use':'Rotary crank Stewart inverse-kinematics derivation'},{'url':'https://www.gates.com/content/dam/gates/home/knowledge-center/resource-library/operating-manuals/preventive-maintenance-manual-en.pdf','use':'Toothed inside idler selection; no small smooth backside idler'}],'physical_tests_performed':False,'supplier_quotes_accepted':0},indent=2))

# Local profile coordinates, including distinct rough-cut and finished bores.
profiles=json.loads((v/'profiles.json').read_text())
with (r/'01_Metal/Flat_Profile_Dimensions.csv').open('w',newline='')as f:
 w=csv.writer(f);w.writerow(['part','feature','index','X_mm','Y_mm','finished_diameter_mm','CUT_diameter_mm','thickness_mm'])
 for name,p in profiles.items():
  for k,pt in enumerate(p['outline'],1):w.writerow([name,'closed outline vertex',k,*pt,'','',p['thickness']])
  for k,(x,y,rad)in enumerate(p['holes'],1):w.writerow([name,'hole',k,x,y,rad*2,p.get('cut_holes',p['holes'])[k-1][2]*2,p['thickness']])
  for k,(x,y,rad)in enumerate(p.get('reference_holes',[]),1):w.writerow([name,'REFERENCE inclined tap; do not cut',k,x,y,rad*2,'DO NOT CUT',p['thickness']])
print('Recorded',test_count,'software tests, dry-run, provenance and manufacturing coordinates')

with (r/'03_Purchase/Rubber_Foot_Finishing.csv').open('w',newline='')as f:
 w=csv.writer(f);w.writerow(['feature','centre_X_mm','centre_Y_mm','width_mm','length_mm','depth_from_top_mm','note'])
 w.writerow(['M6 nut recess',-10,-10,18,18,10,'Pattern relative to40x40 foot centre; rotate complete pattern with outrigger'])
 for x,y in((15,15),(0,15),(15,0)):w.writerow(['M5 head notch',x,y,10,10,7,'Additional finishing, not fully modelled in purchased-envelope STEP; verify actual stack'])

# Zero-quantity construction blanks remain reference-only at the final export stage.
import ezdxf
parts=json.loads((v/'parts.json').read_text())
for name,info in parts.items():
 if info['quantity']!=0:continue
 path=r/info['folder']/'DXF'/f'{name}.dxf'
 if not path.exists():continue
 doc=ezdxf.readfile(path)
 if 'REFERENCE'not in doc.layers:doc.layers.new('REFERENCE',dxfattribs={'color':5})
 for entity in doc.modelspace():entity.dxf.layer='REFERENCE'
 doc.saveas(path)
