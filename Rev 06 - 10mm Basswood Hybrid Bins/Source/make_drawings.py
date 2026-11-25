from pathlib import Path
import math,json
import numpy as np,ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];IMAGES=ROOT/'Source/Illustrations'
INK='#173743';TEAL='#087e87';MUTED='#49616d';LINE='#c9d8dc'
PAGES=[]
def text(c,x,y,s,size=10,bold=False,color=INK):
 c.setFillColor(colors.HexColor(color));c.setFont('Helvetica-Bold'if bold else'Helvetica',size);c.drawString(x*mm,y*mm,s)
def line(c,x,y,u,v,color=LINE):
 c.setStrokeColor(colors.HexColor(color));c.setLineWidth(.65);c.line(x*mm,y*mm,u*mm,v*mm)
def geom(path,layer='CUT'):
 d=ezdxf.readfile(path);return [e for e in d.modelspace()if e.dxf.layer==layer and e.dxftype()in ['LINE','CIRCLE','ARC']]
def bounds(es):
 pts=[]
 for e in es:
  if e.dxftype()=='LINE':pts += [list(e.dxf.start)[:2],list(e.dxf.end)[:2]]
  else:pts += [list(p)[:2]for p in e.flattening(.02)]
 arr=np.array(pts);return arr.min(0),arr.max(0)
def draw(c,es,x,y,s):
 lo,hi=bounds(es);c.setLineWidth(.65);c.setStrokeColor(colors.HexColor(INK))
 def tr(p):return((x+(p[0]-lo[0])*s)*mm,(y+(p[1]-lo[1])*s)*mm)
 for e in es:
  if e.dxftype()=='LINE':c.line(*tr(e.dxf.start),*tr(e.dxf.end))
  else:
   center=tr(e.dxf.center);r=e.dxf.radius*s*mm
   if e.dxftype()=='CIRCLE':c.circle(*center,r,stroke=1,fill=0)
   else:c.arc(center[0]-r,center[1]-r,center[0]+r,center[1]+r,e.dxf.start_angle,(e.dxf.end_angle-e.dxf.start_angle)%360)
 return hi-lo

def dim(c,x,y,length,label,vert=False):
 if vert:
  line(c,x,y,x,y+length,MUTED)
  for a in [y,y+length]:line(c,x-2,a,x+2,a,MUTED)
  c.saveState();c.translate((x-2)*mm,(y+length/2)*mm);c.rotate(90);c.setFont('Helvetica-Bold',9);c.setFillColor(colors.HexColor(MUTED));c.drawCentredString(0,0,label);c.restoreState()
 else:
  line(c,x,y,x+length,y,MUTED)
  for a in [x,x+length]:line(c,a,y-2,a,y+2,MUTED)
  text(c,x+length/2-10,y+3,label,9,True,MUTED)

def header(c,title,sub,page):
 line(c,14,282,406,282,TEAL);text(c,14,272,'TRASH BIN PRO MAX / R06 / FOUR MIRRORED BINS',9,True,TEAL);text(c,14,257,title,22,True);text(c,14,247,sub,9,color=MUTED)
 line(c,14,16,406,16);text(c,14,9,'mm | NOMINAL STOCK | CALIBRATE BEFORE FULL CUT | 10 kg PER-BIN DESIGN TARGET',8,True,TEAL);text(c,365,9,str(page),9,color=MUTED)
def notes(c,x,y,lines):
 for s in lines:text(c,x,y,s,10);y-=6
 return y

out=ROOT/'PDF/Dimensioned_Parts_and_Layouts_R06.pdf';c=canvas.Canvas(str(out),pagesize=(420*mm,297*mm));c.setTitle('R06 four-bin dimensions and manufacturing drawings')
page=1;header(c,'Four-bin placement and dimensions','Bin labels are defined by this drawing. Base plate and central platform are existing reference parts; no fabrication files for them are included.',page)
c.drawImage(str(IMAGES/'four_top.png'),15*mm,29*mm,width=210*mm,height=183.75*mm)
# Image top view uses 840 mm image height across 183.75 mm.
s=183.75/840;cx=120;cy=120.875
for bid,sx,sy in [('B1',1,1),('B2',-1,1),('B3',1,-1),('B4',-1,-1)]:text(c,cx+sx*220*s-4,cy+sy*220*s,bid,14,True,TEAL)
dim(c,cx-350*s,cy-350*s-8,700*s,'700 overall');dim(c,cx-350*s-9,cy-350*s,700*s,'700 overall',True)
notes(c,239,227,['TOP VIEW / +X RIGHT / +Y UP','B1: X 2.5..350 / Y 2.5..350','B2: X -350..-2.5 / Y 2.5..350','B3: X 2.5..350 / Y -350..-2.5','B4: X -350..-2.5 / Y -350..-2.5','','All bins: Z 0..450; each 347.5 x 347.5.','Neighboring bins: 5 mm minimum separation.','Exposed curved face: R75 about global origin.','Nominal central reference circle: diameter 150.','Confirmed post: diameter 147.5.','Nominal radial clearance: 1.25.','','Mirror B1 across X=0 for B2; Y=0 for B3.','Mirror both X=0 and Y=0 for B4.','Z and the underside magnet pockets stay down.','','STEP uses these global coordinates.','Cut profiles use the corresponding global U/Z','or X/Y projection; profile position is arbitrary.','Turn parts on the sheet as needed for nesting.','Keep B-prefix and countersink-face labels.','Assembly: inside-wall faces and floor TOP locate.','Outside faces may vary with stock thickness.'])
c.showPage();PAGES.append('Four-bin placement')
for bid,(sx,sy)in {'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}.items():
 for part in ['W01','W02','W03','W04','F01']:
  page+=1;name=f'{bid}_{part}';es=geom(ROOT/'DXF'/f'{name}.dxf');lo,hi=bounds(es);wh=hi-lo;s=min(173/wh[0],190/wh[1]);x,y=36,39
  thickness=10 if part=='F01'else 6
  header(c,name+' / '+('floor'if part=='F01'else'wall'),f'Laser cut once from {thickness} mm basswood plywood. Finished contour, no kerf offset. Native DWG and DXF supplied.',page)
  draw(c,es,x,y,s);dim(c,x,y-7,wh[0]*s,f'{wh[0]:.1f}');dim(c,x-10,y,wh[1]*s,f'{wh[1]:.1f}',True)
  # Unbroken outer edge projection is shown only as a thickness reference.
  line(c,x,26,x+wh[0]*s,26,INK);line(c,x,26+thickness*s,x+wh[0]*s,26+thickness*s,INK);line(c,x,26,x,26+thickness*s,INK);line(c,x+wh[0]*s,26,x+wh[0]*s,26+thickness*s,INK)
  text(c,222,228,'SECONDARY OPERATIONS / PART DATUMS',11,True,TEAL)
  common=[f'Profile envelope: {wh[0]:.1f} x {wh[1]:.1f}; thickness {thickness}.',f'File: DWG/{name}.dwg',f'Solid: STEP/{name}.step','Keep the labeled bin kit together.','Dimensions are finished nominal values.','Use approved samples and measured stock.','Wood joint gap: 0.20 total nominal.','Printed joint gap: 0.30 total nominal.']
  if part=='F01':
   xy=[(sx*100*math.cos(math.radians(a)),sy*100*math.sin(math.radians(a)))for a in [22.5,45,67.5]]
   extra=['','Three M4 holes: diameter 4.5 through.','Countersink underside Z=0: diameter 8 x 90 deg.','Nominal countersink depth: 1.75.','M4 centers X,Y in global coordinates:']+[f'  ({a:.3f}, {b:.3f})'for a,b in xy]+['Four insert holes: diameter 29.6.','Centers: all combinations of signed 102.5,250:',f'  X sign {sx:+d}; Y sign {sy:+d}.','Corner: R75 nominal; three locating tabs.','Bottom wall-tab width 30; depth 10.']
  else:
   scale=sx if part in ['W01','W03']else sy
   centers=[45.5,132.6666667,219.8333333,307]if part in ['W01','W02']else[145.5,226.25,307]
   extra=['','Projection: U='+('global X'if part in ['W01','W03']else'global Y')+'; vertical = global Z.','Vertical joint bands: nominal height 36.','Band centers Z: 45,117,189,261,333,405.','Bottom tab width 30; depth 10.','Bottom tab U centers (global):',', '.join(f'{scale*v:.3f}'for v in centers)]
   if part in ['W03','W04']:
    extra += ['','Three M3 holes: diameter 3.4 through.','Z hole centers: 81,225,369.',f'U hole center: {scale*120.5:.3f}.','Countersink diameter 6.3 x 90 degrees.','Nominal countersink depth: 1.45.','Exterior face: '+(f'Y={sy*2.5:+.1f}'if part=='W03'else f'X={sx*2.5:+.1f}')+'.']
   else:extra+=['','No countersinks in this wall.']
  notes(c,222,219,common+extra);c.showPage();PAGES.append(name)
 # Printed curve reference views.
 page+=1;header(c,f'{bid}_C01 / one-piece PETG curve','Print once using STL/'+bid+'_C01.stl. The STEP includes all fingers, flanges, pads, holes and nut traps.',page)
 es=geom(ROOT/'DXF'/f'{bid}_C01_REFERENCE.dxf','REFERENCE')
 draw(c,es,25,34,.43)
 notes(c,280,226,['Envelope: 130 x 130 x 450.','Outside R75 / inside R81.','Height axis: global Z.','Nominal shell thickness: 6.','Wing finger bands: 36 at 72 pitch.','Z centers: 45,117,189,261,333,405.','','Six M3 through holes and nut traps.','M3 traps: AF5.8 x 2.6 deep.','Flanges: 5 thick behind plywood.','Three M4 floor pads: diameter 20,','8 high, Z10..18; neck width 14.','M4 traps: AF7.2 x 3.4 deep.','Hole axes match this bin floor.','','Views left to right:','XY section Z225; XY section Z13;','XZ elevation (same global axes).','','Use a printer with sufficient Z:','450 plus process allowance.','PETG profile and supports must','be approved by the print operator.'])
 text(c,28,25,'REFERENCE VIEWS ONLY - DO NOT LASER-CUT C01',9,True,TEAL);c.showPage();PAGES.append(bid+'_C01')
page+=1;header(c,'M01 / common magnet-pocket insert','Print sixteen from STL/M01_magnet_insert.stl. Four per bin. Closed roof down on print bed, then flip for installation.',page)
c.setStrokeColor(colors.HexColor(INK));c.circle(90*mm,145*mm,14.6*3*mm);c.circle(90*mm,145*mm,12.6*3*mm);dim(c,46.2,92,87.6,'diameter 29.2');text(c,44,208,'UNDERSIDE / POCKET OPEN',11,True,TEAL)
# section solid walls and roof, 3:1.
c.setFillColor(colors.HexColor('#eaf4f5'));c.rect(170*mm,125*mm,87.6*mm,30*mm,fill=1,stroke=1);c.setFillColor(colors.white);c.rect(176*mm,125*mm,75.6*mm,15*mm,fill=1,stroke=1);dim(c,267,125,30,'10',True);dim(c,176,115,75.6,'25.2 pocket')
notes(c,292,211,['OD 29.2; height 10.','Underside recess:','diameter 25.2 x 5 deep.','Closed roof: 5.','Radial wall: 2.','Floor opening: diameter 29.6.','Epoxy gap: 0.20 radial.','','Pocket opening flush to actual underside.','Level/seal roof for stock variation.','Keep epoxy out of the pocket.','Choose magnets to fit after cure.','Check against the actual base.','Record magnet polarity before','bonding any magnets.','','Reference STEP and DWG included.'])
c.showPage();PAGES.append('M01');c.save()
# Full-size cutter outlines: twenty production profiles and seven plywood coupons.
out=ROOT/'PDF/Full_Scale_Cutting_Profiles_R06.pdf';c=canvas.Canvas(str(out));c.setTitle('R06 full-scale laser-cutting profiles')
items=sorted([p for p in (ROOT/'DXF').glob('*.dxf')if 'REFERENCE'not in p.stem])
for idx,path in enumerate(items,1):
 es=geom(path);lo,hi=bounds(es);w,h=hi-lo;pw=max(w+40,180);ph=h+52;c.setPageSize((pw*mm,ph*mm));draw(c,es,20,27,1)
 stock=10 if path.stem.endswith('F01')or path.stem.startswith(('Q02','Q04','Q07','Q10'))else 6
 text(c,10,ph-9,path.stem+f' | {stock} mm plywood | 1:1 | '+str(idx),9,True,TEAL);text(c,10,ph-16,'CUT contour only. No kerf offset. Verify scale and calibration before full cut.',7.5)
 dim(c,20,12,100,'100 mm SCALE CHECK');text(c,125,10,'ACTUAL SIZE / NO PAGE FIT',7,color=MUTED);c.showPage()
c.save();(ROOT/'Source/drawing_pages.json').write_text(json.dumps({'dimensioned':PAGES,'full_scale':[p.stem for p in items]},indent=2));print('DRAWING PAGES',len(PAGES),'FULL SCALE',len(items))
