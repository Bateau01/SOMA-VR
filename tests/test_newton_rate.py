"""Actual Newton 2.36 DLL: equal-time 60/120 comparisons in private worlds."""
import ctypes as c,math,json,time,sys,argparse
from pathlib import Path
A=Path(__file__).resolve().parents[1]/'audit/newton';A.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--dll',required=True);parser.add_argument('--corrected',action='store_true');args=parser.parse_args();d=c.WinDLL(args.dll);P=c.c_void_p;F=c.c_float;I=c.c_int;FP=c.POINTER(F)
def api(n,a,r=None):
 f=getattr(d,n);f.argtypes=a;f.restype=r;return f
create=api('NewtonCreate',[P,P],P);destroy=api('NewtonDestroy',[P]);box=api('NewtonCreateBox',[P,F,F,F,I,FP],P);body=api('NewtonCreateBody',[P,P,FP],P);release=api('NewtonReleaseCollision',[P,P]);mass=api('NewtonBodySetMassMatrix',[P,F,F,F,F]);matrix=api('NewtonBodyGetMatrix',[P,FP]);velocity=api('NewtonBodyGetVelocity',[P,FP]);setvel=api('NewtonBodySetVelocity',[P,FP]);force=api('NewtonBodySetForce',[P,FP]);sleep=api('NewtonBodySetAutoSleep',[P,I]);sleeping=api('NewtonBodyGetSleepState',[P],I);damp=api('NewtonBodySetLinearDamping',[P,F]);update=api('NewtonUpdate',[P,F]);callback=api('NewtonBodySetForceAndTorqueCallback',[P,P]);CB=c.CFUNCTYPE(None,P,F,I)
omega=api('NewtonBodyGetOmega',[P,FP]);setomega=api('NewtonBodySetOmega',[P,FP]);adamp=api('NewtonBodySetAngularDamping',[P,FP]);hinge=api('NewtonConstraintCreateHinge',[P,FP,FP,P,P],P);slider=api('NewtonConstraintCreateSlider',[P,FP,FP,P,P],P)
def arr(v):return (F*len(v))(*v)
def mat(x,y,z):return arr([1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1])
def read(f,b,n):
 a=(F*n)();f(b,a);return list(a)
corrected='--corrected' in sys.argv
def run(hz,mode):
 w=create(None,None);refs=[];clock=0.;observed=[]
 try:
  floor=box(w,20,.5,20,0,None);b0=body(w,floor,mat(0,-.25,0));release(w,floor)
  s=box(w,1 if mode=='hinge' else .2,2 if mode=='hinge' else .2,.2,1,None);b=body(w,s,mat(0,2,0));release(w,s);mass(b,1,.336667 if mode=='hinge' else .006667,.086667 if mode=='hinge' else .006667,.416667 if mode=='hinge' else .006667);sleep(b,1);damp(b,0)
  @CB
  def gravity(raw,dt,thread):
   observed.append(float(dt))
   if mode=='servo':
    pos=read(matrix,raw,16);vel=read(velocity,raw,3);goal=[math.sin(clock*1.2)*.4,1.5,0]
    f=[max(-100,min(100,80*(goal[i]-pos[12+i])-16*vel[i])) for i in range(3)];force(raw,arr(f))
   elif mode in ('damping','angular'):force(raw,arr([0,0,0]))
   else:force(raw,arr([0,-9.81,0]))
  refs.append(gravity);callback(b,c.cast(gravity,P))
  if mode=='damping':damp(b,.15);setvel(b,arr([1,0,0]))
  if mode=='angular':adamp(b,arr([.15,.25,.4]));setomega(b,arr([1,0,0]))
  if mode=='hinge':hinge(w,arr([-.5,2,0]),arr([0,0,1]),b,None)
  if mode=='slider':slider(w,arr([0,2,0]),arr([0,1,0]),b,None)
  start=time.perf_counter();samples={}
  for step in range(hz*5):
   clock=step/hz
   fields=(F*4).from_address(b+0x1c0); saved=list(fields)
   if corrected and hz==120:
    for i,x in enumerate(saved): fields[i]=x/(1+math.sqrt(1-x)) if 0<x<1 else x
   update(w,1/hz)
   if corrected and hz==120:
    for i,x in enumerate(saved):fields[i]=x
   if step+1 in (hz//2,hz,hz*5):samples[str((step+1)/hz)]={'pos':read(matrix,b,16)[12:15],'vel':read(velocity,b,3),'sleep':sleeping(b),'omega':read(omega,b,3)}
  result={'hz':hz,'mode':mode,'samples':samples,'cpu_ms':(time.perf_counter()-start)*1000,'callback_dt_min':min(observed),'callback_dt_max':max(observed)}
  assert all(math.isfinite(v) for s in samples.values() for v in s['pos']+s['vel'])
  assert abs(max(observed)-1/hz)<1e-6
  if mode=='drop':assert .08<samples['5.0']['pos'][1]<.12 and abs(samples['5.0']['vel'][1])<.02
  if mode=='servo':assert abs(samples['5.0']['pos'][1]-1.5)<.01
  return result
 finally:destroy(w)
results=[run(hz,mode) for mode in ('drop','servo','damping','angular','hinge','slider') for hz in (60,120)]
(A/('corrected.json' if corrected else 'uncorrected.json')).write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
for a,b in zip(results[::2],results[1::2]):
 delta=max(abs(x-y) for x,y in zip(a['samples']['5.0']['pos'],b['samples']['5.0']['pos']))
 assert delta<.06,(a['mode'],delta)
 if a['mode']=='angular':assert abs(a['samples']['5.0']['omega'][0]-b['samples']['5.0']['omega'][0])<.002
print('PASS: native Newton drop/contact, held-style servo and damping comparisons; no game geometry or headset used')
