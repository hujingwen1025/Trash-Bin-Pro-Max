"""R07 shared geometry. Millimetres, radians, right-handed base coordinates."""
from pathlib import Path
import json
import numpy as np

DEFAULT_CONFIG = Path(__file__).with_name('configuration.json')

def load_config(path=DEFAULT_CONFIG):
    c = json.loads(Path(path).read_text())
    if len(c['servo_ids']) != 6 or len(set(c['servo_ids'])) != 6:
        raise ValueError('Exactly six unique servo IDs are required')
    for key in ('servo_zero_deg', 'servo_direction'):
        if len(c[key]) != 6:
            raise ValueError(key + ' must have six entries')
    if any(x not in (-1, 1) for x in c['servo_direction']):
        raise ValueError('Servo directions must be -1 or +1')
    return c

def rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    k = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3) + np.sin(angle)*k + (1-np.cos(angle))*(k@k)

class Geometry:
    def __init__(self, config=None):
        self.c = config or load_config()
        c = self.c
        ba, pa, ph = (c[k] for k in ('base_pair_half_deg','top_pair_half_deg','phase_deg'))
        self.bt = np.deg2rad(np.array([-ba,ba,120-ba,120+ba,240-ba,240+ba])+ph)
        self.pt = np.deg2rad(np.array([-60+pa,60-pa,60+pa,180-pa,180+pa,300-pa])+ph)
        self.B = np.c_[c['base_radius_mm']*np.cos(self.bt),c['base_radius_mm']*np.sin(self.bt),np.zeros(6)]
        self.p = np.c_[c['top_radius_mm']*np.cos(self.pt),c['top_radius_mm']*np.sin(self.pt),np.zeros(6)]
        self.beta = self.bt + np.tile([1,-1],3)*np.deg2rad(c['horn_plane_offset_deg'])
        self.u = np.c_[np.cos(self.beta),np.sin(self.beta),np.zeros(6)]
        self.v = np.c_[-np.sin(self.beta),np.cos(self.beta),np.zeros(6)]
        self.h = c['crank_mm']
        self.d = np.full(6,c['rod_center_mm'])
        self.reference_alpha = self.ik(np.eye(3),[0,0,c['active_height_mm']],check_servo=False)

    def ik(self, R, t, check_servo=True):
        R, t = np.asarray(R,float), np.asarray(t,float)
        if R.shape != (3,3) or t.shape != (3,) or not np.all(np.isfinite(R)) or not np.all(np.isfinite(t)):
            raise ValueError('Invalid pose')
        if not np.allclose(R.T@R,np.eye(3),atol=1e-7) or np.linalg.det(R)<.999999:
            raise ValueError('Rotation must be orthonormal and right-handed')
        P = self.p@R.T+t
        L = P-self.B
        e = 2*self.h*L[:,2]
        f = 2*self.h*np.sum(L*self.u,axis=1)
        g = np.sum(L*L,axis=1)+self.h**2-self.d**2
        den = np.hypot(e,f)
        if np.any(den<1e-9) or np.any(np.abs(g)>den):
            raise ValueError('Unreachable pose: crank/rod closure')
        a = np.arcsin(g/den)-np.arctan2(f,e)
        if check_servo:
            self.servo_angles(a)
        return a

    def servo_angles(self, a):
        c=self.c
        values=np.asarray(c['servo_zero_deg'])+np.asarray(c['servo_direction'])*c['reduction']*np.rad2deg(np.asarray(a)-self.reference_alpha)
        if np.any(values<c['servo_min_deg']) or np.any(values>c['servo_max_deg']):
            raise ValueError('Servo travel limit exceeded')
        return values

    def points(self,R,t):
        a=self.ik(R,t)
        H=self.B+self.h*(np.cos(a)[:,None]*self.u+np.sin(a)[:,None]*np.array([0,0,1]))
        P=self.p@np.asarray(R).T+np.asarray(t)
        return a,H,P

    def path(self,bin_id,samples=121):
        """Geometric path; controller adds timing. No arbitrary external poses."""
        c=self.c
        if bin_id not in c['bin_azimuth_deg']:
            raise ValueError('Unknown bin')
        az=np.deg2rad(c['bin_azimuth_deg'][bin_id]); direction=np.array([np.cos(az),np.sin(az),0])
        for s in np.linspace(0,1,samples):
            yield np.eye(3),np.array([0,0,c['rest_height_mm']+(c['active_height_mm']-c['rest_height_mm'])*s])
        for s in np.linspace(0,1,samples)[1:]:
            yield rotation([-np.sin(az),np.cos(az),0],np.deg2rad(c['tilt_deg'])*s),direction*c['travel_mm']*s+np.array([0,0,c['active_height_mm']+c['dump_height_delta_mm']*s])

    def statics(self,R,t,payload_cg_mm,moving_mass_kg=None,factor=1.):
        """Six-force equilibrium and motor torque, including reduction efficiency.

        Equal/opposite gravity support wrench. CG specified in tray coordinates.
        Payload CG is relative to the upper joint plane. Moving hardware is
        conservatively placed23 mm above that plane; full rod weight is included
        in its mass allowance although the fixed cranks carry part of that weight.
        """
        a,H,P=self.points(R,t)
        r=self.p@np.asarray(R).T
        u=(P-H)/self.d[:,None]
        # Angular columns use 100 mm normalization for meaningful conditioning.
        J=np.c_[u,np.cross(r,u)/100.]
        cg=np.asarray(R)@np.asarray(payload_cg_mm,float)
        moving_mass_kg=self.c['moving_mass_limit_kg'] if moving_mass_kg is None else moving_mass_kg
        load=self.c['payload_kg']*9.81*factor
        hardware_cg=np.asarray(R)@np.array([0.,0.,self.c.get('moving_cg_above_anchor_mm',23.)])
        moment=np.cross(cg,[0,0,load])+np.cross(hardware_cg,[0,0,moving_mass_kg*9.81*factor])
        wrench=np.r_[0,0,(moving_mass_kg+self.c['payload_kg'])*9.81*factor,moment/100.]
        f=np.linalg.solve(J.T,wrench)
        deriv=self.h*(-np.sin(a)[:,None]*self.u+np.cos(a)[:,None]*[0,0,1])
        leverage=np.sum(u*deriv,axis=1)/1000.
        motor=f*leverage/self.c['reduction']/self.c['belt_efficiency']
        return {'rod_force_N':f,'motor_torque_Nm':motor,'singular_values':np.linalg.svd(J,compute_uv=False),'transmission':np.abs(leverage*1000/self.h)}

def tray_polygon():
    # Local X/Y axes are at 45 degrees to the base; four 330 mm dump edges.
    return np.array([[-165,-180],[165,-180],[180,-165],[180,165],[165,180],[-165,180],[-180,165],[-180,-165]],float)@np.array([[2**-.5,2**-.5],[-2**-.5,2**-.5]])
