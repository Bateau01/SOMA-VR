"""Private real Newton worlds comparing the shipped slider/hinge motor equations. No game scripts, actual scene, controller path or authored callbacks. Separates motor integration from live VR sampling."""
from pathlib import Path
import sys,ctypes as c,json,math
R=Path(__file__).resolve().parents[1]
# Load the common native Newton bindings without running its scenarios.
exec((R/'tests/test_newton_rate.py').read_text().split("results=[run(hz,mode)")[0])
torque=api('NewtonBodySetTorque',[P,FP]);records=[]
for kind in ('slider','light_door','heavy_door','wheel','lever'):
 for hz in (60,120):
  w=create(None,None);clock=0.;previous=0.;angle=0.;force_history=[]
  try:
   shape=box(w,.5,.5,.2,0,None);b=body(w,shape,mat(0,0,0));release(w,shape);mass(b,2,1,1,1);sleep(b,0);damp(b,0);adamp(b,arr([0,0,0]))
   if kind=='slider':slider(w,arr([0,0,0]),arr([1,0,0]),b,None)
   else:hinge(w,arr([0,0,0]),arr([0,1,0]),b,None)
   @CB
   def motor(raw,dt,thread):
    global previous
    if kind=='slider':
     pos=read(matrix,raw,16)[12];v=read(velocity,raw,3)[0];wanted=max(-2,min(2,12*(.3*clock-pos)));p=6;d=.1
    else:
     v=read(omega,raw,3)[1];wanted=.5
     if kind=='lever':p=10;d=1
     elif kind=='wheel':p=15;d=.1
     else:p=(10 if kind=='light_door' else 20)/(1+(10 if kind=='light_door' else 20)*dt);d=0
    error=wanted-v;f=p*error+d*(error-previous)/dt;previous=error
    f=max(-100,min(100,f));force_history.append(f)
    if kind=='slider':force(raw,arr([2*f,0,0]))
    else:torque(raw,arr([0,f,0]))
   callback(b,c.cast(motor,P))
   for n in range(2*hz):
    clock=n/hz;update(w,1/hz);angle+=read(omega,b,3)[1]/hz
   displacement=read(matrix,b,16)[12] if kind=='slider' else angle
   records.append({'kind':kind,'hz':hz,'travel':displacement,'max_accel':max(map(abs,force_history))})
  finally:destroy(w)
for a,b in zip(records[::2],records[1::2]):
 if a['kind']!='lever':assert abs(a['travel']-b['travel'])<.025,(a,b)
p=R/'docs/v109-evidence/mechanism_motors_lever_in.json';p.write_text(json.dumps({'scope':__doc__,'results':records},indent=2));print(json.dumps(records));print('Observed lever separately; PASS previous equal-time motor integration in private Newton worlds; not complete gameplay or hardware validation')
