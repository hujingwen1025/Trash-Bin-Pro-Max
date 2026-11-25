"""Read-only CAD illustrations. Load verified STEP files; never rebuild/export CAD."""
from pathlib import Path
import sys,json,re,math
from functools import lru_cache
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle,Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
from shapely.geometry import Point
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Preview';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'Software'));from geometry import Geometry,tray_polygon
G=Geometry();META=json.loads((ROOT/'Verification/parts.json').read_text());INST={x['instance']:x for x in json.loads((ROOT/'Verification/instance_transforms.json').read_text())}
INK='#263749';BG='#ffffff';CONTEXT='#d9dfe5'
PAL={'M01':'#a3adb9','M02':'#778695','M03':'#939fae','M04':'#c4cbd3','M05':'#8ba8ca','M06':'#d4a05b','M07':'#8e85b0','M08':'#8ca4b9','M09':'#6488ad','M10':'#e0e5eb','M11':'#c5ab70','M12':'#96afb9','M13':'#869eab','M14':'#a7b7c9','M15':'#ba8b7e','M16':'#8e99a5','M17':'#7095b9','M18':'#bda671','M19':'#b69b62','M20':'#8b9da9','M21':'#9aabb5','M22':'#bd9864','M23':'#8b99a8','M24':'#bac9d7','M25':'#8e9cab','M26':'#9da9b6','M28':'#718ba7','P01':'#ac98ba','P02':'#b77871','P03':'#8bae94','P04':'#cf968a','P05':'#c6b49b','P07':'#b9a8c9','P08':'#7a8791','P09':'#b8a5ca','P10':'#a6b8b4'}
LEGS=['#6c91bc','#cb9d68','#80a58b','#b398bb','#baa866','#7f9fa8']
BINS={'B1':'#8ba9c4','B2':'#94b29e','B3':'#cfaf7e','B4':'#b9a0bd'}
VISUAL_LOG=[]

def key_for(name):
 if name in INST:return INST[name]['part']
 if 'servo' in name:return 'Servo_Envelope'
 if 'bearing' in name:return '608_Bearing'
 if name.endswith('36T'):return 'Pulley36'
 if name.endswith('20T'):return 'Pulley20'
 if 'idler' in name:return 'Idler'
 if re.match(r'D\d stop',name):return 'Stop_Pin'
 if 'guide post' in name:return '2020_Extrusion'
 if 'rest tower' in name:return 'Rest_Tower'
 if 'frame post' in name:return 'Outer_Post_820'
 if 'frame ' in name and 'rail' in name:return 'Outer_Rail_710'
 if 'upright' in name:return 'Backstop_Upright_320'
 if 'middle rail' in name:return 'Backstop_Rib_290'
 if name.endswith('foam'):return 'Foam_Pad'
 if name.startswith('foot'):return 'Rubber_Foot'
 return 'REFERENCE'

def colour(name,key):
 if key.startswith('M13')and re.match(r'L[1-6]',name):return LEGS[int(name[1])-1]
 if key.startswith('P06'):return BINS[name[:2]]
 if key=='Servo_Envelope':return '#505c6b'
 if key=='608_Bearing':return '#a9c4cf'
 if key.startswith('Pulley'):return '#cba66b'
 if key=='Idler':return '#b98c60'
 if key=='Stop_Pin':return '#b97c78'
 if key=='Foam_Pad':return '#a7b4bc'
 if key=='Rubber_Foot':return '#697882'
 if key.endswith('Extrusion')or key.startswith(('Outer_','Backstop_')):return '#c4ccd4'
 if key.startswith('P04')and name.endswith(' b'):return '#dfb9ad'
 return PAL.get(key[:3],'#b8c2cb')

@lru_cache(None)
def scene(filename='R07_Level_Assembly.step'):
 ass=cq.Assembly.importStep(str(ROOT/'04_Assembly'/filename));result={}
 for shape,name,loc,_ in ass:
  label=name[len(ass.name)+1:];result[label]=shape.moved(loc)
 return result

@lru_cache(None)
def world_faces(name,filename='R07_Level_Assembly.step'):
 s=scene(filename)[name];vertices,triangles=s.tessellate(.6,.28);v=np.array([p.toTuple()for p in vertices]);return v[np.array(triangles)]

@lru_cache(None)
def part_faces(key):
 m=META[key];s=cq.importers.importStep(str(ROOT/m['folder']/'STEP'/f'{key}.step')).val();v,t=s.tessellate(.45,.25);return np.array([p.toTuple()for p in v])[np.array(t)]

def item(name,shift=(0,0,0),basis=None,origin=None,context=False,filename='R07_Level_Assembly.step',label=None):
 f=world_faces(name,filename).copy()
 if basis is not None:f=(f-np.asarray(origin))@np.asarray(basis)
 f+=np.asarray(shift)
 key=key_for(name);return {'name':label or name,'key':key,'f':f,'color':CONTEXT if context else colour(name,key)}

def raw(key,name=None,shift=(0,0,0),R=None,color=None):
 f=part_faces(key).copy()
 if R is not None:f=f@np.asarray(R).T
 f+=shift;return {'name':name or key,'key':key,'f':f,'color':color or colour(name or key,key)}

def shade(f,col):
 a=f[:,1]-f[:,0];b=f[:,2]-f[:,0];n=np.cross(a,b);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
 light=np.array([.35,-.45,.82]);light/=np.linalg.norm(light);second=np.array([-.6,.2,.7]);second/=np.linalg.norm(second)
 intensity=.80+.13*np.abs(n@light)+.07*np.abs(n@second)
 return np.clip(np.array(to_rgb(col))[None,:]*intensity[:,None],0,1)

def draw(ax,items):
 for x in items:ax.add_collection3d(Poly3DCollection(x['f'],facecolors=shade(x['f'],x['color']),edgecolor='none',linewidth=0,zsort='average'))

def frame_view(ax,items,view=(23,-57),limits=None):
 if limits is None:
  allpts=np.concatenate([x['f'].reshape(-1,3)for x in items]);lo=allpts.min(0);hi=allpts.max(0);span=hi-lo;pad=np.maximum(span*.09,3);lo-=pad;hi+=pad
 else:lo=np.array(limits[0],float);hi=np.array(limits[1],float)
 span=hi-lo;ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(np.maximum(span,10),zoom=1.18);ax.set_proj_type('ortho');ax.view_init(elev=view[0],azim=view[1]);ax.set_axis_off()

def bubble(ax,point,num,offset=(18,18),col=INK,total=6,position=None):
 x,y,_=proj3d.proj_transform(*point,ax.get_proj())
 side=(num-1)%2;row=(num-1)//2;rows=(total+1)//2
 xytext=position or (.08 if side==0 else .92,.84-row*(.65/max(rows-1,1)))
 ax.annotate(str(num),(x,y),xytext=xytext,textcoords='axes fraction',ha='center',va='center',fontsize=14,weight='bold',color=INK,bbox={'boxstyle':'circle,pad=.27','fc':'white','ec':col,'lw':1.2},arrowprops={'arrowstyle':'-','color':INK,'lw':.85},zorder=10000,annotation_clip=False)

def arrow(ax,start,end,col='#566779'):
 d=np.array(end)-np.array(start);ax.quiver(*start,*d,color=col,arrow_length_ratio=.20,linewidth=1.6)

def shot(file,title,items,labels=(),note='',view=(23,-57),arrows=(),limits=None):
 fig=plt.figure(figsize=(14,8.4),facecolor=BG);ax=fig.add_axes([.015,.115,.70,.77],projection='3d');frame_view(ax,items,view,limits);draw(ax,items)
 fig.text(.035,.945,title,size=22,weight='bold',color=INK)
 fig.text(.735,.865,'PART KEY / ASSEMBLY ACTION',size=13,weight='bold',color=INK)
 refs=[];bubble_positions={}
 for side in (0,1):
  group=[]
  for index,entry in enumerate(labels):
   if index%2!=side:continue
   target=next(x for x in items if x['name']==entry[0]);point=target['f'].reshape(-1,3).mean(0)
   group.append((index+1,proj3d.proj_transform(*point,ax.get_proj())[1]))
  for rank,(number,_)in enumerate(sorted(group,key=lambda q:-q[1])):bubble_positions[number]=(.08 if side==0 else .92,.84-rank*(.65/max(len(group)-1,1)))
 for num,entry in enumerate(labels,1):
  target,text,*off=entry;x=next((x for x in items if x['name']==target),None)
  if x is None:raise KeyError(target)
  point=x['f'].reshape(-1,3).mean(0);offset=off[0]if off else((20,18)if num%2 else(-20,-18));bubble(ax,point,num,offset,x['color'],len(labels),bubble_positions[num]);y=.80-(num-1)*min(.118,.63/max(len(labels)-1,1))
  fig.patches.append(Rectangle((.735,y-.007),.016,.021,transform=fig.transFigure,facecolor=x['color'],edgecolor=INK,lw=.4))
  fig.text(.763,y,str(num)+'. '+text,size=15,linespacing=1.35,color=INK,va='top');refs.append({'label':num,'instance':target,'part':x['key'],'text':text})
 for start,end in arrows:arrow(ax,start,end)
 fig.text(.035,.055,note,size=12,color='#536474',wrap=True);fig.text(.035,.025,'Illustration colours identify parts only. Geometry is from the verified CAD; exploded gaps are illustrative.',size=11,color='#667380')
 fig.savefig(OUT/file,dpi=180,facecolor=BG);plt.close(fig);VISUAL_LOG.append({'image':file,'labels':refs,'geometry_source':'existing verified STEP, read only'})
 print('Rendered',file,flush=True)

def select(predicate,**kwargs):return[item(n,**kwargs)for n in scene()if predicate(n,key_for(n))]
def key_is(*prefixes):return lambda n,k:k.startswith(prefixes)
def drive_basis(i=0):return np.column_stack((G.u[i]*G.c['drive_orientation'][i],G.v[i]*G.c['drive_orientation'][i],[0,0,1])),G.B[i]+[0,0,G.c['crank_axis_global_z_mm']]

def render_system(exploded=False):
 if exploded:
  items=[]
  for n in scene():
   k=key_for(n)
   if not(n.startswith(('D','L'))or n in('fixed deck','carrier','tray','perimeter frame')or n.startswith(('brace','deck rib'))):continue
   delta=np.zeros(3)
   if n.startswith('D'):i=int(n[1])-1;delta=G.B[i]/np.linalg.norm(G.B[i])*60
   elif n.startswith('L'):delta=np.array([0,0,85.])
   elif n=='tray':delta=np.array([0,0,300.])
   elif n=='perimeter frame'or n.startswith('brace'):delta=np.array([0,0,230.])
   elif n=='carrier':delta=np.array([0,0,160.])
   items.append(item(n,shift=delta))
  shot('Exploded_Assembly.png','Platform layers - exploded assembly reference',items,[('tray','M10 loading sheet'),('perimeter frame','M18 perimeter frame\n+ four M11 braces'),('carrier','M09 moving carrier'),('L1 tube','Six L1-L6 links'),('D1 crank16','Six D1-D6 drive cells'),('fixed deck','M08 fixed deck')],note='Assembly direction: fixed deck > drive cells > links > carrier > braces/frame > loading sheet.',view=(18,-55))
  return
 items=select(lambda n,k:not(n.startswith(('B3','B4'))and(k.startswith(('P06','M24','M25','M26','P07'))or'foam'in n or'upright'in n or'guide post'in n or'middle rail'in n)))
 base=cq.importers.importStep(str(ROOT/'04_Assembly/Base_Interface_With_Mounting_Holes.step')).val();v,t=base.tessellate(1,.3);items.append({'name':'base','key':'BASE','f':np.array([p.toTuple()for p in v])[np.array(t)],'color':'#d4c2a2'})
 for b in('B1','B2'):
  s=cq.importers.importStep(str(ROOT.parent/'Rev 06 - 10mm Basswood Hybrid Bins/STEP'/f'{b}_Assembly.step')).val().translate((0,0,20));v,t=s.tessellate(1,.4);items.append({'name':b+' bin','key':'R06','f':np.array([p.toTuple()for p in v])[np.array(t)],'color':'#d2dbdf'if b=='B1'else'#d5ddd1'})
 shot('Complete_System.png','Four-bin sorter - parts separated by colour',items,[('tray','M10 loading tray'),('L1 tube','Colour-coded links\nL1-L6'),('D1 crank16','Amber crank plates\nM06'),('B1 guide','P06 discharge guides'),('fixed deck','M08 fixed deck'),('frame post1/1','Neutral support frame')],note='Cutaway: front B3/B4 bins, guides and backstops hidden to expose the mechanism. All four remain in the CAD.',view=(23,-55))

def plan():
 fig,ax=plt.subplots(figsize=(10,10),facecolor='white');ax.set_aspect('equal');ax.set_xlim(-440,440);ax.set_ylim(-440,440)
 for x,y,b in[(1,1,'B1'),(-1,1,'B2'),(1,-1,'B3'),(-1,-1,'B4')]:
  ax.add_patch(Rectangle((2.5 if x>0 else-350,2.5 if y>0 else-350),347.5,347.5,facecolor=BINS[b],alpha=.19,edgecolor=INK));ax.text(x*275,y*275,b,ha='center',color=INK,size=15)
 ax.add_patch(Rectangle((-375,-375),750,750,fill=False,edgecolor=INK,lw=1.6));ax.add_patch(Circle((0,0),73.75,color='#c8d0d8'))
 p=tray_polygon();ax.fill(p[:,0],p[:,1],color=PAL['M10'],edgecolor=INK)
 for b in G.c['bin_azimuth_deg']:
  R,t=list(G.path(b,2))[-1];q=np.c_[p,np.full(len(p),G.c['tray_surface_above_anchor_mm'])]@R.T+t;ax.plot(*np.r_[q[:,:2],q[:1,:2]].T,'--',color=BINS[b],lw=2,label=b+' dump')
 ax.annotate('',(-375,-410),(375,-410),arrowprops={'arrowstyle':'<->','color':INK});ax.text(0,-430,'750 overall frame / 700 original base',ha='center',size=11)
 ax.set_title('Top view - quadrant colours and tray envelopes',loc='left',size=16,color=INK);ax.legend(loc='upper left',fontsize=9);ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');ax.grid(alpha=.12);fig.savefig(OUT/'Top_View.png',dpi=180,bbox_inches='tight');plt.close(fig)

def motion_views():
 fig=plt.figure(figsize=(14,10),facecolor='white')
 for k,b in enumerate(G.c['bin_azimuth_deg']):
  ax=fig.add_subplot(2,2,k+1,projection='3d');R,t=list(G.path(b,2))[-1];a,H,P=G.points(R,t);z=np.array([0,0,G.c['crank_axis_global_z_mm']]);items=[]
  q=np.c_[tray_polygon(),np.full(8,G.c['tray_surface_above_anchor_mm'])]@R.T+t+z;allpts=np.r_[G.B+z,H+z,P+z,q];lo=allpts.min(0)-30;hi=allpts.max(0)+30;frame_view(ax,[],(20,-55),(lo,hi))
  for i in range(6):
   line=np.array([G.B[i],H[i],P[i]])+z;ax.plot(*line.T,color=LEGS[i],lw=3);ax.text(*(H[i]+z),str(i+1),color=INK,size=11)
  ax.add_collection3d(Poly3DCollection([q],facecolor=PAL['M10'],edgecolor=INK,lw=.8));ax.set_title(b+' | 55 deg | 85 mm translation',loc='left',size=15,color=INK)
 fig.suptitle('Four discharge poses - numbered, colour-coded legs',color=INK,size=21);fig.text(.06,.025,'Kinematic diagram. Item contact and real routing still require physical qualification.',size=12,color='#536474');fig.savefig(OUT/'Four_Dump_Poses.png',dpi=170);plt.close(fig)

def orthographic():
 for title,elev,azim in[('Front',0,-90),('Right',0,0),('Rear',0,90),('Left',0,180),('Top',90,-90),('Mechanism',18,-55)]:
  if title=='Mechanism':items=select(lambda n,k:n.startswith(('D','L','brace'))or n in('carrier','perimeter frame','fixed deck'))
  else:items=select(lambda n,k:True)
  labels=[('D1 cradle','P01 servo cradle'),('D1 crank16','M06 crank'),('L1 tube','L1 link'),('carrier','M09 carrier')]
  shot(title+'_View.png',title+' view - differentiated parts',items,labels,note='M10 loading sheet, discharge guides and outer frame hidden in mechanism view.'if title=='Mechanism'else'Nominal CAD reference. Side views use the same component colours as the assembly steps.',view=(elev,azim))

def assembly_images():
 #01-04: structural post and fixed deck. Shroud removed so the core remains visible.
 names=['base backplate','post bottom','post core','post top','fixed deck']+[n for n in scene()if n.startswith('deck rib')]
 offsets={'base backplate':(0,0,-25),'post bottom':(0,0,10),'post top':(0,0,55),'fixed deck':(0,0,110)}
 items=[item(n,shift=offsets.get(n,(0,0,110)if n.startswith('deck rib')else(0,0,20)))for n in names]
 shot('Assembly_01_Support.png','Steps 01-04 | Base, structural post and fixed deck',items,[('base backplate','M03 underside backplate'),('post bottom','M01 bottom endcap'),('post core','M02 steel core'),('post top','M01 top endcap'),('fixed deck','M08 deck + six M28 ribs')],note='Exploded vertical gaps show assembly order. Weld captive top-cap nuts before closing the core; shroud omitted.',view=(12,-55))
 F,B=drive_basis()
 frame_names=[n for n in scene()if n.startswith('D1 ')and('cheek'in n or'foot'in n or'bearing'in n)]
 items=[item(n,basis=F,origin=B)for n in frame_names]
 shot('Assembly_05_Pedestal.png','Step 05 | Build one bearing pedestal set',items,[('D1 cheek-44','M05 common rear cheek'),('D1 cheek-22','M05 D1 finished cheek'),('D1 front cheek','M17 D1 auxiliary cheek'),('D1 foot-44','Three M14 angle feet'),('D1 output bearing -29.5','608 bearings - align\nwith a dummy shaft')],note='Keep D1-D6 finished parts labelled. Leave feet loose until both shafts turn freely.',view=(19,-57))
 names=[n for n in scene()if n.startswith('D1 ')and('cheek'in n or'foot'in n or'bearing'in n or'shaft'in n or'key'in n or'crank'in n)]
 items=[item(n,basis=F,origin=B,context=('cheek'in n or'foot'in n))for n in names]
 shot('Assembly_06_Cranks.png','Step 06 | Keyed shafts, hub and paired cranks',items,[('D1 output shaft','M20 output shaft'),('D1 crank hub','M19 keyed double hub'),('D1 crank16','Two M06 crank plates'),('D1 input shaft','M21 input shaft'),('D1 output key0','M22 keys carry torque')],note='Crank layout shown at REST. Set actual crank zeros using the calibration table, not the picture.',view=(21,-65))
 belt_diagram()
 names=[n for n in scene()if n.startswith('D1 ')and not('output key'in n)]
 items=[item(n,basis=F,origin=B,shift=(0,-45,0)if n=='D1 belt guard'else(0,0,0),context=('cheek'in n or'foot'in n or'bearing'in n))for n in names]
 shot('Assembly_09_Motor_Guard.png','Steps 08-09 | Motor, adapter, stops and guard',items,[('D1 servo','HTD-85H body envelope'),('D1 cradle','P01 cradle + two straps\n(straps not modelled)'),('D1 horn adapter','M07 adapter: match-drill\nthe real metal horn'),('D1 stop0','Two supported stop pins'),('D1 belt guard','P10 guard moved outward\nfor visibility')],note='Verify the real horn/centre screw and complete axial stack on one cell before the other five.',view=(20,-45),arrows=[((35,-100,-45),(35,-70,-45))])
 # Lower universal: use the real L1 geometry, viewed in the fork frame.
 _,H,P=G.points(np.eye(3),[0,0,G.c['rest_height_mm']]);H+=np.array([0,0,G.c['crank_axis_global_z_mm']]);P+=np.array([0,0,G.c['crank_axis_global_z_mm']]);rod=(P[0]-H[0])/G.d[0];xx=np.cross(G.v[0],rod);xx/=np.linalg.norm(xx);yy=np.cross(rod,xx);JF=np.column_stack((xx,yy,rod))
 names=['L1 cross','L1 lower fork','L1 pivot-1','L1 pivot1','L1 tube'];items=[]
 for n in names:
  shift=(0,0,40)if n=='L1 lower fork'else(0,0,80)if n=='L1 tube'else(-15,0,0)if n=='L1 pivot-1'else(15,0,0)if n=='L1 pivot1'else(0,0,0)
  x=item(n,basis=JF,origin=H[0],shift=shift)
  if n=='L1 tube':x['f']=x['f'][x['f'].mean(1)[:,2]<145]
  items.append(x)
 shot('Assembly_10_Lower_Joint.png','Step 10 | Lower universal joint - exploded',items,[('L1 cross','P02 cross: primary\n4.2 mm through bore'),('L1 lower fork','P03 fork + M3 inserts'),('L1 pivot-1','Two M16 smooth-tip\npivots; lock jam nuts'),('L1 tube','M13 tube shown cropped')],note='Move the fork over the cross; engage each smooth tip 2.5 mm in its blind seat. Add the purchased primary pin/spacers at the crank.',view=(17,-64),arrows=[((-31,0,0),(-17,0,0)),((31,0,0),(17,0,0)),((0,0,58),(0,0,30))])
 tube_diagram()
 # Upper cup halves separated along their existing socket normal.
 xform=np.array(INST['L1 socket a']['transform']);sx=xform[:3,0];sy=xform[:3,1];nn=xform[:3,2];SF=np.column_stack((sx,-sy,-nn))
 names=['L1 socket a','L1 socket b','L1 ball stud','L1 upper coupler'];items=[]
 for n in names:
  delta=(0,0,-26)if n=='L1 socket a'else(0,0,26)if n=='L1 socket b'else(0,0,-45)if n=='L1 upper coupler'else(0,0,0)
  items.append(item(n,basis=SF,origin=P[0],shift=delta))
 shot('Assembly_12_Upper_Joint.png','Step 12 | Ball stud and split socket - exploded',items,[('L1 ball stud','M12 part ID: 16 mm ball\nwith M4 threaded stem'),('L1 upper coupler','P05 coupler + M4 insert'),('L1 socket a','P04 lower half'),('L1 socket b','Identical P04 half, flipped')],note='Screw the stud into the insert and lock its jam nut. Enclose the ball with both halves; keep the lips intact.',view=(10,-63),arrows=[((0,0,28),(0,0,12)),((0,0,-28),(0,0,-12))])
 names=['carrier']+[n for n in scene()if re.match(r'L[1-6] (wedge|socket [ab])$',n)]
 items=[item(n,shift=(0,0,-30)if n.startswith('L')else(0,0,0))for n in names]
 shot('Assembly_14_Carrier.png','Steps 13-14 | Labelled sockets under the carrier',items,[('carrier','M09 carrier - inclined\nM3 taps after cutting'),('L1 wedge','P09 L1 wedge'),('L2 wedge','P09 L2 wedge'),('L3 wedge','P09 L3 wedge'),('L4 wedge','P09 L4 wedge'),('L5 wedge','P09 L5 wedge'),('L6 wedge','P09 L6 wedge')],note='All six wedges retain L1-L6 IDs. Their flat faces meet M09; the socket groups are lowered 30 mm in this view.',view=(-43,-55))
 names=['carrier','tray','perimeter frame']+[n for n in scene()if n.startswith('brace')];items=[]
 for n in names:
  delta=135 if n=='tray'else 85 if n=='perimeter frame'else 40 if n.startswith('brace')else 0
  items.append(item(n,shift=(0,0,delta)))
 brace=next(n for n in scene()if n.startswith('brace'))
 shot('Assembly_15_Tray.png','Step 15 | Loading tray - separate the four layers',items,[('tray','M10 - 1 mm loading sheet'),('perimeter frame','M18 perimeter angle ring'),(brace,'Four M11 formed\nU-channel braces'),('carrier','M09 - 4 mm carrier')],note='Exploded gaps are illustrative. At the eight root screws: carrier > 3.5 mm spacers > brace flange > tray. Use flush heads.',view=(24,-53),arrows=[((0,0,965),(0,0,935))])
 items=select(lambda n,k:n.startswith(('D','L'))or n in('fixed deck','carrier')or n.startswith(('rest pad','rest tower')),context=False)
 shot('Assembly_16_Links.png','Step 16 / 25 | Six numbered links and supported carrier',items,[(f'L{i+1} tube',f'L{i+1} connects to drive D{i+1}')for i in range(6)],note='REST layout shown. During initial link attachment, support the ACTIVE upper-joint plane at Z875.6; follow Step 25 calibration.',view=(15,-58))
 # Frame and four panels: hide the two front panels only in this instructional view.
 items=select(lambda n,k:k.startswith(('M23','M25','M26'))or k.startswith(('Outer_','Backstop_'))or n.startswith('foot'))
 for n in('B1 backstop','B1 foam','B2 backstop','B2 foam'):
  items.append(item(n))
 shot('Assembly_18_Frame.png','Steps 17-18 | Outer frame, bridges and padded panels',items,[('corner outrigger1/1','Four M23 outriggers'),('frame post1/1','Four 820 mm posts'),('frame X rail1/500','710 mm rails at\nZ500 and Z800'),('B1 short bridge1/487','M25 short bridges'),('B1 long bridge484','M26 anti-rack bridge'),('B1 backstop','M24 panel + foam')],note='Two front panels omitted for access. Install all four. Short and long bridges triangulate each panel support.',view=(20,-53))
 # One guide module exploded vertically; exact geometry, simplified purchased posts.
 az=np.deg2rad(G.c['bin_azimuth_deg']['B1']);u=np.array([np.cos(az),np.sin(az),0]);v=np.array([-np.sin(az),np.cos(az),0]);F=np.column_stack((u,v,[0,0,1]));O=np.array([0,0,477]);names=['B1 guide','B1 guide cap-150','B1 guide cap150','B1 guide post-150','B1 guide post150']
 items=[item(n,basis=F,origin=O,shift=(0,0,55)if n=='B1 guide'else(0,0,22)if'cap'in n else(0,0,0))for n in names]
 shot('Assembly_20_Guide.png','Steps 19-20 | One removable guide module',items,[('B1 guide','P06 printed guide +\nsmooth sliding liner'),('B1 guide cap-150','Two P07 caps'),('B1 guide post-150','Two 92 mm 2020 posts'),('B1 guide cap150','M5 studs pass through\ncaps into blind inserts')],note='Guide and caps lifted to show order. Assemble at the verified heights; remove the whole module with two underside thumb screws.',view=(12,-58),arrows=[((205,150,190),(205,150,160)),((205,-150,190),(205,-150,160))])
 colour_key()
 (OUT/'Assembly_Illustration_Index.json').write_text(json.dumps(VISUAL_LOG,indent=2))

def belt_diagram():
 fig,ax=plt.subplots(figsize=(12,7.5),facecolor='white');A=np.array([0,0]);B=np.array([40,-96]);C=np.array([50.3,-44]);ra=36*5/(2*np.pi);rb=20*5/(2*np.pi)
 loop=unary_union([Point(*p).buffer(r,resolution=128)for p,r in((A,ra),(B,rb),(C,rb))]).convex_hull
 ax.plot(*loop.exterior.xy,color=INK,lw=3)
 for p,r,col,label in[(A,ra,'#d3b378','36T OUTPUT'),(B,rb,'#ad9ac0','20T INPUT'),(C,rb,'#bc9a6e','20T IDLER')]:
  ax.add_patch(Circle(p,r,fc=col,ec=INK,lw=1));ax.add_patch(Circle(p,4,fc='white',ec=INK,lw=.8));ax.annotate(label,p,xytext=(-35,35)if label.startswith('36')else(-100,-15)if label.endswith('INPUT')else(25,10),textcoords='offset points',fontsize=16,arrowprops={'arrowstyle':'-','color':INK})
 ax.plot([40,50.3],[-74,-44],'--',color='#ba8b7e',lw=2);ax.plot(40,-74,'o',color='#ba8b7e');ax.text(67,-89,'M15 tensioner\npivot 40 / -74\nnominal idler 50.3 / -44',size=15,color=INK)
 ax.set_aspect('equal');ax.set_xlim(-65,147);ax.set_ylim(-132,55);ax.axis('off');fig.suptitle('Step 07 | Belt and toothed inside idler',size=23,color=INK,weight='bold');fig.text(.06,.075,'360-5M-15 belt. The idler contacts the toothed face; no small smooth back-side idler.',size=16,color=INK);fig.text(.06,.035,'Pitch-line schematic, not a cutting template. Set final tension/clamp hole on the real sample cell.',size=13,color='#536474');fig.savefig(OUT/'Assembly_07_Belt.png',dpi=180);plt.close(fig);VISUAL_LOG.append({'image':'Assembly_07_Belt.png','labels':[],'geometry_source':'pitch-line schematic from current drive dimensions; not a cut pattern'})

def tube_diagram():
 fig,ax=plt.subplots(figsize=(14,6),facecolor='white');ax.set_xlim(-15,315);ax.set_ylim(-48,50);ax.axis('off')
 ax.add_patch(Rectangle((22,-4),249.08,8,fc=LEGS[0],ec=INK,lw=1.3));ax.add_patch(Circle((0,0),8,fc=PAL['P02'],ec=INK));ax.add_patch(Circle((297.08,0),8,fc=PAL['M12'],ec=INK))
 ax.add_patch(Rectangle((16,-7),30,14,fc=PAL['P03'],alpha=.7,ec=INK));ax.add_patch(Rectangle((247.08,-7),32,14,fc=PAL['P05'],alpha=.7,ec=INK))
 for x in(40,253.08):ax.add_patch(Circle((x,0),1.6,fc='white',ec=INK));ax.annotate('M3 retaining pin',(x,0),xytext=(0,-35),textcoords='offset points',ha='center',fontsize=14,arrowprops={'arrowstyle':'-','color':INK})
 for y,x1,x2,label in[(34,0,297.08,'297.080 mm joint centres'),(21,22,271.08,'249.080 mm tube cut length'),(-31,22,40,'18 mm'),(-31,253.08,271.08,'18 mm')]:
  ax.annotate('',(x1,y),(x2,y),arrowprops={'arrowstyle':'<->','color':INK});ax.text((x1+x2)/2,y+3,label,ha='center',fontsize=15,color=INK)
 ax.text(0,12,'LOWER',ha='center',size=13,color=INK);ax.text(297.08,12,'UPPER',ha='center',size=13,color=INK)
 fig.suptitle('Step 11 | Tube, cross holes and assembled link length',size=23,weight='bold',color=INK);fig.text(.06,.045,'Tube end offsets: 22 mm from lower centre; 26 mm from upper centre. Adjust and measure the complete link before loading.',size=14,color='#536474');fig.savefig(OUT/'Assembly_11_Tube.png',dpi=180);plt.close(fig);VISUAL_LOG.append({'image':'Assembly_11_Tube.png','labels':[],'geometry_source':'dimensioned assembly schematic from current verified link lengths'})

def colour_key():
 entries=[('M05 / M17 bearing stands',PAL['M05']),('M06 crank plates',PAL['M06']),('P01 servo cradle',PAL['P01']),('P02 universal cross',PAL['P02']),('P03 lower fork',PAL['P03']),('M13 links L1-L6',LEGS[0]),('P04 split sockets',PAL['P04']),('P05 upper couplers',PAL['P05']),('P09 labelled wedges',PAL['P09']),('M09 carrier',PAL['M09']),('M10 tray sheet',PAL['M10']),('M11 braces / M18 ring',PAL['M18']),('Outer frame / existing parts','#c4ccd4')]
 fig,ax=plt.subplots(figsize=(14,6.5),facecolor='white');ax.axis('off')
 for i,(text,col)in enumerate(entries):
  x=.04+(i//7)*.49;y=.84-(i%7)*.115;ax.add_patch(Rectangle((x,y),.05,.065,transform=ax.transAxes,fc=col,ec=INK,lw=.7));ax.text(x+.07,y+.03,text,transform=ax.transAxes,va='center',fontsize=18,color=INK)
 fig.suptitle('Illustration colour key - match the part IDs',size=24,weight='bold',color=INK);fig.text(.06,.025,'Colours are illustrative. All six links also have numbered IDs; existing/context parts are faded in close-ups.',size=14,color='#536474');fig.savefig(OUT/'Colour_Key.png',dpi=180);plt.close(fig)

if __name__=='__main__':
 render_system();render_system(True);plan();motion_views();orthographic();assembly_images();print('Completed read-only colour and assembly illustrations',flush=True)
