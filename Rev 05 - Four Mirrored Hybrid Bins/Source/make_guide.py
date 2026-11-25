from pathlib import Path
import math,json,re,hashlib
import cadquery as cq
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from pypdf import PdfReader
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Source';IMAGES=WORK/'Illustrations'
OUT=ROOT/'PDF/Manufacturing_and_Assembly_Guide_R05.pdf'
INDEX=json.loads((IMAGES/'index.json').read_text())
META=json.loads((ROOT/'Source/model_metadata.json').read_text())
VERIFY=json.loads((ROOT/'Verification.json').read_text())
INK='#173743';MUTED='#49616d';TEAL='#087e87';PALE='#eaf4f5';LINE='#c9d8dc';GOLD='#e9a037'
FILE_REFS=[];PAGE_LOG=[];TEXT_BOXES=[]

PRODUCTION=[
 ('DWG/W01_rear.dwg','Rear wall','6 mm plywood',1,4),
 ('DWG/W02_right.dwg','Right wall','6 mm plywood',1,4),
 ('DWG/W03_front.dwg','Front short wall','6 mm plywood',1,4),
 ('DWG/W04_left.dwg','Left short wall','6 mm plywood',1,4),
 ('DWG/F01_floor.dwg','Floor','9 mm plywood',1,4),
 ('STL/C01_curved_corner.stl','Curved corner','PETG',1,4),
 ('STL/M01_magnet_insert.stl','Magnet insert','PETG',4,16)]
COUPONS=[
 ('DWG/Q01_wall_fit.dwg','Laser / 6 mm ply','Q03 for lower rows; Q04 for upper rows.'),
 ('DWG/Q02_floor_fit.dwg','Laser / 9 mm ply','Q08 tab; also test the small M4 hole.'),
 ('DWG/Q03_wall_tab.dwg','Laser / 6 mm ply','36-wide tab for lower Q01 rows.'),
 ('DWG/Q04_floor_tab.dwg','Laser / 9 mm ply','30-wide tab for upper Q01 rows.'),
 ('STL/Q05_curve_joint_sample.stl','Print / PETG','Print upright; pair with Q06 and an M3 nut.'),
 ('DWG/Q06_curve_wall_sample.dwg','Laser / 6 mm ply','Pair with Q05; test the countersink.'),
 ('DWG/Q07_insert_fit.dwg','Laser / 9 mm ply','Fit one M01 insert in each trial opening.'),
 ('DWG/Q08_floor_wall_tab.dwg','Laser / 6 mm ply','30-wide tab for Q02 slots.')]


def file(path):
    assert (ROOT/path).is_file(),path
    FILE_REFS.append(path)
    return path


def read_face(name):
    shape=cq.importers.importStep(str(ROOT/'STEP'/f'{name}.step')).val()
    faces=[f for f in shape.Faces()if f.geomType()=='PLANE'and abs(f.normalAt().z)>.9999]
    face=max(faces,key=lambda f:f.Area());loops=[]
    for wire in [face.outerWire(),*face.innerWires()]:
        curves=[]
        for edge in wire.Edges():
            if edge.geomType()=='LINE':points=[edge.startPoint(),edge.endPoint()]
            else:points=[edge.positionAt(v)for v in np.linspace(0,1,max(14,int(edge.Length()/1.5)))]
            curves.append([(p.x,p.y)for p in points])
        loops.append(curves)
    return loops


class Guide:
    def __init__(self):
        self.c=canvas.Canvas(str(OUT),pagesize=(297*mm,210*mm));self.page=0
        self.c.setTitle('Manufacturing and Assembly Guide - Trash Bin Pro Max R05')
        self.c.setAuthor('Trash Bin Pro Max')
        self.c.setSubject('Laser-cut plywood, printed PETG parts and assembly for the 10 kg design target')
    def rect(self,x,y,w,h,fill=PALE,stroke=None):
        self.c.setFillColor(colors.HexColor(fill));self.c.setStrokeColor(colors.HexColor(stroke or fill))
        self.c.setLineWidth(.5);self.c.rect(x*mm,y*mm,w*mm,h*mm,fill=1,stroke=bool(stroke))
    def line(self,x1,y1,x2,y2,color=LINE,width=.6):
        self.c.setStrokeColor(colors.HexColor(color));self.c.setLineWidth(width);self.c.line(x1*mm,y1*mm,x2*mm,y2*mm)
    def text(self,x,y,s,size=10,bold=False,color=INK,font=None):
        font=font or ('Helvetica-Bold'if bold else'Helvetica')
        self.c.setFillColor(colors.HexColor(color));self.c.setFont(font,size);self.c.drawString(x*mm,y*mm,s)
        TEXT_BOXES.append((self.page,x,y,stringWidth(s,font,size)/mm,size/mm,s))
    def para(self,x,top,w,text,size=10.2,leading=13.5,color=INK,bold=False):
        style=ParagraphStyle('p',fontName='Helvetica-Bold'if bold else'Helvetica',fontSize=size,leading=leading,textColor=colors.HexColor(color))
        p=Paragraph(text,style);ww,hh=p.wrap(w*mm,500*mm)
        p.drawOn(self.c,x*mm,top*mm-hh)
        TEXT_BOXES.append((self.page,x,top-hh/mm,w,hh/mm,re.sub('<[^>]+>','',text)))
        return top-hh/mm
    def section(self,x,top,w,title,text,size=10.2):
        self.text(x,top,title,11,True,TEAL)
        return self.para(x,top-4.3,w,text,size=size)-6
    def start(self,title,subtitle,chapter):
        self.page+=1;PAGE_LOG.append({'page':self.page,'title':title,'chapter':chapter})
        self.line(11,199,286,199,TEAL,1.3)
        self.text(11,192,'TRASH BIN PRO MAX / R05',8,True,TEAL)
        self.text(185,192,chapter.upper(),8,True,TEAL)
        self.text(11,181,title,23,True)
        self.para(11,176,275,subtitle,size=9.2,leading=11,color=MUTED)
        self.line(11,11,286,11)
        self.text(11,5.8,'mm / NOMINAL STOCK / CALIBRATE BEFORE FULL CUT',7.1,True,TEAL)
        self.text(232,5.8,f'19 NOV 2026  |  {self.page:02d} / 20',7.1,color=MUTED)
    def end(self):self.c.showPage()
    def arrow(self,a,b,color=TEAL):
        ax,ay=a;bx,by=b;dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
        if length<.01:return
        ux,uy=dx/length,dy/length;head=min(3.3,length*.4)
        self.line(ax,ay,bx,by,color,1.4)
        pp=self.c.beginPath();pp.moveTo(bx*mm,by*mm)
        pp.lineTo((bx-ux*head-uy*head*.4)*mm,(by-uy*head+ux*head*.4)*mm)
        pp.lineTo((bx-ux*head+uy*head*.4)*mm,(by-uy*head-ux*head*.4)*mm);pp.close()
        self.c.setFillColor(colors.HexColor(color));self.c.drawPath(pp,fill=1,stroke=0)
    def image(self,name,x,y,w,labels=False,arrows=False):
        info=INDEX[name];h=w*info['height']/info['width']
        self.c.drawImage(str(IMAGES/f'{name}.png'),x*mm,y*mm,width=w*mm,height=h*mm)
        def pt(p):return(x+w*p[0]/info['width'],y+h*(1-p[1]/info['height']))
        if arrows:
            for a,b in info['arrows']:self.arrow(pt(a),pt(b))
        if labels:
            for i,(label,p)in enumerate(info['anchors'].items()):
                a,b=pt(p);offset=-13 if i%2==0 else 6
                xx=min(max(x+1,a+offset),x+w-17);yy=min(max(y+2,b+6),y+h-7)
                self.line(a,b,xx+8,yy+1.8,TEAL,.65)
                self.rect(xx,yy-1,16,5.6,fill='#ffffff',stroke=TEAL)
                self.text(xx+1.1,yy+.3,label,7.4,True,TEAL)
        return h
    def note(self,x,y,w,h,title,text,size=9.5):
        self.rect(x,y,w,h);self.text(x+3,y+h-5,title,10,True,TEAL)
        end=self.para(x+3,y+h-7.5,w-6,text,size=size,leading=12.2,color=MUTED)
        assert end>=y+1,(self.page,title,end,y)
    def table(self,x,top,widths,headers,rows,heights=None,size=9.3,mono_first=False):
        total=sum(widths);self.rect(x,top-8,total,8)
        xx=x
        for w,label in zip(widths,headers):self.text(xx+2,top-5.5,label,8.3,True,TEAL);xx+=w
        yy=top-8
        for i,row in enumerate(rows):
            height=heights[i]if heights else 10
            if i%2==1:self.rect(x,yy-height,total,height,'#f7fafb')
            xx=x
            for j,(w,value)in enumerate(zip(widths,row)):
                if mono_first and j==0:self.text(xx+2,yy-6,str(value),size=8.0,font='Courier')
                else:
                    end=self.para(xx+2,yy-2,w-4,escape(str(value)),size=size,leading=11.6)
                    assert end>=yy-height+1,(self.page,value,end,yy-height)
                xx+=w
            self.line(x,yy-height,x+total,yy-height)
            yy-=height
        return yy
    def outline(self,name,x,y,w,maxh=None):
        loops=read_face(name);pts=np.array([p for loop in loops for edge in loop for p in edge])
        lo,hi=pts.min(0),pts.max(0);s=w/(hi[0]-lo[0])
        if maxh:s=min(s,maxh/(hi[1]-lo[1]))
        self.c.setStrokeColor(colors.HexColor(INK));self.c.setLineWidth(.6)
        for loop in loops:
            for edge in loop:
                p=self.c.beginPath()
                for i,(u,v)in enumerate(edge):
                    xx=(x+(u-lo[0])*s)*mm;yy=(y+(v-lo[1])*s)*mm
                    if i==0:p.moveTo(xx,yy)
                    else:p.lineTo(xx,yy)
                self.c.drawPath(p,stroke=1)
        return s,lo
    def record(self,x,y,w,label):
        self.text(x,y,label,8.4,color=MUTED);self.line(x,y-3,x+w,y-3,GRAY if False else LINE)
    def step(self,title,subtitle,view,parts,tools,sections,check,detail=None,detail_title=None,detail_text=None):
        self.start(title,subtitle,'Assembly')
        self.image(view,12,55,130,labels=True,arrows=True)
        self.text(17,53,'Gold identifies the incoming part. View is exploded.',7.5,color=MUTED)
        if detail:
            self.rect(13,14,49,39,'#ffffff',LINE)
            self.image(detail,14,14.2,43.5)
            self.text(67,44,detail_title,9.4,True,TEAL)
            self.para(67,39.8,82,detail_text,size=8.6,leading=11.4,color=MUTED)
        top=166
        top=self.section(159,top,126,'Parts and tools',parts+'<br/>'+tools,size=9.4)
        for title,text in sections:top=self.section(159,top,126,title,text)
        assert top>46,(self.page,'step text enters check box',top)
        self.note(159,15,127,28,'Check before continuing',check)
        self.end()
    def save(self):self.c.save()


g=Guide()
# 01
g.start('Build the four mirrored bins','A complete workshop guide for the delivered laser-cut plywood and printed PETG parts.','Start here')
g.image('four_layout',7,24,151,labels=True)
y=165
y=g.section(164,y,121,'Four labeled variants','B1 is the reference bin; B2 mirrors X, B3 mirrors Y, and B4 mirrors both. Each has its own wall, floor and curve files. Build one sample first, then keep every variant in its labeled kit.')
y=g.section(164,y,121,'The manufacturing route','1. Select the files and buy the hardware.<br/>2. Cut and print the small fit samples.<br/>3. Calibrate, manufacture and prepare parts.<br/>4. Dry-fit, then bond and fasten.<br/>5. Fit the inserts, finish and load-test.')
y=g.section(164,y,121,'Dimensions and load target','Each bin: <b>347.5 x 347.5 x 450 mm</b>.<br/>Four-bin layout: <b>700 x 700 x 450 mm</b>.<br/>Walls: <b>6 mm birch plywood</b>. Floor: <b>9 mm</b>.<br/>Curve and inserts: <b>PETG</b>.<br/><b>10 kg per-bin design target</b>, with a <b>15 kg supported proof test</b>.')
g.note(163,15,123,29,'Prototype status','Mirrored geometry, insertion and export checks are recorded in Verification.json. Physical fit and load tests remain to be completed. Base and central platform CAD were not supplied.',size=9)
g.end()
# 02
g.start('Select a separate kit for each bin','Every filename below is a manufacturing file. Make one of each B-specific part; keep all five plywood pieces with their matching curve.','File map')
rows=[]
for part,role,process in [('W01','Long wall A','6 mm plywood'),('W02','Long wall B','6 mm plywood'),('W03','Short wall A','6 mm plywood'),('W04','Short wall B','6 mm plywood'),('F01','Shaped floor','9 mm plywood'),('C01','Printed curve','PETG')]:
 paths=[file(('STL/'if part=='C01'else'DWG/')+f'{bid}_{part}'+('.stl'if part=='C01'else'.dwg'))for bid in ['B1','B2','B3','B4']]
 rows.append((part+' / '+process,*paths))
g.table(11,164,[55,55,55,55,55],['Part / material','B1 (+X,+Y)','B2 (-X,+Y)','B3 (+X,-Y)','B4 (-X,-Y)'],rows,heights=[12]*6,size=8.5)
g.note(11,48,132,31,'Laser cutting / 20 finished plywood pieces','Cut each of the twenty B-specific DWGs once: sixteen walls in 6 mm stock and four floors in 9 mm stock. CUT geometry is the finished contour; compensate measured kerf once.',size=9.2)
g.note(149,48,137,31,'3D printing / 20 finished printed pieces','Print B1_C01, B2_C01, B3_C01 and B4_C01 once each. Print sixteen copies of '+file('STL/M01_magnet_insert.stl')+' (four per bin). M01 is common to all variants.',size=9.2)
g.para(12,39,272,'<b>Inspection files.</b> Each B-specific part also has an STL and STEP. Plywood STLs are for inspection. B1_Assembly through B4_Assembly show the separate bins; '+file('STEP/Four_Bin_Layout_R05.step')+' and '+file('STL/Four_Bin_Layout_R05.stl')+' show all four in position. Printed-part _REFERENCE DWGs are dimension views.',size=9.1,leading=12)
g.end()
# 03
g.start('Materials, hardware and tools','Prepare all fasteners before committing to the full print. Check nut and screw fit with the samples.','Procurement')
hardware=[('M3 x 12 countersunk screw','90-degree head; check modeled 6.3 seat',6,24),('M3 hex nut','Fits AF5.8 x 2.6-deep trap',6,24),('M4 x 20 countersunk screw','90-degree head; check modeled 8.0 seat',3,12),('M4 hex nut','Fits AF7.2 x 3.4-deep trap',3,12),('Magnets, selected to suit','Recess is diameter 25.2 x 5 deep',4,16)]
g.table(11,165,[66,99,20,22],['Hardware','Fit requirement','1 bin','4 bins'],hardware,heights=[12]*5,size=9.1)
g.text(225,161,'Consumables',11,True,TEAL)
g.para(225,155,61,'6 mm and 9 mm birch plywood; PETG; structural wood glue suited to the plywood; epoxy compatible with PETG and wood; masking tape; compatible wood finish.',size=9.4,leading=12.3)
g.text(11,82,'Tool checklist',12,True,TEAL)
g.para(11,76,130,'Calipers for sheet, slots and inserts; 600 mm ruler or straightedge; framing square; pencil and part labels; flat padded bench; clamps and scrap pressure pads; fine abrasive and a deburring tool.',size=10)
g.para(153,76,132,'A drill with a 90-degree countersink and backing block; M3/M4 screwdrivers; nut-holding tool or tweezers; cleaning supplies specified by the adhesives; scale, distributed test weights and a way to measure floor deflection.',size=10)
g.note(11,16,275,27,'Order by the supplied geometry','Have the shop nest the plywood from the profiles. Ask it to include coupon stock and print support material. The net C01 CAD volume is about 664 cm3 per curve; actual filament use includes supports and waste.',size=9.4)
g.end()
# 04
g.start('Manufacture the calibration samples first','Make one of each sample for the first prototype. Repeat samples when stock, laser settings or print setup changes.','Calibration')
rows=[(file(p),process,'1',pair)for p,process,pair in COUPONS]
g.table(11,164,[102,51,16,106],['File','Process / material','Qty','Use with / purpose'],rows,heights=[11]*8,size=8.8,mono_first=True)
g.note(11,31,132,30,'Printed samples','Q05 must use the same layer direction as C01. Print one '+file('STL/M01_magnet_insert.stl')+' to try in Q07. Check both the finger fit and an actual M3 nut.')
g.note(149,31,137,30,'Measure the stock','Measure each plywood thickness at several clean locations. Record a range, including any finish. Measure the printed sample after it has cooled. Keep samples identified by material and settings.')
g.end()
# 05
g.start('Select joint clearance and measure kerf','Choose a sliding fit that seats fully by hand, then regenerate profiles for the actual measured stock.','Calibration')
s,lo=g.outline('Q01_wall_fit',15,34,117,117)
g.text(15,155,'Q01 / 6 mm stock',10,True,TEAL)
g.text(15,27,'Upper rows: Q04. Lower rows: Q03.',8.7,color=MUTED)
for row,yy in enumerate([30,65,120,155]):
    n=4 if row%2==0 else 3
    for j in range(n):
        gap=.1+.05*(j+(0 if row%2==0 else 4))
        g.text(15+(25+50*j)*s-3,34+(yy-13)*s,f'{gap:.2f}',6.8,color=MUTED)
y=165
y=g.section(151,y,134,'1 / Fit the correct pairs','Q03 in the lower Q01 rows tests the wall interface. Q04 in the upper Q01 rows tests the floor thickness. Q08 in Q02 tests the wall tabs entering the floor. Values run <b>0.10 to 0.40 mm total clearance</b>.')
y=g.section(151,y,134,'2 / Test the printed interface','Seat Q05 and Q06 along their finger direction. Test the M3 nut. Try M01 in Q07: its three holes are <b>0.10, 0.20 and 0.30 mm radial clearance, left to right</b>. Select the smallest fit that seats without forcing.')
y=g.section(151,y,134,'3 / Measure each kerf plug','Q01 and Q02 each have a nominal 20 x 20 square plug. Measure the plug and its matching opening in X and Y. Estimate full kerf as <b>(opening minus plug) / 2</b>. Record separate results for each sheet thickness.')
g.note(151,15,135,28,'Feed the measurements back','Give actual thicknesses, selected clearances and measured kerfs to the CAD/laser operator. The supplied profiles use nominal stock and contain no kerf offset.',size=9.2)
g.end()
# 06
g.start('Laser-cut the production plywood','Approve the coupons with the supplier before cutting full walls and floors.','Laser cutting')
g.image('exploded',8,30,138)
y=164
y=g.section(158,y,128,'1 / Load twenty production DWGs','Use each B1/B2/B3/B4 W01-W04 on <b>6 mm stock</b>, and each B1/B2/B3/B4 F01 on <b>9 mm stock</b>. The B-prefix is part of the identity. Keep all parts of one bin together. Do not replace a variant with four copies of B1.')
y=g.section(158,y,128,'2 / Check the job setup','Confirm <b>millimetres</b> and <b>1:1</b> import. Use CUT geometry. REFERENCE contains identifiers and sample labels. Apply measured kerf compensation <b>once</b> in the laser workflow, accounting for outside contours and openings.')
y=g.section(158,y,128,'3 / Verify scale and cut quality','If the shop uses '+file('PDF/Full_Scale_Cutting_Profiles_R05.pdf')+', print/import at actual size and verify its <b>100 mm scale bar</b>. Inspect a complete cut through both stock thicknesses before the production run.')
g.note(158,15,128,29,'Receive and inspect','Count four wall parts and one floor per bin. Check clean through-cuts, flat stock, intact fingers and clear holes. Keep the square kerf plugs and the approved samples.',size=9.2)
g.end()
# 07
g.start('3D-print the PETG parts','Use the individual manufacturing STLs. The complete curve remains one piece.','3D printing')
g.image('curve_print',6,50,133,labels=True,arrows=True)
g.text(20,47,'C01 upright: base down, height along printer Z.',8.5,color=MUTED)
g.image('insert_print',80,15,42)
g.text(11,36,'M01 roof on bed;',9,True,TEAL);g.text(11,30,'pocket facing up.',9,color=MUTED)
y=165
y=g.section(150,y,136,'C01 / four distinct manufacturing files',file('STL/B1_C01.stl')+' and its B2/B3/B4 counterparts each have a <b>130 x 130 x 450 mm</b> envelope. Keep the full height upright; use a machine with at least 450 mm usable Z plus process allowance. The <link href="https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf" color="#087e87">H2D specification lists 325 mm Z</link>, so it cannot print this orientation. Test Q05 first.')
y=g.section(150,y,136,'Slicer checks','Use the supplier\'s PETG material profile. Start with <b>six perimeters</b>, and inspect the preview so the <b>6 mm shell is substantially solid</b>. Have the operator confirm bonding, temperatures and layer settings for that material and machine.')
y=g.section(150,y,136,'Support placement','Support the floor-pad undersides, flange starts, finger undersides and captive-nut cavities as needed. Confirm supports can be removed from every recess. Keep the curve upright for the same layer direction as the fit sample.')
g.note(150,15,136,29,'M01 / four inserts per bin','Print the closed roof on the bed with the recess upward, then flip for installation. Check diameter and depth after cooling. Print sixteen inserts for the four-bin set.',size=9.2)
g.end()
# 08
g.start('Clean, inspect and label the parts','Do this before countersinking or applying glue. Keep the approved coupons beside the first bin.','Preparation')
g.image('four_top',8,48,137,labels=True)
g.text(16,45,'TOP VIEW: +Y up; +X right. All bins upright.',8.4,True,TEAL)
g.text(16,38,'B2 | B1 above center; B4 | B3 below center.',8.4,color=MUTED)
g.text(16,31,'Package labels define the quadrants shown here.',8.2,color=MUTED)
y=165
y=g.section(154,y,131,'Plywood','Remove loose char and burrs from the glue lands, slots and fingers. Use light, flat sanding so you preserve the calibrated dimensions. Check for split veneers, burned-away finger roots, warping and incomplete cuts.')
y=g.section(154,y,131,'Printed parts','Remove supports carefully, especially from the M3/M4 nut traps, floor pads and finger recesses. Check the full-height curve for lifted layers or splits. Check every M01 recess and both flat end faces. Resolve fit errors with a sample before the full assembly.')
y=g.section(154,y,131,'Mark the complete identity','Use B1_W01 through B4_W04, B1_F01 through B4_F01 and B1_C01 through B4_C01. W01-W04 are local role IDs, so their global compass sides change under mirroring. Fingers point down. Curves face the central opening; flanges face into their bins.')
g.note(154,15,132,29,'Face labels','Mark the two short-wall outside faces for countersinking. Mark F01 underside: the four magnet recesses will open there. Use removable labels outside the bonding areas.',size=9.2)
g.end()
# 09
g.start('Countersink the correct outside faces','The laser files contain the small through holes. Drill the countersinks after cutting, using a backing block and an approved sample.','Secondary operations')
def section_hole(x,y,width,thick,hole,head,depth,label):
    scale=5;center=x+width/2;top=y+thick*scale
    g.text(x,top+9,label,10,True,TEAL)
    g.rect(x,y,width,thick*scale,'#dfc7a3',LINE)
    p=g.c.beginPath();p.moveTo((center-head/2*scale)*mm,top*mm);p.lineTo((center+head/2*scale)*mm,top*mm);p.lineTo((center+hole/2*scale)*mm,(top-depth*scale)*mm);p.lineTo((center+hole/2*scale)*mm,y*mm);p.lineTo((center-hole/2*scale)*mm,y*mm);p.lineTo((center-hole/2*scale)*mm,(top-depth*scale)*mm);p.close()
    g.c.setFillColor(colors.white);g.c.setStrokeColor(colors.HexColor(INK));g.c.drawPath(p,fill=1,stroke=1)
    g.arrow((center,top+7),(center,top+1));g.text(x,y-6,f'{thick} stock / {hole} through / {head} x 90-degree seat',8.6)
    g.text(x,y-12,f'Nominal depth {depth:.2f}; exterior face shown upward.',8.4,color=MUTED)
section_hole(15,117,117,6,3.4,6.3,1.45,'W03 + W04 / THREE HOLES ON EACH')
section_hole(15,45,117,9,4.5,8,1.75,'F01 / THREE SMALL M4 HOLES ONLY')
y=165
y=g.section(151,y,135,'1 / Identify, then mark','Use the top-view coordinate map on page 8. Mark only W03 and W04 exterior faces, plus F01 underside. W01 and W02 have no countersinks. The large insert holes remain straight through.')
y=g.section(151,y,135,'2 / Cut and test the seats','Use a 90-degree countersink at controlled depth. Test actual screw heads: they must sit flush without crushing plywood or leaving a thin damaged edge. Check Q06 and the Q02 M4 trial hole first.')
g.table(151,95,[25,43,43,24],['Bin','W03 face','W04 face','F01'],[(b,f'Y={sy*2.5:+.1f}',f'X={sx*2.5:+.1f}','Z=0')for b,(sx,sy)in {'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}.items()],heights=[9]*4,size=9)
g.note(151,15,135,29,'Preserve the seats','Keep the countersunk face labeled during dry assembly. Do not deepen a seat to force a misaligned screw. The dimensions above are nominal; approve the chosen head profile on scrap.',size=9.2)
g.end()
# 10
g.start('Prepare each curve and its captive nuts','Assemble one labeled bin at a time. Pages 11-15 show B1; use the direction matrix below for the other variants.','Assembly')
g.image('curve_inside',8,45,135,labels=True)
g.image('m3_pocket',14,16,42);g.image('m4_pad',79,16,42)
g.text(14,53,'M3 side trap',8.3,True,TEAL);g.text(79,53,'M4 floor-pad trap',8.3,True,TEAL)
y=165
y=g.section(151,y,135,'Parts and tools','Matching B#_C01; six M3 nuts and three M4 nuts per curve; tweezers, nut tool and removable tape. Keep all 450 mm height upright and the three floor pads at the bottom.')
y=g.section(151,y,135,'Seat all nine nuts','Press each nut squarely into its accessible trap by hand. M3: AF5.8 x 2.6 deep. M4: AF7.2 x 3.4 deep. Use small pieces of tape to hold nuts during handling; keep tape clear of mating faces. Check each thread from the screw side.')
g.text(151,83,'Incoming motion in the global CAD axes',10,True,TEAL)
g.table(151,78,[23,22,22,22,22,24],['Bin','W03','W04','W01','W02','F01'],[('B1','-X','-Y','-Y','-X','+Z'),('B2','+X','-Y','-Y','+X','+Z'),('B3','-X','+Y','+Y','-X','+Z'),('B4','+X','+Y','+Y','+X','+Z')],heights=[8]*4,size=8.7)
g.para(151,32,134,'All bins stay upright in this coordinate convention. You may rotate a kit on the bench. Preserve the relative joint direction shown; remove parts in the opposite direction.',size=8.9,leading=11.5)
g.end()
# 11
g.step('Dry-fit W03 to its matching curve','B1 shown. W03 seating motion: B1 -X; B2 +X; B3 -X; B4 +X. Keep the B-prefix identical on both parts.','stage_front',
       'B#_C01 + B#_W03; three M3 x 12 screws.','Padded bench, screwdriver and a helper or temporary support.',
       [('1 / Bring the parts together','Keep bottom fingers down and both top edges at Z450. Align all six finger bands before moving the short wall horizontally toward the curve. The countersinks face away from the bin interior.'),
        ('2 / Seat by hand','Slide along the indicated X direction until the finger shoulders seat. Keep the full wall parallel to the curve wing. If one finger catches, withdraw and inspect the local burr or orientation.'),
        ('3 / Hold the joint','Thread the three screws through W03 into the captured nuts. Leave them loose enough to settle the dry fit; support the tall parts while adding W04.')],
       'All finger bands engage; top and bottom datums agree; all three screws start by hand. The smooth curved surface faces the central opening.',
       'print_joint','Printed / plywood joint','Six bands share the edge. The modeled 0.30 mm total vertical gap is a starting clearance; approved samples determine the final cut/print fit.')
# 12
g.step('Dry-fit W04 to the other curve wing','B1 shown. W04 seating motion: B1 -Y; B2 -Y; B3 +Y; B4 +Y.','stage_left',
       'Matching B#_W04; existing C01/W03; three M3 x 12 screws.','Screwdriver, square, padded blocks and temporary support.',
       [('1 / Match the open wing','Identify the second short wall by its full ID and joint pattern. Keep its countersunk face outside, nut flange inside, and bottom fingers pointing down.'),
        ('2 / Slide into all bands','Align the six bands along the entire height. Move W04 horizontally in the listed Y direction. Hold the previously fitted W03 so the first joint is not twisted.'),
        ('3 / Retain, then check','Start all three M3 screws loosely. Place the partial shell on a flat padded surface and use a square to check the two straight-wall directions.')],
       'Six M3 screws are present across the two short walls. Both short walls seat fully and remain supported. Nut traps are still accessible inside.',
       'm3_pocket','Captive-nut check','The nut must stay square in its trap while the screw turns freely. Stop if the nut spins, the screw cross-threads or the printed flange bends.')
# 13
g.step('Dry-fit W01 / long wall A','B1 shown. W01 seating motion: B1 -Y; B2 -Y; B3 +Y; B4 +Y. W01 is the B1 rear-wall role.','stage_rear',
       'Matching B#_W01; the supported curve and two short walls.','Padded clamps or removable tape; square and a helper.',
       [('1 / Present the correct edge','Find the W01 edge that meets W04. Keep its four bottom fingers down. Compare the finger pattern with the assembled B-specific STEP before trying to close the corner.'),
        ('2 / Seat along Y','Align the complete edge and move W01 in the listed Y direction. Hold W04 square and avoid bending fingers to get past an obstruction.'),
        ('3 / Retain the dry corner','Hold the new wood-to-wood joint with padded clamps or tape. Keep the remaining W02 side open for the next operation.')],
       'All six vertical bands at this wood corner are seated. The top edges align, the outer corner is square and the four floor fingers remain intact.',
       'wood_joint','Wood / wood corner','The nominal 0.20 mm total vertical clearance permits assembly before gluing. A corner that only closes under heavy clamp force needs correction.')
# 14
g.step('Close W02 / long wall B','B1 shown. W02 seating motion: B1 -X; B2 +X; B3 -X; B4 +X. Both vertical corners close together.','stage_right',
       'Matching B#_W02; existing three-wall/curve shell.','Square, padded clamps or tape, helper and ruler.',
       [('1 / Align both corners','Bring W02 to its open side with its four bottom fingers down. Align both vertical edge patterns simultaneously, keeping W01 and W03 supported.'),
        ('2 / Move along X','Slide W02 in the listed X direction while keeping it parallel to its final position. Check both ends frequently; neither end should advance by flexing the other wall.'),
        ('3 / Hold the complete shell','Retain both corners with light padded clamping or tape. Check the square outer corners and all 450 mm top edges before preparing the floor.')],
       'Both W02 corners close fully. The shell holds its geometry with light retention. No finger root, printed layer or plywood veneer shows damage.',
       'wood_joint','Two corners, one motion','A wrong bin prefix or a reversed wall can resemble a tight joint. Check the ID and the approved profile before sanding any mating surface.')
# 15
g.step('Fit F01 into the bottom joints','B1 shown inverted for access. In upright CAD coordinates, every F01 seats upward along +Z.','stage_floor',
       'Matching B#_F01; complete retained shell; three M4 x 20 screws.','Helper, padded rim supports, screwdriver and nut-holding tape.',
       [('1 / Invert the held shell','With a helper, turn the lightly clamped shell onto its padded open rim. The retained M4 nuts stay in their pads. The bin underside is now accessible from above.'),
        ('2 / Lower the floor in the room','Keep F01 countersinks and future magnet openings facing you. Align fourteen wall tabs and the three curved locating tabs, then seat the floor evenly. This is the CAD +Z motion after inversion.'),
        ('3 / Retain and return upright','Start the three M4 screws from the underside into the captured nuts. Leave them loose during dry fitting. Support the complete bin when returning it upright.')],
       'The underside is flush at Z0; the floor top is Z9. All tabs seat, and all three screws start by hand. Do not use the screws to pull a tilted floor into place.',
       'floor_joint','Floor / wall interface','The walls have 30 mm wide, 9 mm deep bottom tabs. Align the whole perimeter before seating the floor; keep the countersinks on the underside.')
# 16
g.start('Inspect and record the complete dry fit','Complete this inspection on B1, B2, B3 and B4 before committing adhesive to that kit.','Assembly checks')
g.image('overview',7,35,139,labels=True)
y=165
y=g.section(153,y,132,'Geometry and joints','Confirm the 347.5 x 347.5 x 450 mm envelope, aligned top edges and a flush underside. Check the three square outer corners with a framing square. Compare wall spacing at top and bottom; the curved corner has no square vertex for a direct diagonal check.')
y=g.section(153,y,132,'Mechanical attachment','Count <b>six M3 and three M4 screws</b> in each bin. Every screw starts by hand, its nut stays seated and its head can sit flush. Tighten gently for a fit check; no printed flange or plywood seat should crush. No torque rating has been established.')
y=g.section(153,y,132,'Inserts and full-system trial','Try four M01 inserts dry, roof toward the bin interior. Arrange all four bins using the page 8 map. Check the actual base, magnet locations and central post before bonding. Keep the 5 mm bin gaps clear.')
g.note(153,16,133,27,'Confirmed post clearance','The confirmed post diameter is 147.5 mm. The R75 curve leaves 1.25 mm nominal radial clearance. Curves and floors preserve that space in all four bins. Trial base alignment and magnet fit before bonding.',size=9.2)
g.record(15,31,129,'Kit ID / measured envelope / dry-fit result:')
g.record(15,20,129,'Stock / print profile / corrections approved:')
g.end()
# 17
g.start('Glue, clamp and fasten in the same order','Use the first dry fit to establish the correct motion and clamp positions. Work within the adhesive manufacturer\'s open time.','Permanent assembly')
g.image('exploded',7,42,139)
y=165
y=g.section(154,y,131,'1 / Disassemble and prepare','Remove F01 in CAD -Z, then W02, W01, W04 and W03 in reverse order. Reverse the directions listed on page 10. Keep the captive nuts retained. Clean the wood glue lands and protect the bench.')
y=g.section(154,y,131,'2 / Apply wood glue','Apply an even film to mating plywood finger faces and the plywood floor/wall joints. Reassemble W03, W04, W01, W02, then F01 as practiced. The curve is mechanically fastened; keep wood glue out of nut traps, threads, magnet holes and printed clearances.')
y=g.section(154,y,131,'3 / Clamp and cure','Install six M3 and three M4 screws. Use padded clamps and check square corners, parallel walls and flush joints before the glue sets. Tighten only enough to seat the faces. Remove squeeze-out and follow the full cure time before load testing.')
g.note(154,16,132,28,'Check the hidden floor joints','Inspect all floor tabs before curing. Confirm the three M4 pads sit against the floor top, and all countersunk heads are flush below. Do not depend on clamps or screws to hide a bad fit.',size=9.2)
g.record(15,32,128,'Bin / glue product / start time / cure due:')
g.record(15,21,128,'Square and flush check / clamp removal:')
g.end()
# 18
g.start('Bond inserts, finish and establish polarity','The same M01 file supplies sixteen inserts. Finish and adhesive choices must be compatible with the actual wood, PETG and magnets.','Finishing')
g.image('floor_bottom',5,60,121,labels=True)
g.image('insert_installed',13,14,47)
g.text(68,43,'M01 installed: roof up,',9.2,True,TEAL);g.text(68,37,'magnet pocket down.',9.2,color=MUTED)
g.para(68,30,74,'OD29.2 x 9; recess diameter 25.2 x 5 deep. Four per floor.',size=8.8,leading=11.5)
y=165
y=g.section(152,y,133,'1 / Bond the four inserts flush','After wood glue cures, prepare PETG and wood as specified by a compatible epoxy. Apply epoxy in the 0.20 mm radial annulus around each insert. Keep its closed roof flush with the floor top and its pocket opening on the underside. Wipe away excess and let it cure.')
y=g.section(152,y,133,'2 / Seal the plywood','Smooth sharp edges lightly and apply a suitable finish to all accessible wood faces and exposed edges. Preserve holes, joint clearance, seats and the magnet recesses. Let the coating cure before final checks or a liner is fitted.')
y=g.section(152,y,133,'3 / Fit magnets against the actual base','Check each finished pocket diameter/depth. Choose magnets that leave room for the adhesive without protruding. Dry-check the correct base location and mark attracting polarity before bonding. Record which bin occupies each quadrant.')
g.note(152,15,134,27,'Magnet fit does not establish load capacity','Inspect base alignment and retention separately. Do not use the magnets as lifting points. The supplied files do not include or verify the existing base/post hardware.',size=9.1)
g.end()
# 19
g.start('Test every manufactured bin','10 kg is the working-load design target. CAD screening has been completed; these physical acceptance checks have not been performed.','Physical verification')
y=165
y=g.section(12,y,132,'1 / Set up the supported proof test','Wait for all adhesive and finish to cure. Place the bin on a rigid, stable perimeter support with the floor span accessible for measurement. Record the support arrangement. Keep a catch surface below; keep hands clear of the loaded floor.')
y=g.section(12,y,132,'2 / Apply 15 kg distributed load','Record the unloaded floor position. Add known weights gradually and distribute them across the floor, protecting it from concentrated points. Hold 15 kg for 60 minutes. Inspect joints, screws, layers and wood while measuring floor deflection relative to its supports.')
y=g.section(12,y,132,'3 / Unload and check recovery','Workshop acceptance targets: peak deflection at most 2.0 mm; residual at most 0.5 mm after ten unloaded minutes. Require no cracks, joint opening, loose nuts, proud heads or permanent deformation. A failure stops use until corrected and retested.')
y=165
y=g.section(155,y,131,'4 / Trial normal handling at 10 kg','After a successful proof test, use 10 kg distributed payload. With a helper and catch surface, complete ten controlled lift/set-down cycles, supporting the lower body at sound wall regions. Do not lift by the printed curve, rim, screws or magnets.')
y=g.section(155,y,131,'5 / Check the four-bin installation','Place each labeled bin in its assigned quadrant. Check actual base/magnet engagement, post clearance and removal access, with no rubbing or trapped hardware. Check the 5 mm nominal bin gaps and re-inspect after the handling trial.')
g.para(155,y,131,'<b>Calculation context.</b> The inherited ideal 9 mm floor screen assumes E=3,000 MPa and span/width 335.5 mm: 0.79 mm at 10 kg, 1.18 mm at 15 kg. It omits local holes, joint behavior and print defects; it is a preliminary screen, not a certified rating.',size=9.2,leading=12)
g.table(12,62,[24,44,45,43,43,76],['Bin','15 kg / 60 min','Peak deflection','10-min residual','10 kg / 10 lifts','Base / post / inspection result'],[(b,'________','________ mm','________ mm','________','__________________')for b in ['B1','B2','B3','B4']],heights=[8]*4,size=8.3)
g.text(12,14,'Tester / date / support arrangement / instrument: ______________________________________________________________________',8.8)
g.end()
# 20
g.start('Troubleshoot and sign off the four-bin set','Record changes and retest the affected kit. Keep the approved coupons, stock measurements and print settings with the job.','Handover')
rows=[
 ('Tight fingers or floor tabs','Check the B-prefix, face labels, burrs and actual stock thickness. Recheck Q01/Q02/Q05/Q06. Adjust and regenerate the master geometry and all affected mirrors; do not force the joint.'),
 ('Loose joints or visible gaps','Compare actual kerf, sheet thickness and print shrinkage with the approved samples. Recalibrate the nominal gap; replace damaged parts. Glue cannot restore missing or burned finger roots.'),
 ('Warped print or lifted layers','Check the cooled part on a flat surface. Reprint using an approved PETG profile and upright layer direction; do not assemble a cracked, delaminated or twisted curve.'),
 ('Blocked nut trap / spinning nut','Remove remaining support without enlarging the pocket. Check nut AF and depth. Replace the nut or reprint a damaged trap before loading; hold the nut square while starting its screw.'),
 ('Proud head / misaligned screw','Check countersink face, head angle and joint seating. Trial the actual fastener on a sample. Keep the nominal seat size; do not deepen a hole to conceal an offset assembly.'),
 ('Floor will not seat evenly','Use the matching B#_F01. Align fourteen wall tabs and three curve tabs at once. Reverse the motion and inspect. Confirm all nuts/support remnants are clear and the retained shell is square.'),
 ('Post, base or magnets do not fit','Measure the existing hardware and compare global center locations. Check the confirmed 147.5 mm post and the actual base mounting. Keep all four kits in their mapped quadrants; review any mounting change before remanufacture.')]
g.table(11,165,[61,214],['Observed issue','Action'],rows,heights=[14]*7,size=9.2)
g.note(11,17,132,29,'Four completed kits','20 plywood plates; 4 matching curves; 16 inserts; 24 M3 screws/nuts; 12 M4 screws/nuts. Labels, finish, joint seating and screw heads checked. All physical results recorded.',size=9)
g.note(149,17,137,29,'Final acceptance','B1 ____ B2 ____ B3 ____ B4 ____<br/>Assembler / date __________________________<br/>Owner acceptance / post fit __________________',size=9.2)
g.end();g.save()
assert g.page==20,g.page
reader=PdfReader(OUT);assert len(reader.pages)==20
texts=[p.extract_text()for p in reader.pages]
assert all(texts)
assert len(set(FILE_REFS))>=35
for page,x,y,w,h,text in TEXT_BOXES:
    assert x>=0 and y>=3 and x+w<=297.1 and y+h<=200,(page,x,y,w,h,text)
(ROOT/'Source/guide_verification.json').write_text(json.dumps({'pages':PAGE_LOG,'file_references':sorted(set(FILE_REFS)),'part_quantities':{'laser_6mm_walls':16,'laser_9mm_floors':4,'printed_curves':4,'printed_inserts':16},'text_boxes_checked':len(TEXT_BOXES),'notes':'B1 assembly views use the tested sequence; mirrored motion directions supplied for B2-B4. All file references checked against package.'},indent=2))
print('Guide saved:',OUT,'pages',g.page,'file refs',len(set(FILE_REFS)))
