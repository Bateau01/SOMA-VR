"""Private native Newton worlds with modeled production motor laws and sampled90Hz motion. No game callbacks, scene contacts, DLL adapter or headset execution."""
from pathlib import Path
import sys,ctypes as c,json,math,re
R=Path(__file__).resolve().parents[1]
exec((R/'tests/test_newton_rate.py').read_text().split("results=[run(hz,mode)")[0])
src=(R/'source/s26n.c').read_text()
def constant(name):return float(re.search(r'^#define '+name+r'\s+([0-9.]+)f',src,re.M)[1])
slide_kp=constant('H5755EA_SLIDE_POSITION_KP');slide_cap=constant('H5755EA_SLIDE_TARGET_SPEED_CAP')
torque=api('NewtonBodySetTorque',[P,FP]);records=[]
for kind in ('slider','light_door','heavy_door','wheel'):
 for speed in (.5,1.5,3.5):
  for hz in (60,120):
   w=create(None,None);clock=0.;previous=0.;angle=0.;last_hand=0.;phase=0.;forces=[];targets=[];travels=[]
   try:
    shape=box(w,.5,.5,.2,0,None);b=body(w,shape,mat(0,0,0));release(w,shape);mass(b,2,1,1,1);sleep(b,0);damp(b,0);adamp(b,arr([0,0,0]))
    if kind=='slider':slider(w,arr([0,0,0]),arr([1,0,0]),b,None)
    else:hinge(w,arr([0,0,0]),arr([0,1,0]),b,None)
    @CB
    def motor(raw,dt,thread):
     global previous,last_hand,phase
     tracked=math.floor((clock+1e-8)*90)/90*speed
     delta=tracked-last_hand;last_hand=tracked
     if kind=='slider':
      pos=read(matrix,raw,16)[12];v=read(velocity,raw,3)[0];wanted=max(-slide_cap,min(slide_cap,slide_kp*(tracked-pos)));p=6;d=.1
     else:
      v=read(omega,raw,3)[1]
      if kind=='wheel':
       phase=max(-.15,min(.15,phase+delta-v*dt));wanted=max(-4,min(4,delta/dt+8*phase));p=15;d=.1
      else:
       err=tracked-angle;wanted=max(-12,min(12,24*err+(delta/dt if kind=='heavy_door' else 0)));p=(10 if kind=='light_door' else 20)/(1+(10 if kind=='light_door' else 20)*dt);d=0
     error=wanted-v;f=p*error+d*(error-previous)/dt;previous=error
     f=max(-100,min(100,f));forces.append(f);targets.append(wanted)
     if kind=='slider':force(raw,arr([2*f,0,0]))
     else:torque(raw,arr([0,f,0]))
    callback(b,c.cast(motor,P))
    for n in range(2*hz):
     clock=(n+1)/hz;update(w,1/hz);angle+=read(omega,b,3)[1]/hz
     travels.append(read(matrix,b,16)[12] if kind=='slider' else angle)
    records.append({'kind':kind,'speed':speed,'hz':hz,'travel':travels[-1],'target_min':min(targets[hz:]),'target_max':max(targets[hz:]),'peak_force':max(map(abs,forces))})
   finally:destroy(w)
p=R/'docs/v109-evidence/mechanism_cadence_ir.json';p.write_text(json.dumps({'scope':__doc__,'results':records},indent=2))
for a,b in zip(records[::2],records[1::2]):print(a['kind'],a['speed'],'60',round(a['travel'],6),'120',round(b['travel'],6),'delta',round(b['travel']-a['travel'],6),'120 target range',b['target_min'],b['target_max'])
