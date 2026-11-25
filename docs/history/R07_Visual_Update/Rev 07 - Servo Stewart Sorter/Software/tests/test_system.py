import sys,unittest,struct
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from geometry import Geometry,load_config,rotation
from bus import packet,Bus,MOVE_WAIT,MOVE_START
from controller import Controller,Fault

class Clock:
 def __init__(self):self.t=0.
 def now(self):return self.t
 def sleep(self,x):self.t+=x

class FakeBus:
 def __init__(self,angles):self.q=list(angles);self.moves=[];self.bad=None;self.staged_failure=False
 def status(self,sid,fields=None):
  if self.bad=='timeout':raise TimeoutError('missing servo')
  result={'angle_deg':self.q[sid-1]+(20 if self.bad=='tracking' else 0),'temperature_C':60 if self.bad=='hot' else 25,'voltage_V':8 if self.bad=='voltage' else 12}
  return result if fields is None else{k:result[k]for k in fields}
 def synchronized_move(self,ids,q,duration_ms):
  if self.staged_failure:raise IOError('staging failure')
  self.q=list(q);self.moves.append((ids,list(q),duration_ms))

class ProtocolTests(unittest.TestCase):
 def test_known_frame(self):self.assertEqual(packet(1,28),bytes.fromhex('555501031cdf'))
 def test_checksum(self):
  p=packet(6,MOVE_WAIT,struct.pack('<HH',500,50));self.assertEqual(sum(p[2:])&255,255)
 def test_no_partial_invalid_move(self):
  class Port:
   def __init__(self,*a,**k):self.writes=[]
   def write(self,p):self.writes.append(p);return len(p)
   def flush(self):pass
  b=Bus('fake',serial_factory=Port)
  with self.assertRaises(ValueError):b.synchronized_move([1,2],[120,300])
  self.assertEqual(b.serial.writes,[])
 def test_no_start_after_staging_failure(self):
  class Port:
   def __init__(self,*a,**k):self.writes=[]
   def write(self,p):
    self.writes.append(p)
    if len(self.writes)==2:raise IOError('disconnect')
    return len(p)
   def flush(self):pass
  b=Bus('fake',serial_factory=Port)
  with self.assertRaises(IOError):b.synchronized_move([1,2],[120,120])
  self.assertFalse(any(p[4]==MOVE_START for p in b.serial.writes))

 def test_selected_status_fields_only(self):
  b=Bus.__new__(Bus);calls=[]
  def read(sid,cmd):
   calls.append(cmd);return bytes([25])if cmd==26 else struct.pack('<h',500)
  b.read=read
  self.assertEqual(b.status(1,fields=('angle_deg','temperature_C')),{'angle_deg':120,'temperature_C':25})
  self.assertEqual(calls,[28,26])

class KinematicsTests(unittest.TestCase):
 def setUp(self):self.g=Geometry()
 def test_all_paths_close(self):
  for b in self.g.c['bin_azimuth_deg']:
   for R,t in self.g.path(b,101):
    a,H,P=self.g.points(R,t);self.assertLess(np.max(abs(np.linalg.norm(P-H,axis=1)-self.g.d)),1e-7)
 def test_four_bin_mapping(self):
  for b,(sx,sy)in {'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}.items():
   R,t=list(self.g.path(b,2))[-1];self.assertEqual(np.sign(t[0]),sx);self.assertEqual(np.sign(t[1]),sy)
   downhill=R@[sx,sy,0];self.assertLess(downhill[2],0)
 def test_unreachable_and_invalid(self):
  for R,t in [(np.eye(3),[0,0,10000]),(np.eye(3)*2,[0,0,200]),(np.eye(3),[float('nan'),0,200])]:
   with self.assertRaises(ValueError):self.g.ik(R,t)
 def test_statics_balance(self):
  R,t=list(self.g.path('B2',2))[-1];result=self.g.statics(R,t,[150,0,50]);_,H,P=self.g.points(R,t);u=(P-H)/self.g.d[:,None]
  net=(u*result['rod_force_N'][:,None]).sum(0);np.testing.assert_allclose(net,[0,0,3.3*9.81],atol=1e-8)

class ControlTests(unittest.TestCase):
 def setUp(self):
  self.c=load_config();self.c['calibrated']=True;self.c['physical_qualification_passed']=True;self.clock=Clock();g=Geometry(self.c);q=g.servo_angles(g.ik(np.eye(3),[0,0,self.c['rest_height_mm']]));self.bus=FakeBus(q);self.ctl=Controller(self.bus,self.c,self.clock.now,self.clock.sleep,empty_check=lambda:True)
 def test_full_cycle(self):
  self.ctl.dump('B1',arm=True,clear=True);self.assertGreater(len(self.bus.moves),300);self.assertAlmostEqual(self.ctl.pose[1][2],self.c['rest_height_mm'])
 def test_qualification_gate(self):
  self.c['physical_qualification_passed']=False
  with self.assertRaises(Fault):self.ctl.dump('B1',arm=True,clear=True)
  self.assertEqual(self.bus.moves,[])
 def test_commissioning_bypass_only_qualification(self):
  self.c['physical_qualification_passed']=False;self.ctl.dump('B3',arm=True,clear=True,commissioning=True);self.assertTrue(self.bus.moves)
 def test_missing_arm_and_calibration(self):
  with self.assertRaises(Fault):self.ctl.dump('B1',arm=False,clear=True)
  self.assertEqual(self.bus.moves,[])
 def test_unknown_startup_blocks_motion(self):
  self.bus.q=[50]*6
  with self.assertRaises(Fault):self.ctl.identify_pose()
  self.assertEqual(self.bus.moves,[])
 def test_health_faults_latch(self):
  for bad in ('timeout','hot','voltage'):
   self.bus.bad=bad
   with self.assertRaises(Fault):self.ctl.health()
   self.assertIsNotNone(self.ctl.fault)
   self.bus.bad=None
   with self.assertRaises(Fault):self.ctl.dump('B1',arm=True,clear=True)
 def test_tracking_latches(self):
  self.bus.bad='tracking'
  with self.assertRaises(Fault):self.ctl.health(self.bus.q)
 def test_cooling_interval(self):
  self.ctl.dump('B4',arm=True,clear=True)
  with self.assertRaises(Fault):self.ctl.dump('B4',arm=True,clear=True)
 def test_staging_failure_latches(self):
  self.bus.staged_failure=True
  with self.assertRaises(Fault):self.ctl.dump('B2',arm=True,clear=True)
  self.assertIsNotNone(self.ctl.fault)
 def test_usb_feedback_latency_budget(self):
  clock=self.clock
  class DelayedBus(FakeBus):
   def status(self,sid,fields=None):
    clock.sleep(.016*len(fields or('angle_deg','temperature_C','voltage_V')));return super().status(sid,fields)
   def synchronized_move(self,*args):
    clock.sleep(.007);return super().synchronized_move(*args)
  self.bus=DelayedBus(self.bus.q);self.ctl=Controller(self.bus,self.c,clock.now,clock.sleep,empty_check=lambda:True)
  self.ctl.dump('B1',arm=True,clear=True)
  self.assertIsNone(self.ctl.fault);self.assertLess(clock.t,25)
 def test_excess_usb_latency_latches(self):
  clock=self.clock
  class SlowBus(FakeBus):
   def status(self,sid,fields=None):
    clock.sleep(.04*len(fields or('angle_deg','temperature_C','voltage_V')));return super().status(sid,fields)
   def synchronized_move(self,*args):clock.sleep(.007);return super().synchronized_move(*args)
  bus=SlowBus(self.bus.q);ctl=Controller(bus,self.c,clock.now,clock.sleep,empty_check=lambda:True)
  with self.assertRaises(Fault):ctl.dump('B1',arm=True,clear=True)
  self.assertIn('deadline',ctl.fault);self.assertLess(len(bus.moves),10)
 def test_known_dump_can_home(self):
  g=Geometry(self.c);R,t=list(g.path('B2',2))[-1];self.bus.q=g.servo_angles(g.ik(R,t));self.ctl.home(arm=True,clear=True);self.assertAlmostEqual(self.ctl.pose[1][2],self.c['rest_height_mm'])
 def test_home_blocks_bridged_item(self):
  g=Geometry(self.c);R,t=list(g.path('B2',2))[-1];self.bus.q=g.servo_angles(g.ik(R,t));self.ctl.empty_check=lambda:False
  with self.assertRaises(Fault):self.ctl.home(arm=True,clear=True)
  self.assertEqual(self.bus.moves,[])
 def test_bridged_item_blocks_return(self):
  self.ctl.empty_check=lambda:False
  with self.assertRaises(Fault):self.ctl.dump('B1',arm=True,clear=True)
  self.assertNotAlmostEqual(self.ctl.pose[1][2],self.c['rest_height_mm']);self.assertIn('bridging',self.ctl.fault)

if __name__=='__main__':unittest.main()
