"""Create the illustrated R07 manual, A3 part sheets and Chinese quote packet."""
from pathlib import Path
import sys,json,csv,math,textwrap,io,os,re
import numpy as np
from PIL import Image as PILImage
import cadquery as cq
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Software'))
from geometry import Geometry,load_config
g=Geometry();cfg=g.c;parts=json.loads((ROOT/'Verification/parts.json').read_text());profiles=json.loads((ROOT/'Verification/profiles.json').read_text())
pdfmetrics.registerFont(TTFont('STSong-Light',os.environ.get('R07_CJK_FONT','/System/Library/Fonts/STHeiti Medium.ttc'),subfontIndex=0))
BLUE=colors.HexColor('#153C53');TEAL=colors.HexColor('#167D8D');RED=colors.HexColor('#9D2828');PALE=colors.HexColor('#EEF4F6')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyR07',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=8));styles.add(ParagraphStyle(name='SmallR07',fontName='Helvetica',fontSize=7.5,leading=10,spaceAfter=5));styles.add(ParagraphStyle(name='CNR07',fontName='STSong-Light',fontSize=10,leading=15,spaceAfter=8,wordWrap='CJK'))
styles['Heading1'].textColor=BLUE;styles['Heading1'].spaceBefore=15;styles['Heading1'].fontSize=17
styles['Heading2'].textColor=TEAL;styles['Heading2'].fontSize=12;styles['Heading2'].spaceBefore=10
styles['Title'].textColor=BLUE
report={}
for f in ['Geometry_Verification.json','Coarse_Verification.json']:
 if (ROOT/'Verification'/f).exists():report=json.loads((ROOT/'Verification'/f).read_text());break
passed=report.get('digital_tests_passed',False)
STATUS='DIGITAL CHECKS PASSED / PHYSICAL PROTOTYPE NOT QUALIFIED'if passed else'ENGINEERING HOLD - DO NOT MANUFACTURE THE FULL SET'

def fit_image(path,width=510,height=440):
 w,h=PILImage.open(path).size;scale=min(width/w,height/h);return Image(str(path),width=w*scale,height=h*scale)

def P(s,style='BodyR07'):return Paragraph(escape(str(s)).replace('\n','<br/>'),styles[style])
def table(rows,widths=None,cn=False,padding=6):
 style='CNR07'if cn else'SmallR07';data=[[P(str(v),style)for v in row]for row in rows];t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('LINEBELOW',(0,0),(-1,0),.7,TEAL),('BOTTOMPADDING',(0,0),(-1,-1),padding),('TOPPADDING',(0,0),(-1,-1),padding)]))
 # Paragraph text color must be set explicitly for colored header cells.
 for cell in data[0]:
  cell.style=ParagraphStyle('header',parent=cell.style,textColor=colors.white)
  for frag in cell.frags:frag.textColor=colors.white
 return t
def footer(c,doc):
 w,h=doc.pagesize;c.setFillColor(BLUE);c.setFont('Helvetica',7);c.drawString(40,24,'TRASH BIN PRO MAX | R07 | mm | 20 NOV 2026');c.drawRightString(w-40,24,f'{doc.page}');c.setFillColor(RED);c.drawString(40,h-24,'PROTOTYPE / PROCUREMENT HOLD UNTIL REQUIRED GATES PASS')
def document(path,story):SimpleDocTemplate(str(path),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
ASSEMBLY_IMAGES={
 4:('Assembly_01_Support.png','Steps 1-4: base, endcaps, steel core and fixed deck. The outer shroud is omitted to expose the structure.'),
 5:('Assembly_05_Pedestal.png','Step 5: align one pedestal set before repeating D1-D6. Numbered leaders identify the individual parts.'),
 6:('Assembly_06_Cranks.png','Step 6: the keyed shaft/hub/crank stack. Muted grey parts show the surrounding pedestal.'),
 7:('Assembly_07_Belt.png','Step 7: belt routing and inside-idler location. This is a pitch-line schematic, not a manufacturing template.'),
 9:('Assembly_09_Motor_Guard.png','Steps 8-9: mount the motor and real horn interface, then the stops and guard. The guard is moved outward for visibility.'),
 10:('Assembly_10_Lower_Joint.png','Step 10: exploded lower joint. Arrows show fork and smooth-tip pivot insertion; the primary crank pin and spacers are purchased hardware.'),
 11:('Assembly_11_Tube.png','Step 11: tube cut length, cross-hole locations and finished link centres. Measure the assembled link after adjustment.'),
 12:('Assembly_12_Upper_Joint.png','Step 12: ball stud, coupler and two identical clamshell halves. The halves separate along their actual socket axis.'),
 14:('Assembly_14_Carrier.png','Steps 13-14: underside of M09 and all six labelled wedge/socket groups. Keep L1-L6 identities when assembling.'),
 15:('Assembly_15_Tray.png','Step 15: carrier, braces, perimeter frame and loading sheet, shown with illustrative exploded gaps.'),
 16:('Assembly_16_Links.png','Step 16 / calibration reference: match L1-D1 through L6-D6. The pictured REST position is not the Step 25 ACTIVE calibration height.'),
 18:('Assembly_18_Frame.png','Steps 17-18: outer frame and triangulated backstop supports. Two front panels are omitted for access; install all four.'),
 20:('Assembly_20_Guide.png','Steps 19-20: one removable guide module. Caps and guide are lifted to show order; all four guides use the same mounting method.')}

def chapter(story,title,steps):
 story.append(PageBreak());story.append(Paragraph(title,styles['Heading1']))
 for heading,body in steps:
  block=[Paragraph(heading,styles['Heading2']),P(body)]
  match=re.match(r'Step(\d+):',heading)
  illustration=ASSEMBLY_IMAGES.get(int(match.group(1)))if match else None
  if illustration:
   filename,caption=illustration
   block.extend([Spacer(1,5),fit_image(ROOT/'Preview'/filename,510,320),P(caption,'SmallR07'),Spacer(1,8)])
   story.append(KeepTogether(block))
  else:story.extend(block)

def manufacture_rows():
 rows=[]
 for name,m in parts.items():
  if not m['quantity']:continue
  process='3D PRINT'if m['kind']=='print'else'LASER + FINISH'if name in profiles and m['material']!='REFERENCE ONLY'else'MACHINE / FORM'
  if name=='M22_Parallel_Key':process='BUY STANDARD'
  if name.startswith('Q'):process='3D PRINT SAMPLE / JIG'
  rows.append({'part':name,'quantity':m['quantity'],'process':process,'material':m['material'],'step':f"{m['folder']}/STEP/{name}.step",'stl':f"{m['folder']}/STL/{name}.stl",'dxf':f"{m['folder']}/DXF/{name}.dxf"if name in profiles else'REFERENCE VIEW ONLY','notes':m['notes']})
 return rows

PURCHASE=[
('HTD-85H servo',6,'Hiwonder HTD-85H, 9-14.8V,240deg legacy UART115200. Manufacturer stall85 kg.cm at11.1V; continuous torque unpublished. One actual sample first.'),
('Matched metal servo horn',6,'Hiwonder HTD-85H metal horn option. Confirm centre screw/spline and hole pattern on sample; M07 is match drilled.'),
('USB half-duplex adapter',1,'Hiwonder BusLinker V3.0 or legacy-compatible transparent UART USB interface; verify HTD 0x55 protocol and readback on one servo. Signal/GND only; separate motor power.'),
('12V supply, prewired enclosed',1,'Mean Well LRS-350-12,12V29A, or enclosed equivalent continuous>=29A with overload protection. Purchase enclosed, earthed, fused mains assembly; do not route power through USB adapter.'),
('DC emergency disconnect',1,'12VDC >=30A contactor/disconnect with NC mushroom stop and deliberate manual restart. It must not re-energize automatically when stop is reset.'),
('Fused star distribution',1,'30A main fuse, six individually fused5A branches. Connector/harness rating>=6A per motor. MainAWG12, branchesAWG18; retain only short factory servo tails.'),
('608ZZ bearing',34,'8x22x7 mm;30 installed plus4 spares. Align bores with dummy shaft before tightening. Supplier actual OD checked with Q01 and first metal cheek.'),
('36T timing pulley',6,'HTD5M,15 mm belt face,8H7 bore with2 mm keyway; pitch diameter57.296, verify flange envelope<=60.'),
('20T timing pulley',6,'HTD5M,15 mm belt face,8H7 bore with2 mm keyway; pitch diameter31.831, verify flange envelope<=36.'),
('Timing belt',6,'360-5M-15,72 teeth. Verify tensioner range on ONE cell before six sets. Do not substitute GT2 tooth profile.'),
('20T toothed inside idler',6,'HTD5M20T,15 mm belt face,flangeOD<=36,bearing-supported8 mm bore. TOOTHED face contact, no reverse belt bending. M8 shoulder spindle and spacer. Supplier drawing and first-cell tooth engagement/tension approval required.'),
('8mm shaft collar',24,'Split clamp type,8 bore,OD<=16,length5.0. Axial retention only; keys carry torque. Confirm installed axial stack before ordering.'),
('Main lower joint shoulder screw',6,'ISO7379 type, smooth shoulder4x40, M3 threaded end; 38 mm outer crank span; two5 mm spacers between cross and crank inner faces; compact washers and M3 nyloc, nyloc nut.'),
('Hard-stop shoulder screw',12,'Smooth shoulder6x60, M5 threaded end, grade10.9 or equivalent. Two4 mm spacers and M5 nyloc per pin. Supported at both cheek ends.'),
('M5 resting threaded rod',3,'Cut to actual pad height from M5 steel stock, 335.6 mm nominal fromZ510 to845.6; trim to actual pad/nut engagement before loading; supplier captiveM5 nuts welded under TOP post cap before core is closed.'),
('2020 extrusion820',4,'20x20 structural aluminium,820 mm, outer frame posts. End tapM5 where indicated; verify4.2 mm core hole.'),
('2020 extrusion710',8,'Outer rails,710 mm; four atZ500 and four atZ800. Reinforced corner brackets both ends.'),
('2020 extrusion320',8,'Backstop uprights,320 mm, fromZ490 to810. End tapsM5 >=15 mm.'),
('2020 extrusion290',4,'Backstop middle rails,290 mm; centresZ640, between uprights.'),
('2020 extrusion92',8,'Guide posts,92 mm, fromfixed deckZ526 to618. TapM5 both ends >=15 mm.'),
('Reinforced2020 angle bracket',56,'Two-hole reinforced metal type,32 for outer rails,16 for backstop middle rails,8 for outer post feet. Holes match M5T-nuts. Supplier sample required.'),
('M5 2020T-nut',168,'Required allocation152 plus16 spares; match actual extrusion slot profile. Includes panel and bridge connections.'),
('M5x10/M5x12 screws',160,'Frame brackets, panels and short bridges; check actual bracket thickness, use washers and adequate thread engagement.'),
('M5x20 screws/studs',40,'Long bridge stack and guide connections. Guide: eightM5x20 studs, ten mm into profile +2 mm cap roof +8 mm brass insert.'),
('M5 removable thumb screw',8,'Two under-deck fasteners per guide module. Length deck6 plus10 mm profile engagement; do not bottom in extrusion.'),
('M6 post mounting set',12,'SixM6x30 bottom, sixM6x25 top, washers/nyloc. Confirm installed stack; torque against steel backing surfaces without crushing wood.'),
('M6x35 flat-head set',16,'Four per outer frame outrigger, flush at base upper surface. Matching nyloc and washers below steel plate. Rubber foot nut reliefs required.'),
('M4 cradle screws/nuts',24,'M4x20 starting length;6 mm deck +6 mm tab +compact washer/nyloc. Right holes8/15 are7 mm apart: use heads and washersOD<=7, not wide washers; confirm sample stack. No protruding tips in servo housing.'),
('M3 crank hub screws',48,'M3x10 with1 mm washer. Four at each side of each hub. >=3 mm steel engagement, torque and threadlocker as guide.'),
('M3x35 guard screws',12,'Two per guard, into tapped rear cheek. Check that screw ends do not reach a bearing.'),
('M3x30 socket screws',12,'Trim to drawing/actual tilted socket stack; thread into angled carrier M3 taps >=4 mm; tips below carrier upper face.'),
('M3 tray fasteners',28,'EightM3x16 roots; twentyM3x10 for outer braces/perimeter; low flush heads, washers/nyloc. Countersink assembled metal stack.'),
('M3 tube retaining pins',12,'M3x20 with washers/nyloc. Static pins, not rotary pivots; smooth portion across tube preferred.'),
('Heat-set inserts',26,'12xM3x4x4.6OD;6xM4x8x6OD;8xM5x8x7OD. Buy spares. Fit samples govern pilot bores before printing full sets.'),
('M5 cell foot bolts',72,'M5x20/25 for36 cheek-to-angle connections and36 foot-to-deck connections. Washers/nyloc, verify actual stack, no contact with moving crank. Add12M5 tensioner pivot/clamp sets with washers; clamp hole match-drilled on first cell.'),
('8mm shaft spacers',1,'Machine/select axial shims to actual sample stack: typical3.5 mm at crank/bearing gaps and5.5 mm pulley/bearing gap, ID8.2 OD<=11.5. Record measured gaps; collars5 mm wide. Do not preload bearing outer rings through shaft spacers.'),
('Bearing retaining compound',1,'Removable retaining compound suitable22H7 aluminium/steel seats, e.g. a supplier-approved removable retaining grade according to its cure/cleaning instructions. Confirm200 N axial sample retention and service temperature; no glue in bearing.'),
('Cable anchor hardware',1,'Three captiveM3 nuts under TOP cap, threeM3x16 lower anchor screws, threeM3x8 carrier anchors with DIN439 thinM3 nuts1.8 mm thick and threadlocker; keep bolt tips at/below jointZ20 to clear brace undersides20.5. Verify actual eye/washer stack. Use suitable rated flat eye terminals and broad washers. Carrier anchor screws enter from below and finish below tray. Verify all450 mm cables stay slack but cannot enter links. Restrained catch test required.'),
('Lower joint spacers',12,'4.2ID x8OD x5 long, one each side of each P02 cross; smooth4x40 shoulder pin spans38 mm crank outer faces. Measure washer/thread lengths on first joint.'),
('Jam nuts / assorted washers',1,'12M3 pivot jam nuts,6thinM4 stud jam nuts,12M5 pad/captive nuts,24 hard-stop4 mm spacers;3.5 mm tray root spacers x8; blue medium threadlocker.'),
('Safety retention cables',3,'2 mm stainless cable with rated swaged eyes, each working load>=500N; nominal450 mm eye-to-eye, physical slack routing check required. Central anchors only; no cables across dump paths.'),
('EVA impact liner',4,'20 mm thick,358x298, bonded onto bin-facing backstops; resilient/damped, replace if cut or permanently compressed. Physical impact trial required.'),
('Chute sliding liner',4,'0.3 mm PET/PP sheet, smooth edges, bonded flush without lips. Measure actual chute after printing.'),
('Rubber support blocks',4,'40x40x20, rated>=250N each, one18x18x10 nut relief at local(-10,-10), plus three10x10x7 head reliefs at(15,15),(0,15),(15,0), relative to block centre; rotate with outrigger. See Rubber_Foot_Finishing.csv. Keep bottom below central nuts/backplate; installed under outriggers.'),
('Bin-bottom impact liner samples',4,'Begin with150 mm supplier-selected energy-absorbing cushioning and a thin HDPE load spreader, trimmed to actual R06 interior. Request drop/energy data. Grade/thickness are NOT qualified; progressive2 kg routing and empty/part-filled bin tests must show no bottoming, floor/joint damage or escape before any full purchase.'),
('Calibration tools',1,'Caliper,0.1deg inclinometer,0-100N spring scale, multimeter, torque tools; borrowed tools excluded from mechanism budget.')]

def write_tables():
 out=ROOT/'03_Purchase';out.mkdir(exist_ok=True)
 rows=manufacture_rows()
 with (ROOT/'Manufacture_List.csv').open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 with (out/'Purchase_List.csv').open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.writer(f);w.writerow(['item','required_quantity','specification','supplier_quote_CNY','quote_status']);w.writerows((a,b,d,'','NOT QUOTED')for a,b,d in PURCHASE)
 allocations=[('Six servos and matched horns',1300),('All custom metal and post work',700),('Printing and sliding liners',230),('Bearings, belts, pulleys, keys and collars',260),('External frame and backstop material',220),('Power, control, wiring and emergency disconnect',200),('Fasteners, foam and cables',90)]
 with (out/'Budget_Quote_Check.csv').open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.writer(f);w.writerow(['group','maximum_allocation_CNY','accepted_quote_CNY','status']);w.writerows((a,b,'','UNVERIFIED ALLOCATION, NOT PRICE')for a,b in allocations)
 (out/'Procurement_Status.json').write_text(json.dumps({'cap_CNY':3000,'allocated_CNY':sum(v for _,v in allocations),'accepted_quotes':0,'purchase_release':False,'reason':'No accepted regional supplier quotes; external frame and machined interfaces may exceed allocations. Do not buy full set. All quote fields are unaccepted; currency conversions are not local supplier quotes.','source':'https://www.hiwonder.com/products/htd-85h'},indent=2))

def make_guide():
 story=[Paragraph('Trash Bin Pro Max',styles['Title']),Paragraph('R07 servo Stewart sorter',styles['Heading1']),P('Illustrated manufacturing, purchasing, assembly and commissioning guide | Visual update A'),P(STATUS)]
 if (ROOT/'Preview/Complete_System.png').exists():story.extend([fit_image(ROOT/'Preview/Complete_System.png',510,355),Spacer(1,10)])
 story.extend([P('2 kg payload target | Four55 degree dump poses |750 mm external frame | R06 bins retained'),P('This package is a prototype engineering release. A CAD calculation is not a physical fit, strength, heat or routing test. The original R06 bin manufacturing package remains separate. Purchase release is blocked until quotations satisfy the hard3000 CNY cap and the required gates below pass.')])
 chapter(story,'1. Read this before ordering',[
 ('Release status',STATUS+'. Read Verification/Geometry_Verification.json (or the clearly identified coarse report) and the issue list. Any failed interference/export test blocks full fabrication. Do not hide failed tests by using earlier exports. Physical tests performed: NONE.'),
 ('What the mechanism does','One item rests on the level tray. The mechanism lifts off three resting pads, moves toward the chosen quadrant and tilts up to55 degrees. Short chutes and padded backstops contain the discharge. After the tray is visually or independently confirmed empty, it returns to the supports. This uses a controlled gravity discharge.'),
 ('Item and loading limits','At most2.00 kg per item, bottles laid flat up to320 mm long and100 mm diameter, paper balls up to120 mm. Keep hands out of the mechanism. Set items down gently on the level tray; free-drop loading is unqualified. Start commissioning with empty bottles and small weights. Wet, sticky or sharp objects and uncontained liquids are outside initial qualification.'),
 ('Budget hold','3000 CNY is a HARD LIMIT. Purchase_List.csv contains required specifications, not accepted quotes. Budget_Quote_Check.csv contains allocation targets only. The independent750 mm frame is necessary for overshoot containment and may make the current design exceed those allocations. Obtain itemized quotations; if the total exceeds3000, report the gap and revise scope/parts before ordering. Nothing has been purchased.')])
 chapter(story,'2. File map and repeat ordering',[
 ('Use individual part files','01_Metal contains manufactured metal STEP/STL and applicable1:1DXF/DWG.02_Print contains PETG/TPU parts and jigs.03_Purchase contains supplier-envelope references and purchasing tables.04_Assembly contains level, four dump poses, complete system and exploded references. Never print an assembly STL as one solid.'),
 ('Files to laser cut','Send metal files to a metal fabrication shop with fibre laser/waterjet/CNC, reaming, machining and welding capability. Cut only CUT-layer contours (DRILL on the BASE template), in millimetres at1:1. REFERENCE is never a cutting layer. Precision cutting profiles leave0.5 mm diametral stock:21.5 to22H7 for bearings and7.5 to8H7 for crank shafts; STEP shows final sizes. BASE_Drill_Template is a modification template, not a replacement base outline. M09 joint tap locations are REFERENCE: machine/tap them on their tilted axes after cutting. Ream H7 bores after rough cutting. Apply measured kerf compensation ONCE.'),
 ('Files to machine or form','Tube, shaft, ball stud, keyed hub, adapter, formed brace and perimeter frame require machining/forming operations described in their notes. Their DWGs may be reference projections. Never treat a shaft projection or a curved-part view as a laser pattern. The shop must approve one bend sample for M11 and one matching servo/horn interface before production.'),
 ('Repeat parts','Manufacture_List.csv is the quantity authority. RearM05 cheeks are common x6; FRONTM05 andM17 variants are labelledD1-D6 because their stop bores differ. Do not order zero-quantity blanks in addition to finished variants. Six link tubes are identical. Four backstop panels, four guides and all24 keys are repeated parts. P09 wedges and Q02 stop jigs retain theirL/D labels.')])
 story.extend([PageBreak(),Paragraph('How to read the assembly illustrations',styles['Heading1']),P('Use the numbered leaders and part IDs together with the colours. The same component family keeps its colour across the platform views and assembly close-ups. Existing or surrounding parts are faded grey in detail views. Colours do not specify a material or finish.'),fit_image(ROOT/'Preview/Colour_Key.png',510,250),P('Arrows show insertion or the direction in which an exploded part closes. Exploded gaps are illustrative, not spacer dimensions. Some views omit surrounding parts to expose a joint; the caption states what is hidden. STEP, the manufacturing tables and the written dimensions remain the authority. This visual update changes no geometry, tolerances, quantities or commissioning limits.')])
 story.append(table([['Assembly stage','Illustrated after step']]+[[caption.split(':')[0],str(step)]for step,(filename,caption)in ASSEMBLY_IMAGES.items()],[405,110]))
 story.extend([PageBreak(),Paragraph('Assembly reference views',styles['Heading1']),fit_image(ROOT/'Preview/Exploded_Assembly.png',510,330),P('Exploded platform layers: fixed deck, six drive cells, six links, carrier, four braces/perimeter frame and loading sheet. Guides and the external frame are omitted from this view. Use the numbered part key to follow the stack.'),fit_image(ROOT/'Preview/Mechanism_View.png',510,225),P('Internal mechanism: loading sheet, discharge guides and outer frame hidden to expose the coloured drive cells, six links and carrier. Hidden parts remain required.')])
 chapter(story,'3. Manufactured parts',[])
 story.append(P('Coordinate authority: STEP and the CSV dimensions govern; PDF views are reference views, not1:1 cutting patterns. Each flat profile has a local outline/hole table in01_Metal/Flat_Profile_Dimensions.csv. Finished bearing bores are22H7; ream after welding and rough cutting.'))
 story.append(table([['Part','Qty','Process / material']]+[[r['part'],r['quantity'],r['process']+'; '+r['material']]for r in manufacture_rows()],[235,30,250]))
 chapter(story,'4. Purchased components',[])
 story.append(table([['Item','Qty','Required specification']]+[[a,b,d]for a,b,d in PURCHASE],[125,30,360],padding=4))
 chapter(story,'5. Fit samples before full fabrication',[
 ('GateA: real servo and metal sample','Buy ONE HTD-85H with its matched metal horn and ONE set of bearings, pulleys and belt. Compare the actual housing with the manufacturer reference drawing. Verify voltage, HTD protocol readback and uncoupled direction. Match-drill M07 only after that sample is present. Confirm pulley/key dimensions and shaft-collar envelope.'),
 ('GateB: printed interfaces','Print Q01, one P02/P03/P05 set, twoP04 halves and one representativeP09. Check actual insert pilots,8.2 mm tube socket,16.3 mm ball cavity,20.4 mm extrusion cap and all pin fits. Ream pin bores, do not force them. A joint must rotate through its demanded cone without a neck, bolt or print layer binding.'),
 ('GateC: one cell and rod','Machine one bearing/hub/shaft/crank cell. Align all bearing seats using a straight8 mm dummy shaft; tighten feet only after shafts turn freely. Build one complete297.080 mm centre-to-centre rod, verify its pins and jam nut, and carry out the200 N axial proof test described later. Reject cracked or permanently distorted prints.'),
 ('Stock and allowances','General noncritical metal tolerance+/-0.2 mm; shaft length+/-0.1; link centres+/-0.2; bore/shaftH7/h6 as called out. Printed working gaps are explicit in the CAD, not press fits. Actual stock and supplier process must be measured. R06 plywood coupons and its own10 kg bin tests remain necessary independently.')])
 chapter(story,'6. Printing and finishing',[
 ('Materials and orientation','Use dry PETG for structural housings, forks, sockets, wedges, caps, guards and guides. Use TPU95A for resting pads only. Do not substitute PLA for loaded joints. Joints, crosses, couplers and wedges: solid infill, six or more perimeters,0.2 mm layers; orient pin loads across several continuous perimeters. Remove supports from every moving cavity.'),
 ('Large guides','Print each P06 as one piece on a machine whose usable volume and chosen orientation fit the exported envelope. The floor is3 mm thick NORMAL to its slope, with underside stiffeners. Do not scale the STL to fit a printer. Inspect complete extrusion paths and support removal before accepting a quote. Smooth the sliding face and install the thin PET/PP liner with flush taped edges.'),
 ('Spherical sockets','Inspect both clamshell lips under magnification; no split layers, sharp burrs or exposed infill. Trial the actual polished16 mm steel stud in the two halves before installing. The ball must swivel freely with the retaining lips intact. Lubricate sparingly without contaminating the tray. Qualify the complete joint under load; CAD clearance alone does not establish printed strength.'),
 ('Do not force assembly','A shaft, key, pin or tube should seat with the specified clearance. Forcing an undersized print can create an invisible layer crack. Measure the failed interface, correct the relevant source dimension, regenerate both mating files and rerun checks; never sand a load-bearing lip until it no longer retains the ball.')])
 chapter(story,'7. Base and steel central support',[
 ('Step1: prepare the base','Use the supplied700x700x20 mm base. The centre pocket is147.7 mm diameter and12.5 mm deep, leaving7.5 mm under it. The post147.5 mm diameter therefore has only0.1 mm nominal radial pocket clearance. Trial this fit before finishing; the separate bin curves provide1.25 mm nominal radial clearance. Do not confuse those two fits.'),
 ('Step2: drill and reinforce','Centre the base template on the existing pocket and drill six6.6 mm through holes on100 mmPCD. Fit the steel underside backplate. For the outer frame, drill its sixteen markedM6 holes and countersink for flush upper heads; no screw may protrude beneath a bin. Use40x40x20 blocks centred atX/Y+/-350, with an18x18x10 recess aligned to the nearby340/340 bolt; trial all four rotations. Add three10x10x7 mm M5-head notches at local(15,15),(0,15),(15,0); these finishing reliefs are additional to the simplified purchased-envelope STEP. Cut nut reliefs in the rubber blocks and check all underside hardware clears the floor.'),
 ('Step3: fabricate the post','Weld the60ODx3 steel core to two6 mm endcaps, maintaining512.5 mm total height. Before closing the TOP cap, weld in three captiveM5 nuts for the resting rods and three captiveM3 nuts for the retention anchors. Deburr, coat and inspect the welds. Seat the lower cap atZ7.5; installed top isZ520. The rolled0.8 mm outer shroud preserves147.5 mm OD with a BUTT seam and the15x490 mm internal splice; no external overlap is allowed in the147.7 pocket. Leave removable access before final bonding.'),
 ('Step4: mount the fixed deck','Bolt the post through the base and backplate. Weld all six M28 underside ribs to M08 in a flat jig before final holes/reaming; radius75..215 andZ500..520; use the six installed angles inconfiguration.json/assembly transforms to keep ribs clear of all bolt heads. Inspect welds and flatness. Mount the fixed actuator deck directly atZ520, with pedestal feet on itsZ526 top. Tighten against metal backing surfaces and check that the wooden pocket floor is not crushed. Install the three resting rods before the six cells obstruct access. No post spacers from an earlier draft are used.')])
 chapter(story,'8. Build each servo cell',[
 ('Step5: label and align the frame','BuildD1-D6 using the matching FRONT cheek and auxiliary front cheek; the rear blank is common. Fit three M14 angle feet per cell. The tall bearing stands keep the fixed deck below the crank sweep. Assemble with bolts loose, align using dummy shafts, then tighten evenly. Both input/output bearing bores are22H7 for608ZZ bearings.'),
 ('Step6: keyed shafts and cranks','Fit the two keys on each output shaft, the steel double crank hub and the paired crank plates. The100.5 mm dimension is shaft centre to joint centre. Attach each crank plate with fourM3 screws to its own hub face; keep sufficient steel thread engagement. The key transmits torque; collars retain axially. Never rely on a grub screw alone.'),
 ('Step7: input stage','Fit the input shaft, its two keys and20T pulley; the output receives36T. Install the360-5M-15 belt and adjustable20T toothed INSIDE idler. Use the belt supplier tension specification and the single-cell load test; do not apply an arbitrary deflection force. Nominal idler centre50.3/-44 relative to output, pivot40/-74. Match-drill the clamp only after sample tensioning. Excess tension can damage bearings.'),
 ('Step8: motor and adapter','The motor is below the crank to clear the lower motion envelope. Clamp it in P01 using thin rubber lining and two metal straps. Match-drill the adapter to the real metal horn and keep the original horn centre screw. Trial the entire axial stack with actual collars, keys and horn screws. Record the measured motor direction; the supplied directions are starting calibration data.'),
 ('Step9: mechanical stops and guards','Use the drive-specificQ02 jig to match-drill both supported stop bores. Install the diameter6 shoulder stops with the specified spacers/nuts; confirm the crank touches a stop before a joint or shaft binds. Fit P10 guards before any powered linked test. Check full turn freedom with power disconnected and no loaded tray.')])
 chapter(story,'9. Assemble the six links',[
 ('Step10: lower universal','Fit the rounded P02 cross between the two crank ends with the4 mm smooth shoulder pin. Place a5 mm spacer on each side of the cross, then install P03 around the cross using the two smooth-tipM3 pivots. Engage each tip2.5 mm into its blind seat and lock the outer jam nut while keeping the cross free. The primary through-pin and secondary blind pivots must not intersect.'),
 ('Step11: tube retention','Cut each8ODx1 aluminium tube to the current drawing length (centre length minus48 mm). Cross-drill3.2 mm at18 mm from each end and deburr the inside. Lower tube-end offset is22 mm; upper offset26 mm. Fit both ends and retain with transverseM3 pins. Glue is not a substitute for those pins.'),
 ('Step12: upper spherical end','Fit theM4 brass insert in P05, screw in the polished steel ball stud and secure the thin jam nut. Maintain at least8 mm metal-thread engagement. Adjust and measure the complete link to297.080+/-0.20 mm centre to centre. Keep all six measured lengths in the calibration record. Enclose each ball in its two P04 halves.')])
 chapter(story,'10. Upper carrier and tray',[
 ('Step13: socket wedges','KeepL1-L6 wedge labels. Their flat faces meet the carrier underside; their other faces follow the socket orientation. Machine the carrier M3 holes on the supplied tilted axes listed in01_Metal/Carrier_Joint_Hole_Axes.csv after laser cutting, using bushings/jigs or a tilting fixture. Do not laser the reference circles as vertical holes. Screw tips must remain below the carrier upper face.'),
 ('Step14: fasten the sockets','Fit the two long screws through each socket and wedge into the carrier taps. Trim fromM3x30 stock to the actual stack using Carrier_Joint_Hole_Axes.csv, with at least4 mm engagement and no protrusion toward the tray. Use medium threadlocker and approximately0.3 Nm on these small aluminium taps; do not apply the higher general steel-joint torque. Verify free articulation again after tightening.'),
 ('Step15: stiffen the tray','The1 mm tray requires ALL four formed U-channel braces and the closed15x15x1 perimeter frame. Make one bend/weld sample first. Fit the carrier/brace spacers and countersink through the assembled sheet/support stack for flush heads. No protruding fastener or liner lip may catch a paper ball. Check the complete moving assembly against the1.3 kg allowance.'),
 ('Step16: resting pads and retention','Adjust three resting pads so the unloaded tray is level without twisting it. Recess metal nuts below the TPU contact surface. Keep servos powered while a load is present: the small central pads do not passively support every off-centre2 kg load. Fit three rated450 mm retention cables at the central anchors only, rotated60 degrees from the rest rods. Check their slack through every pose without crossing a leg or discharge path; no cable is a guarantee of safe power-loss behaviour until a restrained catch test passes.')])
 chapter(story,'11. Outer backstop frame and guides',[
 ('Step17: build the750 mm frame','Attach the four identical steel outriggers under the original base. Posts are centred atX/Y+/-365 and rise820 mm. Fit710 mm side rails atZ500 and800, with inward-facing reinforced corner brackets. Square both levels before tightening. The frame adds25 mm beyond each side of the original base.'),
 ('Step18: mount the padded panels','Fit320 mm backstop uprights fromZ490 to810 and their290 mm middle rails atZ640. Short bridges connect to the nearest outer rail. One long bridge per panel at each level triangulates the assembly; stack it with the short bridge and use3 mm outer spacers. Do not omit this anti-racking connection. Bolt the2 mm panels to the front slots, then bond the20 mmEVA liner.'),
 ('Step19: fit guide modules','Each guide sits on two92 mm posts with aligned radial/tangent cap faces. UseM5 end taps and studs, notM4 taps in a4.2 mm extrusion core. The blind inserts are approached from below. Remove a complete guide/post module using its two underside thumb screws whenever additional bin-lifting clearance is needed.'),
 ('Step20: check the discharge envelope','Guide inletR200/Z750, kneeR240/Z630, outletR254/Z480; bin rimsZ470. The padded backstop inner face is nearR280, its metal planeR300, and its topZ800. It catches overshoot that a short chute alone cannot contain. Rotate the largest laid-flat bottle through several orientations with power off; any bridging or snag must be corrected before loaded motion. Remove bins along a clear side path beneath the lower outer rails.')])
 chapter(story,'12. Wiring and emergency controls',[
 ('Step21: power distribution','Use a prewired enclosed12 V supply and a separately powered Pi. Run a fused star supply to each servo; the factory daisy-chain connectors must not carry the combined six-motor current. The USB adapter carries data/common ground only. Verify pin labels from the actual servo/adapter documentation before connecting12 V.'),
 ('Step22: emergency disconnect','The physical stop must interrupt motor DC power through a suitably rated contactor/disconnect. A small pushbutton is not a30 A power switch. Resetting the stop must not restart motion. Protect wiring, strain-relieve cables and keep flexing wire away from cranks and chute edges. Have the vendor supply the mains enclosure already assembled and earthed.'),
 ('What software faults do','Motion polling rotates two read transactions per50 ms frame: per-motor position about0.3 s, temperature/voltage about0.6 s. Full readback occurs before/after timed segments; qualify actual USB timing. The program latches faults and stops issuing new motion; it holds the last commanded positions while power remains. It does NOT guarantee a safety-rated torque-off. A host crash can leave servos holding. The operator must support/restrain the tray and use the independent DC stop for a jam, overheating or unsafe movement. Initial commissioning is attended only.')])
 story.append(fit_image(ROOT/'Preview/Wiring_Diagram.png',510,330))
 chapter(story,'13. Calibration and software',[
 ('Step23: install on the Pi','Use Python3.11 or newer. From Software, create a virtual environment and install requirements.txt. Run python sorter.py simulate first. It sends no hardware commands. Run python -m unittest discover -s tests -v to reproduce software tests.'),
 ('Step24: identify one uncoupled servo','Disconnect every other servo and remove links. Example: python sorter.py set-id --port /dev/ttyUSB0 --id 1 --new-id 2 --only-one-servo --links-disconnected --arm --confirm-clear . Use spaces between option and value (--id 1, --new-id 2). Assign IDs1-6 one at a time; power-cycle and verify readback. Then run probe.'),
 ('Step25: record mechanical zero','With links disconnected, command each motor to its listed active-pose reference angle, using calibrate-angle and the required confirmation flags. Fit the crank to the specified reference angle, verify its direction with a tiny uncoupled move, then support the level carrier at the active-height fixture. Attach links without force. Correct actual zero offsets; only then set calibrated=true in a copy of configuration.json.'),
 ('Step26: attended commissioning','Run dump --bin B1 --port /dev/ttyUSB0 --commissioning --arm --confirm-clear, initially unloaded and at doubled segment times. The program asks you to confirm EMPTY before it returns. Unknown startup poses, missing status replies, temperature>=55 C, voltage outside10.5-12.6 V, tracking errors or a bridged item block further motion. Never bypass a fault to force a home move.'),
 ('Later AI integration','The Python Controller exposes home and dump(B1-B4). Supply an independent empty_check callback before automatic return. Camera inference and hand-presence validation are not implemented in this motion package. Destination mapping isB1 +X/+Y,B2 -X/+Y,B3 +X/-Y,B4 -X/-Y. Physical qualification stays false until the following tests are recorded.')])
 story.append(table([['Drive','Base anchor XYZ global (mm)','Crank alpha active (deg)','Servo reference (deg)']]+[[f'D{i+1}',', '.join(f'{x:.3f}'for x in(g.B[i]+[0,0,cfg['crank_axis_global_z_mm']])),f'{np.rad2deg(g.reference_alpha[i]):.4f}',str(cfg['servo_zero_deg'][i])]for i in range(6)],[40,215,130,130]))
 chapter(story,'14. Physical acceptance and test record',[
 ('Single-component proof','Proof one complete printed rod/joint assembly at200 N axial for60 s in a restrained fixture. No cracking, disengagement or more than0.2 mm permanent length change. Test one drive at the calculated working/factored torque, with angle/temperature readback and guarded belt. Check stop pins and keys for permanent movement. A failed sample blocks the other five sets.'),
 ('Unloaded and incremental loads','Run ten unloaded full cycles in each direction, then0.25,0.5,1 and2 kg. Test the marked centre and conservative off-centre positions with secured test weights. Watch clearance throughout transitions, not just endpoints. Require repeatable return to level, no loose fasteners, no tooth skipping, no joint binding and no permanent structural deformation. Measure the six shaft-centre positions relative to the post under2 kg; elastic change must be less than1 mm and no part may consume its measured running clearance.'),
 ('Thermal duty','At the intended maximum ambient temperature (test at30 C minimum), run30 cycles at the30 s minimum cycle interval with the2 kg test load. All motors must stay below55 C, voltage inside limits, and tracking within5 degrees. The last ten cycles must show a temperature rise of no more than2 C. If heat keeps rising, the mechanism is NOT qualified: improve the drive/duty and repeat; do not silently lower payload.'),
 ('Impact and routing','Fit and qualify removable bottom cushioning/load spreaders in the R06 bins before unsecured heavy-object trials.150 mm is a starting sample thickness, not a validated cushion specification. Check empty and part-filled bins and inspect floors/joints after every increment. Static10 kg bin capacity does not prove drop-impact capacity. Use the independent backstop frame with restrained cabinet and energy-absorbing pads. Test real largest bottles, paper and representative loads in several orientations, including transverse and diagonal bottles. Require20 consecutive correct discharges per bin (80 minimum), no escape, bridging, rebounds into another bin or contact with a servo. Record item, mass, orientation and destination for every trial.'),
 ('Power-loss and removal','With the tray restrained by a secondary test fixture, cut DC power at level, mid-tilt and dump poses, first unloaded then progressively loaded. Verify stops/catches contain motion and no component detaches. Check bin removal with guides disconnected as necessary. These tests are not performed by CAD software.'),
 ('Release record','Only after geometry, sample fits, structural/load, thermal, routing and restrained power-loss tests pass may physical_qualification_passed become true. Record the actual weighed moving mass, servo serial numbers, temperatures, stock measurements, final calibration, revisions and quote total. Retain failed results as evidence.')])
 chapter(story,'15. Verification results and limitations',[])
 sw=json.loads((ROOT/'Verification/Software_Verification.json').read_text());dw=json.loads((ROOT/'Verification/DWG_Verification.json').read_text());story.append(P(f"Recorded checks: {len(report.get('tests',[]))} CAD/engineering checks, {report.get('sampling',{}).get('collision_poses','?')} distinct sampled solid poses, {sw['tests_run']} software tests using a simulated bus/clock, and {len(dw['tests'])} independently read/round-tripped DWGs. These are digital results."))
 story.append(P('Digital status: '+str(report.get('digital_tests_passed','not run'))+'. Physical tests performed: false. All price fields remain unquoted.'))
 if report.get('loads'):story.append(table([['Calculated quantity','Value']]+[[k,str(v)]for k,v in report['loads'].items()],[240,275]))
 failed=[q for q in report.get('tests',[])if not q['pass']]
 if failed:story.append(table([['FAILED CHECK - manufacturing blocked']]+[[q['name']]for q in failed],[515]))
 if report.get('collisions'):story.append(P('The complete collision list is in Verification. Examples: '+ '; '.join(f"{q['pose']}: {q['part_a']} / {q['part_b']}"for q in report['collisions'][:12])))
 story.append(P('Kinematics are not a dynamic trash-contact model. Plywood grade, printed anisotropy/creep, actual servo continuous torque, supplier horn geometry, cable routing and real friction require physical verification. No component has been physically manufactured or load-tested in this chat.'))
 story.append(Paragraph('Source documents',styles['Heading2']))
 for s in ['https://www.hiwonder.com/products/htd-85h','https://www.hiwonder.com/products/buslinker','https://raw.org/research/inverse-kinematics-of-a-stewart-platform/','https://www.gates.com/content/dam/gates/home/knowledge-center/resource-library/operating-manuals/preventive-maintenance-manual-en.pdf','https://display.meanwell.com/Upload/PDF/LRS-350/LRS-350-SPEC.PDF','R06 manufacturer package and the three supplied STL files listed in Reference Inputs']:story.append(P(s,'SmallR07'))
 document(ROOT/'PDF/Manufacturing_and_Assembly_Guide_R07.pdf',story)

def make_drawings():
 path=ROOT/'PDF/Dimensioned_Parts_R07.pdf';can=canvas.Canvas(str(path),pagesize=landscape(A3));W,H=landscape(A3)
 # Overall dimensions accompany the individual local manufacturing views.
 can.setFillColor(BLUE);can.setFont('Helvetica-Bold',18);can.drawString(38,H-40,'R07 overall arrangement | mm | prototype')
 for fname,x,y,w,h in [('Top_View.png',40,430,520,312),('Front_View.png',620,430,520,312),('Right_View.png',40,105,520,312),('Mechanism_View.png',620,105,520,312)]:
  im=ROOT/'Preview'/fname;iw,ih=PILImage.open(im).size;scale=min(w/iw,h/ih);can.drawImage(str(im),x,y,width=iw*scale,height=ih*scale,mask='auto')
 can.setFont('Helvetica',10);can.drawString(40,60,'Original base700 x700 x20. Outer frame750 x750. Post147.5 OD x512.5. Shaft axesZ640. Level trayZ858.6.')
 can.drawString(40,42,'55 degree dump,85 translation. R06 bin rimZ470. Dimensions are nominal; physical qualification and quote gates remain open.');can.showPage()
 for page,(name,m)in enumerate((q for q in parts.items()if q[1]['quantity']>0),1):
  can.setFillColor(BLUE);can.setFont('Helvetica-Bold',18);can.drawString(38,H-40,name);can.setFont('Helvetica',10);can.drawString(38,H-60,f"R07 | {m['material']} | QTY {m['quantity']} | mm | PROTOTYPE")
  shape=cq.importers.importStep(str(ROOT/m['folder']/'STEP'/f'{name}.step')).val()
  for (title,direction),(x,y)in zip([('TOP',(0,0,1)),('FRONT',(0,-1,0)),('RIGHT',(1,0,0)),('ISOMETRIC',(1,-1,1))],[(40,430),(590,430),(40,170),(590,170)]):
   svg=cq.exporters.getSVG(shape,{'width':666.6667,'height':313.3333,'marginLeft':24,'marginTop':24,'projectionDir':direction,'showAxes':False,'showHidden':False,'strokeWidth':-1.0})
   # Match the dimension extension lines to the true projected envelope.
   if title!='ISOMETRIC':
    bb=m['bounds'];size=np.array([bb[k+3]-bb[k]for k in range(3)]);basis=gp_Ax2(gp_Pnt(),gp_Dir(*direction))
    xd=basis.XDirection();yd=basis.YDirection();dx=np.abs([xd.X(),xd.Y(),xd.Z()])@size;dy=np.abs([yd.X(),yd.Y(),yd.Z()])@size
    scale=float(re.search(r'scale\(([^,]+),',svg).group(1))*.75
    left=x+18;right=left+dx*scale;top=y+235-18;bottom=top-dy*scale;dimy=bottom-12;dimx=left-12
    can.setStrokeColor(TEAL);can.setLineWidth(.5);can.line(left,dimy,right,dimy);can.line(dimx,bottom,dimx,top)
    for xx in(left,right):can.line(xx,bottom-3,xx,dimy-3);can.line(xx-2,dimy-2,xx+2,dimy+2)
    for yy in(bottom,top):can.line(left-3,yy,dimx-3,yy);can.line(dimx-2,yy-2,dimx+2,yy+2)
    can.setFillColor(TEAL);can.setFont('Helvetica',8);can.drawCentredString((left+right)/2,dimy-10,f'{dx:.3f} mm')
    can.saveState();can.translate(dimx-5,(bottom+top)/2);can.rotate(90);can.drawCentredString(0,0,f'{dy:.3f} mm');can.restoreState()
   drawing=svg2rlg(io.BytesIO(svg.encode()));renderPDF.draw(drawing,can,x,y);can.setFillColor(TEAL);can.setFont('Helvetica-Bold',9);can.drawString(x,y+238,title)
  b=m['bounds'];size=[b[i+3]-b[i]for i in range(3)];can.setFillColor(BLUE);can.setFont('Helvetica-Bold',11);can.drawString(40,146,f"Envelope X {size[0]:.3f}   Y {size[1]:.3f}   Z {size[2]:.3f} mm")
  can.setFont('Helvetica',8)
  for j,line in enumerate(textwrap.wrap(m['notes'],width=175)):can.drawString(40,129-j*11,line)
  can.setFont('Helvetica',7);can.setFillColor(RED);can.drawString(40,25,'ENGINEERING HOLD UNTIL CURRENT VERIFICATION AND SAMPLE GATES PASS. DO NOT SCALE THIS PDF. USE1:1CUT FILES OR STEP.');can.drawRightString(W-40,25,str(page));can.showPage()
 can.save()

def make_chinese_order():
 s=[Paragraph('R07 制造询价与样件订单说明',ParagraphStyle('CNTitle',fontName='STSong-Light',fontSize=20,leading=28,textColor=BLUE)),P('状态：暂缓整套生产。先询价、先做样件。预算上限人民币3000元。','CNR07'),P('金属零件需由具备金属激光/水切割、车铣钻攻铰和焊接能力的工厂加工，与R06木板切割分开询价。请厂家先核对全部文件、材料、加工方法和数量，并给出分项报价。未通过数字干涉检查、实物配合检查和样件测试前，不得批量加工。当前没有已接受的供应商报价。','CNR07'),P('本包保留原R06四个垃圾桶，不要重复生产R06板件。新增外框约750毫米见方，原底板仍为700毫米见方。STL整机文件只供查看，不能作为一个整体打印。','CNR07')]
 s.append(P('一、激光切割与二次加工','CNR07'));s.append(P('DXF/DWG使用毫米单位，比例1:1，只切CUT图层（底板模板加工DRILL层）。REFERENCE图层不切。轴承孔先切21.5毫米再铰到22H7，曲柄轴孔先切7.5毫米再铰到8H7；STEP表示最终尺寸。孔H7需切割后铰孔，不能把激光切出来的孔当精密轴承孔。M09倾斜M3螺纹孔按STEP和孔轴数据二次钻攻，不得照参考圆直接垂直切穿。BASE模板仅表示原底板新增孔。','CNR07'))
 s.append(P('二、先做样件','CNR07'));s.append(P('先购买一只HTD-85H及配套金属舵盘；按实物配钻M07。先做一组驱动支架、轴、轴承、同步轮、皮带；先打印一套关节和配合样件。确认轴、键、球头、热熔螺母、打印层向与实际尺寸后，再申请其余数量。未确认处请先报问题，不要强装或擅自缩放文件。','CNR07'))
 s.append(P('三、零件数量','CNR07'));s.append(table([['零件编号','数量','加工 / 材料']]+[[r['part'],r['quantity'],r['process']+' / '+r['material']]for r in manufacture_rows()],[240,35,240],True))
 s.append(P('四、相同件与区别件','CNR07'));s.append(P('通用件可按表订多个：六根连杆管、十二片曲柄、四块后挡板、四个导料槽等。D1至D6前支架的机械限位孔不同，虽然外形相同，完成加工后不能随意互换。L1至L6垫块保留标签。数量为0的毛坯参考件不额外下单。标准平键M22直接购买，不要3D打印。','CNR07'))
 s.append(P('五、材料与交付','CNR07'));s.append(P('受力支架按图用铝合金或钢，轴和双曲柄轮毂用指定热处理钢；打印关节用PETG，支承软垫用TPU。禁止把受力金属件换成普通打印件。金属板去毛刺，球面抛光，键槽与轴承孔按实物样件检查。提供材料、尺寸、加工和报价记录。','CNR07'))
 s.append(P('六、报价停止条件','CNR07'));s.append(P('总额包含六个舵机、机械加工、打印、外框、同步传动、电源、电气件和全部紧固件，不含已有树莓派、摄像头及原垃圾桶。若超过3000元，请列明差额并暂停下单；不得自行降低2公斤载荷目标、删去挡板/限位/加强件或换薄材料。','CNR07'))
 document(ROOT/'PDF/Manufacturer_Order_CN_R07.pdf',s)

if __name__=='__main__':
 write_tables();make_guide();make_drawings();make_chinese_order();print('Created three PDFs and manufacturing/purchase/quote tables')
