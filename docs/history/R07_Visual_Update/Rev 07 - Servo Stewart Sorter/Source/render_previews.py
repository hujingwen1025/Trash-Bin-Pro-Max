"""Render the actual parametric CAD with Matplotlib; no generated-image geometry."""
from pathlib import Path
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Source'));import build_cad as model
sys.path.insert(0,str(ROOT/'Software'));from geometry import Geometry,tray_polygon
g=Geometry();cache={}
def faces(shape,key=None):
 if key in cache:return cache[key]
 vv,tt=shape.tessellate(.8,.4);v=np.array([p.toTuple()for p in vv]);f=v[np.array(tt)]
 if key:cache[key]=f
 return f
def add(ax,shape,color,alpha=1.,key=None,T=None):
 f=faces(shape,key)
 if T is not None:T=np.array(T);f=f@T[:3,:3].T+T[:3,3]
 ax.add_collection3d(Poly3DCollection(f,facecolor=color,edgecolor='none',linewidths=0,alpha=alpha,zsort='average'))
def setup(ax):
 ax.set_xlim(-430,430);ax.set_ylim(-430,430);ax.set_zlim(-30,1100);ax.set_box_aspect([860,860,1130]);ax.view_init(elev=25,azim=-55);ax.set_axis_off()
def render_system(exploded=False):
 fig=plt.figure(figsize=(14,11),facecolor='#f5f8fa');ax=fig.add_subplot(111,projection='3d');setup(ax)
 members,refs=model.build_assembly(np.eye(3),[0,0,g.c['rest_height_mm']],'render',export=False)
 for name,key,s,T,role in members:
  delta=np.zeros(3)
  if exploded:
   if name.startswith('D'):i=int(name[1])-1;delta=g.B[i]/np.linalg.norm(g.B[i])*90
   elif name.startswith('L'):delta=np.array([0,0,160.])
   elif role=='moving':delta=np.array([0,0,250.])
   elif name.endswith('guide'):delta=np.array(T)[:3,0]*100
  T=np.array(T);T[:3,3]+=delta
  add(ax,model.parts[key]['shape'],'#2493a1'if model.parts[key]['kind']=='print'else'#a7b7c2',key=key,T=T)
 for name,key,s,T,role in refs:
  if 'servo'in name:col='#283b50'
  elif key=='Foam_Pad':col='#495b66'
  else:col='#718492'
  if exploded and name.startswith('D'):i=int(name[1])-1;T=np.array(T);T[:3,3]+=g.B[i]/np.linalg.norm(g.B[i])*90
  add(ax,model.purchase[key],col,key='ref_'+key,T=T)
 base=model.box(700,700,20,(0,0,10));add(ax,base,'#bdab87',key='render_base')
 for bid in g.c['bin_azimuth_deg']:
  shape=cq.importers.importStep(str(ROOT.parent/'Rev 06 - 10mm Basswood Hybrid Bins/STEP'/f'{bid}_Assembly.step')).val().translate((0,0,20))
  add(ax,shape,'#c9b791',alpha=.20 if bid in ('B3','B4')else .75,key='bin_'+bid)
 if exploded:ax.set_zlim(-30,1300);ax.set_box_aspect([860,860,1330])
 title='Exploded CAD reference'if exploded else'Complete system - front bins shown translucent'
 fig.text(.06,.94,title,size=20,weight='bold',color='#153c53');fig.text(.06,.905,'R07 | 2 kg payload target | 55 degree discharge | digital prototype',size=11,color='#476170')
 fig.text(.06,.045,'750 x750 mm external frame. Original700 x700 base and R06 bins retained. Physical qualification not performed.',size=10,color='#9d2828')
 fig.savefig(ROOT/'Preview'/('Exploded_Assembly.png'if exploded else'Complete_System.png'),dpi=170,bbox_inches='tight');plt.close(fig)
def plan():
 fig,ax=plt.subplots(figsize=(10,10),facecolor='white');ax.set_aspect('equal');ax.set_xlim(-440,440);ax.set_ylim(-440,440)
 for x,y,b in [(1,1,'B1'),(-1,1,'B2'),(1,-1,'B3'),(-1,-1,'B4')]:
  from matplotlib.patches import Rectangle,Circle
  ax.add_patch(Rectangle((2.5 if x>0 else -350,2.5 if y>0 else -350),347.5,347.5,facecolor='#eee7d9',edgecolor='#897d67'))
  ax.text(x*275,y*275,b,ha='center',color='#776b55',size=15)
 ax.add_patch(Rectangle((-375,-375),750,750,fill=False,edgecolor='#153c53',linewidth=2));ax.add_patch(Circle((0,0),73.75,color='#8fa4b1'))
 p=tray_polygon();ax.fill(p[:,0],p[:,1],color='#167d8d',alpha=.55);ax.plot(*np.r_[p,p[:1]].T,color='#153c53')
 for k,b in enumerate(g.c['bin_azimuth_deg']):
  R,t=list(g.path(b,2))[-1];q=np.c_[p,np.full(len(p),g.c['tray_surface_above_anchor_mm'])]@R.T+t;ax.plot(*np.r_[q[:,:2],q[:1,:2]].T,'--',linewidth=1,label=b+' dump')
 ax.annotate('',(-375,-410),(375,-410),arrowprops={'arrowstyle':'<->','color':'#153c53'});ax.text(0,-425,'750 overall frame /700 original base',ha='center',size=11)
 ax.set_title('Top view and four tray envelopes (mm)',loc='left',size=17,color='#153c53');ax.legend(loc='upper left',fontsize=8);ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');ax.grid(alpha=.12)
 fig.savefig(ROOT/'Preview/Top_View.png',dpi=180,bbox_inches='tight');plt.close(fig)
def motion_views():
 fig=plt.figure(figsize=(14,11),facecolor='white')
 for k,b in enumerate(g.c['bin_azimuth_deg']):
  ax=fig.add_subplot(2,2,k+1,projection='3d');setup(ax);R,t=list(g.path(b,2))[-1];a,H,P=g.points(R,t);z=np.array([0,0,g.c['crank_axis_global_z_mm']])
  for i in range(6):
   q=np.array([g.B[i],H[i],P[i]])+z;ax.plot(*q.T,color='#167d8d',linewidth=2);ax.scatter(*q.T,color='#153c53',s=8)
  q=np.c_[tray_polygon(),np.full(8,g.c['tray_surface_above_anchor_mm'])]@R.T+t+z;ax.add_collection3d(Poly3DCollection([q],facecolor='#779da9',alpha=.7,edgecolor='#153c53'))
  ax.set_title(b+' |55 deg |85 mm translation',loc='left',size=12,color='#153c53')
 fig.suptitle('Calculated discharge poses - no trash-contact physics implied',color='#153c53',size=17);fig.savefig(ROOT/'Preview/Four_Dump_Poses.png',dpi=180,bbox_inches='tight');plt.close(fig)

def orthographic():
 members,refs=model.build_assembly(np.eye(3),[0,0,g.c['rest_height_mm']],'render',export=False)
 for title,elev,azim in [('Front',0,-90),('Right',0,0),('Rear',0,90),('Left',0,180),('Top',90,-90),('Mechanism',18,-55)]:
  fig=plt.figure(figsize=(12,10),facecolor='white');ax=fig.add_subplot(111,projection='3d');setup(ax);ax.set_proj_type('ortho');ax.view_init(elev=elev,azim=azim)
  if title=='Mechanism':ax.set_xlim(-310,310);ax.set_ylim(-310,310);ax.set_zlim(500,920);ax.set_box_aspect([620,620,420])
  for name,key,shape,T,role in members+refs:
   if title=='Mechanism'and(key=='P06_Discharge_Guide'or key.startswith(('M23','M24','M25','M26','M01','M02','M03','M04'))or key.startswith(('Outer_','Backstop_','Foam','Rubber'))):continue
   if key in model.parts:original=model.parts[key]['shape'];col='#1c8a98'if model.parts[key]['kind']=='print'else'#a4b3be'
   else:original=model.purchase[key];col='#526575'
   add(ax,original,col,key=('ref_'if key not in model.parts else'')+key,T=T)
  fig.text(.05,.95,title+' CAD view',size=19,color='#153c53',weight='bold');fig.text(.05,.04,'Frame750 x750 | Crank axesZ640 | Level trayZ858.6 | Active trayZ898.6 mm | Prototype',size=10,color='#9d2828')
  fig.savefig(ROOT/'Preview'/f'{title}_View.png',dpi=150,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':render_system();render_system(True);plan();motion_views();orthographic();print('Rendered four CAD previews')
