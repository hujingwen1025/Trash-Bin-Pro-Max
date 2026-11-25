from pathlib import Path
import json,ezdxf,subprocess,hashlib,shutil,os
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'.build/sample_dwg';WORK.mkdir(parents=True,exist_ok=True);SRC=WORK/'input';BACK=WORK/'roundtrip';SRC.mkdir(exist_ok=True);BACK.mkdir(exist_ok=True)
name='Q10_floor_corner_sample';shutil.copy2(ROOT/'DXF'/f'{name}.dxf',SRC/f'{name}.dxf')
oda=os.environ['ODA_CONVERTER']
for cmd in [[oda,str(SRC),str(ROOT/'DWG'),'ACAD2000','DWG','0','1','*.dxf'],[oda,str(ROOT/'DWG'),str(BACK),'ACAD2000','DXF','0','1',name+'.dwg']]:
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
def key(e):
 typ=e.dxftype();pt=lambda v:tuple(round(float(x),5)for x in list(v)[:2])
 if typ=='LINE':return(typ,*sorted([pt(e.dxf.start),pt(e.dxf.end)]))
 if typ=='CIRCLE':return(typ,pt(e.dxf.center),round(e.dxf.radius,5))
 if typ=='ARC':return(typ,pt(e.dxf.center),round(e.dxf.radius,5),round(e.dxf.start_angle%360,5),round(e.dxf.end_angle%360,5))
 if typ=='TEXT':return(typ,e.dxf.text,pt(e.dxf.insert))
 return(typ,)
a,b=ezdxf.readfile(SRC/f'{name}.dxf'),ezdxf.readfile(BACK/f'{name}.dxf');same=sorted(map(key,a.modelspace()),key=str)==sorted(map(key,b.modelspace()),key=str)
p=subprocess.run(['/opt/homebrew/bin/dwgread','-v0','-O','JSON',str(ROOT/'DWG'/f'{name}.dwg')],capture_output=True,text=True)
ok=same and b.units==4 and (ROOT/'DWG'/f'{name}.dwg').read_bytes()[:6]==b'AC1015'and p.returncode==0 and'ERROR'not in p.stderr
r=json.loads((ROOT/'Verification.json').read_text());label=name+' DWG geometry, units and independent read';r['tests']=[t for t in r['tests']if t['name']!=label];r['tests'].append({'name':label,'pass':bool(ok),'entities':len(a.modelspace())});assert ok
keys=[key(e)for e in a.modelspace()if e.dxf.layer=='CUT'];ok=len(keys)==len(set(keys));label=name+' no duplicate cutter entities';r['tests']=[t for t in r['tests']if t['name']!=label];r['tests'].append({'name':label,'pass':bool(ok)});assert ok
(ROOT/'Verification.json').write_text(json.dumps(r,indent=2));print('Q10 DWG checks passed')
