from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(13,8));ax.set_xlim(0,13);ax.set_ylim(0,8);ax.axis('off')
def block(x,y,w,h,text,color='#e8f2f4'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor=color,edgecolor='#153c53',linewidth=1.2));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10,color='#153c53')
def arrow(a,b,color='#b54135',style='-'):
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':color,'lw':1.6,'linestyle':style})
block(.3,6.4,2.5,1,'Vendor-assembled\nfused/earthed AC enclosure')
block(3.5,6.4,2.2,1,'12 V / >=29 A\nDC supply')
block(6.4,6.4,2.5,1,'30 A main fuse\nDC-rated disconnect')
block(9.6,6.4,2.7,1,'Fused star distribution\n6 x 5 A branches')
for a,b in [((2.8,6.9),(3.5,6.9)),((5.7,6.9),(6.4,6.9)),((8.9,6.9),(9.6,6.9))]:arrow(a,b)
block(6.3,4.6,2.7,1,'NC emergency stop\nmanual restart circuit','#f9e6e3');arrow((7.65,5.6),(7.65,6.4),style='--')
block(.3,3.1,2.5,1.2,'Raspberry Pi\nseparate regulated supply')
block(3.5,3.1,2.2,1.2,'USB / TTL\nhalf-duplex adapter')
arrow((2.8,3.7),(3.5,3.7),'#167d8d');ax.text(3.1,3.95,'USB',ha='center',fontsize=8)
for i in range(6):
 x=.3+i*2.1;block(x,.8,1.8,1.1,f'HTD-85H\nID {i+1}')
 arrow((x+.65,2.18),(x+.65,1.9),'#c34d3a')
ax.plot([10.95,12.7,12.7,.95],[6.4,5.95,2.18,2.18],color='#c34d3a',lw=1.5)
arrow((4.6,3.1),(6.45,2.35),'#167d8d');ax.plot([1.2,11.7],[2.35,2.35],color='#167d8d',lw=1.7)
for i in range(6):arrow((1.2+i*2.1,2.35),(1.2+i*2.1,1.9),'#167d8d')
ax.text(.3,2.6,'DATA + common GND bus (confirm actual connector pins)',fontsize=9,color='#167d8d')
ax.text(.3,.3,'Red: individually fused motor power. Teal: signal/common ground. No motor power through USB adapter. Connector pinouts are supplier-specific.',fontsize=9,color='#9d2828')
fig.suptitle('R07 power and control connections - functional diagram',x=.12,ha='left',fontsize=17,color='#153c53');fig.savefig(ROOT/'Preview/Wiring_Diagram.png',dpi=160,bbox_inches='tight');plt.close(fig)
