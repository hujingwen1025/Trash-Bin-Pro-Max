"""Prepare a calibration copy; never authorizes hardware or marks tests passed."""
import argparse,json
from pathlib import Path
import numpy as np
from geometry import Geometry,load_config

def main():
 p=argparse.ArgumentParser();p.add_argument('--config');p.add_argument('--directions',nargs=6,type=int,choices=[-1,1]);p.add_argument('--measured-active-deg',nargs=6,type=float);p.add_argument('--out',required=True);a=p.parse_args()
 c=load_config(a.config)if a.config else load_config()
 if a.directions:c['servo_direction']=a.directions
 g=Geometry(c);q=np.array([np.rad2deg(g.ik(R,t,False)-g.reference_alpha)for b in c['bin_azimuth_deg']for R,t in g.path(b,241)])
 suggested=120-np.array(c['servo_direction'])*c['reduction']*(q.min(0)+q.max(0))/2
 c['servo_zero_deg']=a.measured_active_deg if a.measured_active_deg else suggested.round(5).tolist()
 c['calibrated']=False;c['physical_qualification_passed']=False;c['hardware_armed']=False
 g=Geometry(c);values=np.array([g.servo_angles(g.ik(R,t))for b in c['bin_azimuth_deg']for R,t in g.path(b,241)])
 out=Path(a.out)
 if out.exists():raise FileExistsError('Choose a new calibration filename; do not overwrite evidence')
 out.write_text(json.dumps(c,indent=2)+'\n')
 print('Active-reference crank angles deg:',np.rad2deg(g.reference_alpha).round(4).tolist())
 print('Servo reference positions:',c['servo_zero_deg'])
 print('Path ranges:',values.min(0).round(3).tolist(),values.max(0).round(3).tolist())
 print('Saved uncoupled setup copy. Verify physical direction, offsets, joints and fixtures before marking calibrated.')

if __name__=='__main__':main()
