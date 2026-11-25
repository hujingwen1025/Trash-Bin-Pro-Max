#!/usr/bin/env python3
"""CLI: dry-run, probe, home, dump, uncoupled calibration and servo ID assignment."""
import argparse,json,struct
import numpy as np
from geometry import load_config,Geometry
from bus import Bus,ID_WRITE
from controller import Controller

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['simulate','probe','home','dump','set-id','calibrate-angle']);p.add_argument('--bin',default='B1',choices=['B1','B2','B3','B4']);p.add_argument('--config');p.add_argument('--port');p.add_argument('--arm',action='store_true');p.add_argument('--confirm-clear',action='store_true');p.add_argument('--commissioning',action='store_true');p.add_argument('--links-disconnected',action='store_true');p.add_argument('--only-one-servo',action='store_true');p.add_argument('--id',type=int,default=1);p.add_argument('--new-id',type=int);p.add_argument('--angle',type=float,default=120);p.add_argument('--log',default='motion.jsonl');a=p.parse_args()
 c=load_config(a.config)if a.config else load_config();g=Geometry(c)
 if a.command=='simulate':
  for b in c['bin_azimuth_deg']:
   vals=[g.servo_angles(g.ik(R,t))for R,t in g.path(b)]
   print(json.dumps({'bin':b,'samples':len(vals),'min_servo_deg':np.min(vals,axis=0).tolist(),'max_servo_deg':np.max(vals,axis=0).tolist(),'hardware_commands':0}))
  return
 if not a.port:p.error('--port is required for hardware commands')
 bus=Bus(a.port,c['command_timeout_s'])
 try:
  if a.command=='probe':
   for sid in c['servo_ids']:print(sid,bus.status(sid))
  elif a.command in ('set-id','calibrate-angle'):
   if not(a.links_disconnected and a.confirm_clear and a.arm):p.error('Uncoupled calibration requires --links-disconnected --confirm-clear --arm')
   if a.command=='set-id':
    if not a.only_one_servo or a.new_id is None or not 0<=a.new_id<=253:p.error('Connect only one servo and supply --only-one-servo --new-id 0..253')
    bus.write(a.id,ID_WRITE,bytes([a.new_id]));print('ID written; power cycle then probe before adding another servo.')
   else:
    bus.synchronized_move([a.id],[a.angle],3000);print('Uncoupled calibration move sent. Record actual crank alignment before setting calibrated=true.')
  else:
   ctl=Controller(bus,c,log=a.log,empty_check=lambda:input('Visually verify tray EMPTY and no item bridging to a guide/backstop. Type EMPTY to return: ').strip()=='EMPTY');options=dict(arm=a.arm,clear=a.confirm_clear,commissioning=a.commissioning)
   if a.command=='home':ctl.home(**options)
   else:ctl.dump(a.bin,**options)
 finally:bus.close()

if __name__=='__main__':main()
