"""Guarded R07 motion controller. Simulation is the default entry point."""
import time,json
from pathlib import Path
import numpy as np
from geometry import Geometry

class Fault(RuntimeError):pass

class Controller:
    def __init__(self,bus,config,clock=time.monotonic,sleep=time.sleep,log=None,empty_check=None):
        self.bus=bus;self.c=config;self.g=Geometry(config);self.clock=clock;self.sleep=sleep
        self.fault=None;self.pose=None;self.last_cycle=-float('inf');self.log=log;self.empty_check=empty_check

    def record(self,event,**data):
        if self.log:
            with Path(self.log).open('a')as f:f.write(json.dumps({'time_monotonic':self.clock(),'event':event,**data})+'\n')

    def latch(self,message):
        self.fault=message;self.record('FAULT',message=message)
        # Keep last commanded holding positions. Never cut torque automatically
        # or attempt a blind home motion. Physical E-stop is independent.
        raise Fault(message)

    def health(self,expected=None,tick=None):
        statuses=[]
        try:
            selected=range(6)if tick is None else[tick%6]
            for i in selected:
                sid=self.c['servo_ids'][i]
                fields=('angle_deg','temperature_C','voltage_V')if tick is None else('angle_deg','temperature_C'if(tick//6)%2==0 else'voltage_V')
                s=self.bus.status(sid,fields=fields);statuses.append(s)
                if not all(np.isfinite(s[k])for k in fields):raise ValueError('Non-finite servo status')
                if 'temperature_C'in s and s['temperature_C']>=self.c['temperature_limit_C']:raise ValueError(f'Servo {sid}: temperature limit')
                if 'voltage_V'in s and not self.c['voltage_min_V']<=s['voltage_V']<=self.c['voltage_max_V']:raise ValueError(f'Servo {sid}: voltage limit')
                if expected is not None and abs(s['angle_deg']-expected[i])>self.c['tracking_error_deg']:raise ValueError(f'Servo {sid}: tracking error')
        except Exception as e:self.latch(str(e))
        return statuses

    def identify_pose(self):
        s=self.health();actual=np.array([v['angle_deg']for v in s])
        known=[('REST',np.eye(3),np.array([0,0,self.c['rest_height_mm']])),('ACTIVE',np.eye(3),np.array([0,0,self.c['active_height_mm']]))]
        for b in self.c['bin_azimuth_deg']:
            R,t=list(self.g.path(b,2))[-1];known.append((b,R,t))
        for name,R,t in known:
            q=self.g.servo_angles(self.g.ik(R,t))
            if np.max(abs(q-actual))<=2:
                self.pose=(R,t);self.record('STARTUP',pose=name);return name
        self.latch('Unknown startup pose. Support tray and recover manually with links disconnected; no blind homing.')

    def execute(self,poses,seconds,arm=False,clear=False,commissioning=False):
        if self.fault:raise Fault('Latched fault: '+self.fault)
        if not arm or not clear:raise Fault('Explicit arm and clear-area confirmation required')
        if not self.c['calibrated']:raise Fault('Calibration not recorded')
        if not commissioning and not self.c['physical_qualification_passed']:raise Fault('Physical qualification incomplete; use attended commissioning only')
        poses=list(poses)
        # Validate entire path before staging a single motor command.
        angles=[self.g.servo_angles(self.g.ik(R,t))for R,t in poses]
        if self.pose is None:self.identify_pose()
        current=self.g.servo_angles(self.g.ik(*self.pose))
        if np.max(abs(current-angles[0]))>2:raise Fault('Path does not begin at the current known pose')
        dt=seconds/(len(poses)-1)
        if dt<.04:raise ValueError('Insufficient segment time')
        if max(np.max(abs(q2-q1))/dt for q1,q2 in zip(angles,angles[1:]))>90:raise ValueError('Servo speed limit exceeded')
        # Full readback is outside the timed loop. During motion, two read
        # transactions per frame rotate through all six IDs. This fits a50 ms
        # frame even with a16 ms USB reply latency in the tested timing model.
        self.health(current)
        previous=angles[0];start=self.clock()
        for i,((R,t),q)in enumerate(zip(poses,angles)):
            deadline=start+i*dt
            wait=deadline-self.clock()
            if wait>0:self.sleep(wait)
            elif -wait>.10:self.latch('Motion loop missed its deadline')
            self.health(previous,tick=i)
            try:self.bus.synchronized_move(self.c['servo_ids'],q,max(20,round(dt*1000)))
            except Exception as e:self.latch('Staging/write failure: '+str(e))
            previous=q;self.pose=(R,t);self.record('MOVE',angles_deg=q.tolist())
        self.sleep(dt);self.health(previous)

    def dump(self,bin_id,**options):
        if bin_id not in self.c['bin_azimuth_deg']:raise ValueError('Unknown bin')
        if self.clock()-self.last_cycle<self.c['minimum_cycle_seconds']:raise Fault('Cooling interval not complete')
        if self.pose is None:self.identify_pose()
        rest=(np.eye(3),np.array([0,0,self.c['rest_height_mm']]))
        if np.linalg.norm(self.pose[1]-rest[1])>1 or np.max(abs(self.pose[0]-rest[0]))>.01:raise Fault('Dump must start from resting supports')
        c=self.c;n=round(c['lift_seconds']*c['update_hz'])+1;m=round(c['tilt_seconds']*c['update_hz'])+1
        def smooth(s):return s*s*s*(10+s*(-15+6*s))
        lift=[(np.eye(3),np.array([0,0,c['rest_height_mm']+(c['active_height_mm']-c['rest_height_mm'])*smooth(s)]))for s in np.linspace(0,1,n)]
        from geometry import rotation
        az=np.deg2rad(c['bin_azimuth_deg'][bin_id]);u=np.array([np.cos(az),np.sin(az),0])
        tilt=[]
        for ss in np.linspace(0,1,m):
            s=smooth(ss);tilt.append((rotation([-np.sin(az),np.cos(az),0],np.deg2rad(c['tilt_deg'])*s),u*c['travel_mm']*s+[0,0,c['active_height_mm']+c['dump_height_delta_mm']*s]))
        self.last_cycle=self.clock();self.execute(lift,c['lift_seconds'],**options);self.execute(tilt,c['tilt_seconds'],**options)
        end=self.clock()+c['dwell_seconds']
        while self.clock()<end:self.health(self.g.servo_angles(self.g.ik(*self.pose)));self.sleep(.10)
        if self.empty_check is None or not self.empty_check():self.latch('Discharge not confirmed empty/free of bridging. Support tray and recover manually; no automatic return.')
        self.execute(reversed(tilt),c['tilt_seconds'],**options);self.execute(reversed(lift),c['lift_seconds'],**options)
        self.record('DUMP_COMPLETE',bin=bin_id)

    def home(self,**options):
        if self.pose is None:self.identify_pose()
        c=self.c;R,t=self.pose
        # Only reverse a certified trajectory from its exact dump endpoint.
        for bid in c['bin_azimuth_deg']:
            route=list(self.g.path(bid,61));rr,tt=route[-1]
            if np.max(abs(R-rr))<1e-6 and np.max(abs(t-tt))<1e-4:
                if self.empty_check is None or not self.empty_check():self.latch('Discharge not confirmed empty/free of bridging. No home return.')
                self.execute(reversed(route[60:]),c['tilt_seconds'],**options)
                self.execute(reversed(route[:61]),c['lift_seconds'],**options);return
        if np.max(abs(R-np.eye(3)))<1e-6 and abs(t[2]-c['rest_height_mm'])<1:return
        if np.max(abs(R-np.eye(3)))<1e-6 and abs(t[2]-c['active_height_mm'])<1:
            path=[(np.eye(3),[0,0,z])for z in np.linspace(c['active_height_mm'],c['rest_height_mm'],61)]
            self.execute(path,c['lift_seconds'],**options);return
        raise Fault('Home recovery requires a known endpoint; manual recovery otherwise')
