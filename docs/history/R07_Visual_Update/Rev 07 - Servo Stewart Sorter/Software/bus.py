"""Legacy Hiwonder/LewanSoul 0x55 bus protocol, 115200 baud.

Use a half-duplex USB adapter, NOT a bare USB-UART cable. This is not the
different magnetic-encoder HX protocol. Servo power must be wired separately.
"""
import struct,time

MOVE_WAIT=7; MOVE_START=11; ID_WRITE=13
TEMP_READ=26; VOLT_READ=27; POS_READ=28

def packet(servo_id,command,data=b''):
    if not 0<=servo_id<=254 or len(data)>28:
        raise ValueError('Invalid ID or packet length')
    body=bytes([servo_id,len(data)+3,command])+data
    return b'\x55\x55'+body+bytes([(~sum(body))&255])

class Bus:
    def __init__(self,port,timeout=.15,serial_factory=None):
        if serial_factory is None:
            import serial
            serial_factory=serial.Serial
        self.serial=serial_factory(port,115200,timeout=timeout,write_timeout=timeout)
        self.timeout=timeout

    def close(self):self.serial.close()

    def write(self,sid,cmd,data=b''):
        p=packet(sid,cmd,data)
        if self.serial.write(p)!=len(p):raise IOError('Incomplete serial write')
        self.serial.flush()

    def read(self,sid,cmd):
        self.serial.reset_input_buffer();self.write(sid,cmd)
        deadline=time.monotonic()+self.timeout;buf=bytearray()
        while time.monotonic()<deadline:
            b=self.serial.read(1)
            if not b:continue
            buf.extend(b)
            while len(buf)>=2 and buf[:2]!=b'\x55\x55':del buf[0]
            if len(buf)<4:continue
            n=buf[3]
            if n<3 or n>32:del buf[0];continue
            if len(buf)<n+3:continue
            frame=bytes(buf[:n+3]);del buf[:n+3]
            if ((~sum(frame[2:-1]))&255)!=frame[-1]:raise IOError('Servo checksum failure')
            if frame[2]==sid and frame[4]==cmd:return frame[5:-1]
        raise TimeoutError(f'Servo {sid}: no valid reply for command {cmd}')

    def status(self,sid,fields=None):
        def sized(cmd,n):
            value=self.read(sid,cmd)
            if len(value)!=n:raise IOError(f'Servo {sid}: wrong reply size')
            return value
        fields=tuple(fields)if fields is not None else('angle_deg','temperature_C','voltage_V')
        if not fields or any(k not in('angle_deg','temperature_C','voltage_V')for k in fields):raise ValueError('Unknown status field')
        result={}
        for field in fields:
            if field=='angle_deg':
                position=struct.unpack('<h',sized(POS_READ,2))[0]
                if not 0<=position<=1000:raise IOError('Position outside HTD0..1000 range')
                result[field]=position*240/1000
            elif field=='temperature_C':result[field]=sized(TEMP_READ,1)[0]
            else:result[field]=struct.unpack('<H',sized(VOLT_READ,2))[0]/1000
        return result

    def synchronized_move(self,ids,angles_deg,duration_ms=50):
        if len(ids)!=len(angles_deg) or len(set(ids))!=len(ids):raise ValueError('ID/angle mismatch')
        if not 20<=duration_ms<=30000:raise ValueError('Invalid duration')
        if any(not 10<=float(x)<=230 for x in angles_deg):raise ValueError('Servo angle outside guarded range')
        # Complete validation above before writing any staged command.
        try:
            for sid,deg in zip(ids,angles_deg):
                self.write(sid,MOVE_WAIT,struct.pack('<HH',round(float(deg)*1000/240),duration_ms))
            self.write(254,MOVE_START)
        except Exception:
            # Do not broadcast START after any staging failure. Latched controller
            # fault prevents a later START from accidentally running stale targets.
            raise

