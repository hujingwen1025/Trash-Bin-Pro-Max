"""Create the drawing booklet, full-scale profile PDF and CAD illustrations."""
from pathlib import Path
import json,math,textwrap,os
import numpy as np
import trimesh
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];INTERNAL=Path(os.environ.get('BIN_BUILD_DIR',str(ROOT/'.build')))
META=json.loads((ROOT/'Source/model_metadata.json').read_text())
P=json.loads((ROOT/'Source/parameters.json').read_text())
PRO=json.loads((INTERNAL/'all_profiles.json').read_text())
SECTIONS=json.loads((INTERNAL/'curve_sections.json').read_text())
SIDE=json.loads((INTERNAL/'curve_side.json').read_text())
REPORT=json.loads((ROOT/'Verification.json').read_text())
INK='#203943';TEAL='#087f83';PALE='#edf5f6';GRAY='#5c7079';LIGHT='#c9d8dc'

# Render the delivered meshes with true depth-buffer visibility.
import vtk
vtk_colors={'W01_rear':(.76,.65,.51),'W02_right':(.74,.63,.49),'W03_front':(.89,.78,.64),'W04_left':(.82,.70,.55),'F01_floor':(.81,.69,.54),'C01_curved_corner':(.25,.60,.64)}
shifts={'W01_rear':(0,55,0),'W02_right':(55,0,0),'W03_front':(0,-55,0),'W04_left':(-55,0,0),'C01_curved_corner':(-35,-35,0),'F01_floor':(0,0,-55)}
for exploded in [False,True]:
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1500,1500);win.AddRenderer(ren);win.SetMultiSamples(8)
 for name,color in vtk_colors.items():
  reader=vtk.vtkSTLReader();reader.SetFileName(str(ROOT/'STL'/f'{name}.stl'));reader.Update()
  normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(reader.GetOutputPort());normals.SetFeatureAngle(30);normals.Update()
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
  actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color)
  actor.GetProperty().SetAmbient(.3);actor.GetProperty().SetDiffuse(.7);actor.GetProperty().SetSpecular(.05)
  if exploded:actor.SetPosition(*shifts.get(name,(0,0,0)))
  ren.AddActor(actor)
 cam=ren.GetActiveCamera();cam.SetPosition(-800,-800,760);cam.SetFocalPoint(175,175,210);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(390 if exploded else 350)
 ren.ResetCameraClippingRange();win.Render()
 image=vtk.vtkWindowToImageFilter();image.SetInput(win);image.SetScale(1);image.ReadFrontBufferOff();image.Update()
 writer=vtk.vtkPNGWriter();writer.SetFileName(str(INTERNAL/('exploded.png'if exploded else'assembled.png')));writer.SetInputConnection(image.GetOutputPort());writer.Write();win.Finalize()


def pts(e):
    if e['type']=='LINE':return [e['start'],e['end']]
    a,b=(0,360)if e['type']=='CIRCLE'else(e['start_angle'],e['end_angle'])
    if b<a:b+=360
    return [[e['center'][0]+e['radius']*math.cos(math.radians(t)),e['center'][1]+e['radius']*math.sin(math.radians(t))]
            for t in np.linspace(a,b,max(16,int((b-a)/2)+1))]


def bounds(wires):
    arr=np.array([q for w in wires for e in w for q in pts(e)])
    return arr.min(0),arr.max(0)


class Book:
    def __init__(self,path):self.c=canvas.Canvas(str(path),pagesize=(420*mm,297*mm));self.page=0
    def text(self,x,y,s,size=10,bold=False,color=INK):
        self.c.setFillColor(colors.HexColor(color));self.c.setFont('Helvetica-Bold'if bold else'Helvetica',size)
        self.c.drawString(x*mm,y*mm,s)
    def line(self,x1,y1,x2,y2,color=LIGHT,width=.6):
        self.c.setStrokeColor(colors.HexColor(color));self.c.setLineWidth(width);self.c.line(x1*mm,y1*mm,x2*mm,y2*mm)
    def rect(self,x,y,w,h,fill=PALE):
        self.c.setFillColor(colors.HexColor(fill));self.c.rect(x*mm,y*mm,w*mm,h*mm,stroke=0,fill=1)
    def start(self,title,subtitle):
        self.page+=1;self.line(14,282,406,282,TEAL,1.4)
        self.text(14,272,'TRASH BIN PRO MAX / R04 / HYBRID BIN',9,True,TEAL)
        self.text(14,257,title,24,True);self.text(14,247,subtitle,10,color=GRAY)
        self.line(14,16,406,16);self.text(14,9,'mm | NOMINAL STOCK - CALIBRATE BEFORE FULL CUT',8,True,TEAL)
        self.text(331,9,f'19 NOV 2026  |  {self.page:02d}',8,color=GRAY)
    def end(self):self.c.showPage()
    def para(self,x,y,text,width=105,size=10,leading=5):
        for s in textwrap.wrap(text,width):self.text(x,y,s,size);y-=leading
        return y
    def block(self,x,y,title,lines,size=10):
        self.text(x,y,title,12,True,TEAL)
        for i,line in enumerate(lines):self.text(x,y-8-i*6,line,size,color=GRAY)
    def drawing(self,wires,x,y,s,stroke=INK):
        lo,hi=bounds(wires)
        def tr(p):return ((x+(p[0]-lo[0])*s)*mm,(y+(p[1]-lo[1])*s)*mm)
        self.c.setStrokeColor(colors.HexColor(stroke));self.c.setLineWidth(.65)
        for w in wires:
            for e in w:
                if e['type']=='CIRCLE':
                    cc=tr(e['center']);self.c.circle(*cc,e['radius']*s*mm,stroke=1,fill=0)
                elif e['type']=='ARC':
                    cc=tr(e['center']);r=e['radius']*s*mm
                    a,b=e['start_angle'],e['end_angle'];extent=(b-a)%360
                    self.c.arc(cc[0]-r,cc[1]-r,cc[0]+r,cc[1]+r,a,extent)
                else:
                    a,b=tr(e['start']),tr(e['end']);self.c.line(*a,*b)
        return hi-lo
    def dim_h(self,x,y,length,label):
        self.line(x,y,x+length,y,GRAY)
        for a in [x,x+length]:self.line(a,y-2,a,y+2,GRAY)
        self.text(x+length/2-10,y+2,label,9,True,GRAY)
    def dim_v(self,x,y,length,label):
        self.line(x,y,x,y+length,GRAY)
        for a in [y,y+length]:self.line(x-2,a,x+2,a,GRAY)
        self.c.saveState();self.c.translate((x-2)*mm,(y+length/2)*mm);self.c.rotate(90)
        self.c.setFont('Helvetica-Bold',9);self.c.drawCentredString(0,0,label);self.c.restoreState()
    def image(self,path,x,y,w,h):self.c.drawImage(str(path),x*mm,y*mm,width=w*mm,height=h*mm,preserveAspectRatio=True,anchor='c')
    def save(self):self.c.save()

b=Book(ROOT/'PDF/Drawings_Assembly_and_Verification.pdf')
b.start('Hybrid removable bin','Four laser-cut walls + floor + one PETG curve + four magnet-pocket inserts. Quantities below are for one bin.')
b.image(INTERNAL/'assembled.png',7,32,230,207)
b.rect(242,32,164,202)
b.block(250,222,'Master dimensions',[
 'Exterior 347.5 x 347.5 x 450',
 'Source XY limits 2.5 to 350.0',
 'Plywood walls 6.0 / floor 9.0',
 'Corner radii R75 exposed / R81 interior',
 'Bottom pocket centers 102.5 and 250.0',
 'Four pockets diameter 25.2 x 5 deep'])
b.block(250,163,'10 kg design target',[
 '15 kg supported proof-test procedure on page 13.',
 'CAD and geometric checks have been run.',
 'Physical load tests remain to be performed.',
 'Measured stock and coupons set the cutting fit.'])
b.block(250,113,'File conventions',[
 'STL and STEP component origins match the source.',
 'Laser DWGs contain finished-size CUT geometry.',
 'REFERENCE layer contains labels; disable for cutting.',
 'Apply measured kerf compensation once.',
 'C01 and M01 DWGs are reference views.'])
b.text(250,60,'Source: Bin Studio - Bin (1).stl',9,color=GRAY)
b.end()

for name in ['W01_rear','W02_right','W03_front','W04_left']:
    label=name.replace('_',' ')
    b.start(label,'Laser-cut 6 mm plywood. Source-coordinate joint positions and matching component names are retained.')
    s=.4;x=26;y=30
    wh=b.drawing(PRO[name],x,y,s)
    b.dim_h(x,y+wh[1]*s+7,wh[0]*s,f'{wh[0]:.2f}')
    b.dim_v(x+wh[0]*s+8,y,wh[1]*s,f'{wh[1]:.2f}')
    b.block(224,226,'Vertical corner joints',[
     'Six 36 nominal fingers at 72 pitch.',
     'Joint centers Z45 / 117 / 189 / 261 / 333 / 405.',
     'Wood-to-wood finished total gap 0.20.',
     'Wood-to-printed finished total gap 0.30.',
     'Gaps are independent of kerf compensation.'])
    centers=META[name]['floor_finger_centers']
    b.block(224,175,'Floor engagement',[
     f'{len(centers)} fingers, each 30 wide x 9 deep.',
     'Centers in the source wall-length coordinate',
     ' / '.join(f'{p:.2f}'for p in centers),
     'Tab bottoms at Z0. Main wall starts at Z9.',
     'End margin to the first/last floor finger is 28.'])
    if name in ['W03_front','W04_left']:
        b.block(224,121,'Curve interface',[
         'Nominal body starts at station 102.5.',
         'Finger extremity reaches station 96.5.',
         'Three diameter 3.4 through holes at station 120.5.',
         'Z centers 81 / 225 / 369.',
         'After laser cutting: exterior countersink',
         'diameter 6.3 x 90 degrees for flush M3 heads.'])
    else:
        b.block(224,121,'Orientation',[
         'Match labels in the assembly STEP.',
         'Rear fingers own both upper rear corners.',
         'Right wall closes the assembly last.',
         'Dry-fit before applying wood glue.'])
    b.rect(224,34,179,35);b.para(230,60,'Cut only the CUT layer of the matching DWG. See the separate full-scale profile PDF for a 1:1 vector outline.',width=78,size=10)
    b.text(x,y-6,'PROFILE SCALE 1 : 2.5',8,color=GRAY)
    b.end()

b.start('F01 floor','Laser-cut 9 mm plywood. Original exterior footprint and underside magnet centers are preserved.')
wh=b.drawing(PRO['F01_floor'],27,39,.5)
b.dim_h(27,222,wh[0]*.5,'347.5');b.dim_v(211,39,wh[1]*.5,'347.5')
b.block(234,225,'Pocket inserts',[
 'Four diameter 29.6 through holes.',
 'Centers (X,Y) in source coordinates',
 '(102.5,102.5) / (102.5,250)',
 '(250,102.5) / (250,250)',
 'Use M01 inserts to restore diameter 25.2 x 5 pockets.',
 'Insert outside diameter 29.2; radial epoxy gap 0.20.'])
b.block(234,169,'Floor-to-curve bolts',[
 'Three diameter 4.5 through holes on radius 100.',
 'Angles 22.5 / 45 / 67.5 degrees from +X.',
 'Centers  (92.388,38.268)',
 '         (70.711,70.711)',
 '         (38.268,92.388)',
 'After laser cutting: underside countersinks',
 'diameter 8 x 90 degrees for flush M4 heads.'])
b.block(234,101,'Curved edge',[
 'Nominal exposed arc R75 about source X0,Y0.',
 'Three 16 arc-width locating tabs in C01.',
 'Tab angles 22.5 / 45 / 67.5 degrees.',
 'Floor-notch clearance 0.30 total.'])
b.rect(233,34,174,30);b.para(239,55,'Dimensions describe the finished part. Cut a coupon in the actual 9 mm stock before cutting this floor.',width=74)
b.end()

b.start('C01 printed curved corner','One PETG part, printed upright. Overall CAD envelope 130 x 130 x 450 including internal screw flanges.')
b.drawing(SECTIONS['225.0'],29,143,.63)
b.dim_h(29,234,130*.63,'130 MAX')
b.text(30,130,'SECTION AT Z225',9,True,TEAL)
b.drawing(SECTIONS['13.0'],29,35,.65)
b.text(30,28,'SECTION AT Z13 / FLOOR BOLT PADS',8,True,TEAL)
b.drawing(SIDE,201,31,.43)
b.dim_v(267,31,450*.43,'450')
b.block(285,225,'Geometry and fit',[
 'Arc radii 75 and 81; wall 6.',
 'Straight wings end at X/Y102.5.',
 'Finger engagement 6; nominal height 36.',
 'Six finger bands on each vertical seam.',
 'Internal flanges 5 thick, finish at X/Y132.5.',
 'Three M3 seats on each flange.',
 'M3 captive nut AF5.8 x 2.6 deep.'],size=9)
b.block(285,159,'Floor bolt pads',[
 'Three pads at radius 100.',
 'Each pad diameter 20, 8 high above Z9.',
 'Necks 14 wide join the curve at radius 80.',
 'M4 captive nut AF7.2 x 3.4 deep.',
 'Three M4 x 20 countersunk floor screws.'],size=9)
b.block(285,103,'Print setup',[
 'Use a printer that accepts the 450 height.',
 'Print full height, open top upward.',
 'Use six perimeters as a starting profile.',
 'Slice the 6 mm shell substantially solid.',
 'Support pads, flange starts, fingers and nut traps.',
 'Check Q05 sample and inspect layer bonding.'],size=9)
b.end()

b.start('M01 magnet-pocket insert','Four identical PETG inserts. Recesses open downward when fitted to the floor.')
# Explicit dimensional section from the master primitives.
section=[[(0,0),(2,0)],[(2,0),(2,5)],[(2,5),(27.2,5)],[(27.2,5),(27.2,0)],
         [(27.2,0),(29.2,0)],[(29.2,0),(29.2,9)],[(29.2,9),(0,9)],[(0,9),(0,0)]]
w=[[{'type':'LINE','start':a,'end':c}for a,c in section]]
b.drawing(w,40,139,5)
b.dim_h(40,196,146,'29.2 OUTSIDE');b.dim_h(50,128,126,'25.2 POCKET')
b.dim_v(197,139,45,'9');b.dim_v(28,139,25,'5 POCKET DEPTH')
b.text(40,115,'SECTION / MOUNTED ORIENTATION',10,True,TEAL)
b.block(236,221,'Dimensions',[
 'Outside diameter 29.2; total height 9.',
 'Pocket diameter 25.2; depth 5.0 in CAD.',
 'Pocket roof approximately 4.',
 'Floor holes diameter 29.6 nominal.',
 'Radial adhesive gap 0.20.'])
b.block(236,170,'Manufacturing',[
 'Print with the closed roof on the build plate',
 'and the pocket upward; flip for installation.',
 'Check Q07 for the actual insert/floor fit.',
 'Use a compatible epoxy on cleaned, abraded surfaces.',
 'Keep both floor faces flush during bonding.',
 'Recheck pocket depth after curing.'])
b.block(236,106,'Magnets',[
 'Original four centers are retained.',
 'Verify actual magnet dimensions before bonding.',
 'Complete the floor load test before installing magnets.',
 'Magnets and all screws are purchased parts.'])
b.end()

b.start('Calibration boards and kerf samples','Seven total-clearance choices from 0.10 to 0.40, spaced in 0.05 increments.')
for name,x,y,s in [('Q01_wall_fit',22,55,.9),('Q02_floor_fit',236,135,.78)]:
    b.drawing(PRO[name],x,y,s)
    b.text(x,y-7,name,10,True,TEAL)
    if name.startswith('Q01'):
        for row,yy in enumerate([30,65,120,155]):
            count=4 if row%2==0 else 3
            for j in range(count):
                gap=.1+.05*(j+(0 if row%2==0 else 4))
                b.text(x+(25+50*j)*s-4,y+(yy-13)*s,f'{gap:.2f}',8)
    else:
        for i in range(7):
            b.text(x+(25+50*(i%4))*s-4,y+(30+35*(i//4)-13)*s,f'{.1+.05*i:.2f}',8)
b.block(236,118,'Q01 / nominal 6 mm stock',[
 '200 x 180 board.',
 'Lower rows: slots 36+gap wide and 6+gap high.',
 'Upper rows: slots 30+gap wide and 9+gap high.',
 'Use Q03 and Q04 tab blanks.'])
b.block(236,70,'Q02 / nominal 9 mm stock',[
 '200 x 100 board. Use the Q08 6 mm wall-tab blank.',
 'Slots 30+gap by 6+gap.',
 'Each board also has a nominal 20 x 20 kerf plug.',
 'Measure plug and opening on both axes.',
 'Kerf estimate = (opening - plug) / 2.',
 'Q02 also tests a 4.5 hole for the floor bolt.'])
b.end()

b.start('Small samples before the full bin','Use the same materials, orientation and laser settings intended for the production parts.')
for name,x,y,s in [('Q03_wall_tab',25,158,1.3),('Q04_floor_tab',118,158,1.3),
                    ('Q06_curve_wall_sample',226,143,1.1),('Q07_insert_fit',26,51,1.4)]:
    b.drawing(PRO[name],x,y,s);b.text(x,y-7,name,9,True,TEAL)
b.block(318,217,'Q05 printed sample',[
 '42.5 x 11 x 72 envelope.',
 'Exact cropped curve-wing geometry.',
 'Pair with Q06 in 6 mm plywood.',
 'Print in the full curve orientation.',
 'Check insertion and captive nut fit.'],size=9)
b.block(220,106,'Select and record',[
 'Q08 is the 30-wide, 6-thick tongue for the Q02 floor coupon.',
 'Q07 holes use 0.10 / 0.20 / 0.30 radial insert clearance.',
 'Choose the smallest gap that slides without forcing.',
 'Measure stock in several places with calipers.',
 'Record kerf separately for 6 and 9 mm sheets.',
 'Regenerate the nominal files with those measurements.'])
b.end()

b.start('Assembly sequence','The straight insertion sweeps were checked continuously across 12 mm of travel.')
b.image(INTERNAL/'exploded.png',5,31,224,205)
b.block(235,225,'Dry-fit before glue',[
 '1. Stand C01 upright with all captive nuts in place.',
 '2. Slide W03 front toward C01 along -X.',
 '3. Slide W04 left toward C01 along -Y.',
 '4. Bring W01 rear into W04 along -Y.',
 '5. Close W02 right toward the other walls along -X.',
 '6. Raise F01 from below into the wall and curve tabs.',
 '7. Fit the six M3 and three M4 screws loosely.',
 '8. Check square, floor level and pocket centers.'])
b.block(235,150,'Bond and fasten',[
 'Remove loose laser char from bonding surfaces.',
 'Use a suitable structural wood glue at plywood seams.',
 'Reassemble in the tested order while glue is workable.',
 'Clamp square without crushing the plywood edges.',
 'Tighten screws with flush heads, without crushing wood.',
 'Bond M01 inserts flush after checking their fit.',
 'Allow the specified full adhesive cure before loading.'])
b.block(235,76,'Hardware for one bin',[
 '6 x M3 x 12, 90-degree countersunk screws + M3 nuts.',
 '3 x M4 x 20, 90-degree countersunk screws + M4 nuts.',
 'Wood glue, insert epoxy and four magnets as selected.'],size=9)
b.end()

b.start('Verification results','Numerical checks apply to the supplied nominal-stock geometry and exported files.')
tests=REPORT['tests'];passed=sum(t['pass']for t in tests)
b.rect(18,205,384,30);b.text(25,218,f'{passed} / {len(tests)} recorded checks passed',21,True,TEAL)
b.block(22,189,'CAD and manufacturing checks',[
 'Single valid solid per component and watertight, consistently oriented meshes.',
 'No unintended final-assembly intersections. Original exterior envelope retained.',
 'Continuous insertion sweeps for the four walls and the floor.',
 'Closed, nonduplicated cut contours and remaining wood around isolated holes.',
 'STEP volumes checked after reimport. STL volumes compared with the master solids.',
 'DWGs written by ODA, converted back, then independently read by LibreDWG.',
 'DWG units, entity geometry and R2000 file signatures verified.'])
b.block(22,123,'Floor screening calculation',[
 'Uniform payload; one simply supported beam strip, span and width 335.5 mm.',
 'Assumed plywood modulus E = 3,000 MPa. Floor thickness 9 mm.',
 '10 kg: estimated deflection 0.79 mm; bending stress 0.91 MPa.',
 '15 kg: estimated deflection 1.18 mm; bending stress 1.36 MPa.',
 'This screen omits local pockets, joints, material variation and concentrated loads.'])
b.rect(18,36,384,32);b.para(24,59,'The 10 kg capacity is a design target. Physical load tests have not been performed. The next page defines the proof and handling tests for a manufactured sample.',width=145,size=11)
b.end()

b.start('Physical acceptance test','Working-load target 5-10 kg per bin. Proof load 15 kg, after full adhesive cure and fit approval.')
b.block(22,226,'1 / Calibration and baseline',[
 'Approve coupons and countersink samples before committing to the complete parts.',
 'Inspect all plywood bonds, screw seats, captive nuts, magnet inserts and printed layers.',
 'Set the bin on the same supports used in the assembly. Record floor-center height,',
 'joint gaps and overall squareness before adding load.'])
b.block(22,177,'2 / Supported proof load',[
 'Use evenly distributed dry weights. Increase from 5 kg to 10 kg, then 15 kg.',
 'Hold the 15 kg load for 60 minutes with the bin supported as installed.',
 'Acceptance target: floor deflection no more than 2 mm, no new cracking,',
 'no delamination, no fastener movement and no progressive joint opening.',
 'Unload and wait 10 minutes. Target residual floor movement at most 0.5 mm.'])
b.block(22,117,'3 / Handling trial at the 10 kg working target',[
 'Use two people for the first trial, with a catch surface immediately below.',
 'Lift from two opposing plywood rims and hold just clear of the catch surface.',
 'Perform ten lift-and-set-down cycles. Reinspect floor joints and the curve fixings.',
 'Reject a sample with cracks, permanent distortion or loosening. Record results',
 'before repeating the geometry for the other three bins.'])
b.rect(18,35,384,29);b.para(24,55,'A calculated fit and a supported proof test answer different questions. Record the actual material, cut settings, glue, print profile and observed results with the sample.',width=150,size=10)
b.end();b.save()

# Actual-size cutting pages. Source is the same exact vector entity list used for DWG.
c=canvas.Canvas(str(ROOT/'PDF/Full_Scale_Cutting_Profiles.pdf'))
for name,wires in PRO.items():
    lo,hi=bounds(wires);size=hi-lo
    width=max(150.,size[0]+40);height=max(115.,size[1]+60)
    c.setPageSize((width*mm,height*mm))
    c.setFont('Helvetica-Bold',10);c.setFillColor(colors.HexColor(TEAL))
    c.drawString(12*mm,(height-13)*mm,name+' / 1:1 / mm')
    c.setFont('Helvetica',8);c.drawString(12*mm,(height-20)*mm,'NOMINAL STOCK - calibrate fit; apply measured kerf once. CUT contour only.')
    c.setStrokeColor(colors.black);c.setLineWidth(.12*mm)
    x=20;y=27
    def tr(p):return((x+p[0]-lo[0])*mm,(y+p[1]-lo[1])*mm)
    for w in wires:
        for e in w:
            if e['type']=='LINE':c.line(*tr(e['start']),*tr(e['end']))
            elif e['type']=='CIRCLE':c.circle(*tr(e['center']),e['radius']*mm,stroke=1,fill=0)
            else:
                cc=tr(e['center']);r=e['radius']*mm
                c.arc(cc[0]-r,cc[1]-r,cc[0]+r,cc[1]+r,e['start_angle'],(e['end_angle']-e['start_angle'])%360)
    c.setStrokeColor(colors.HexColor(TEAL));c.setLineWidth(.5)
    c.line(20*mm,12*mm,120*mm,12*mm)
    for xx in [20,120]:c.line(xx*mm,10*mm,xx*mm,14*mm)
    c.setFont('Helvetica',8);c.drawString(48*mm,16*mm,'100 mm scale check')
    c.showPage()
c.save()
assert len(PdfReader(ROOT/'PDF/Drawings_Assembly_and_Verification.pdf').pages)==13
assert len(PdfReader(ROOT/'PDF/Full_Scale_Cutting_Profiles.pdf').pages)==len(PRO)
print('Created booklet and full-scale profiles',len(PRO),'profile pages',flush=True)
