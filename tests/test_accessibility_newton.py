"""Isolated world in SOMA's actual Newton.dll: ray ABI, blockers and sleep wake.
Does not load a save or touch the running game's physics world.
"""
from pathlib import Path
import ctypes as C,json
R=Path(__file__).resolve().parents[1];n=C.CDLL(r'D:\SteamLibrary\steamapps\common\SOMA\Newton.dll')
P=C.c_void_p;F=C.c_float;I=C.c_int;V=F*16;Vec=F*4
def api(name,restype,args):
 f=getattr(n,name);f.restype=restype;f.argtypes=args;return f
create=api('NewtonCreate',P,[]);destroy=api('NewtonDestroy',None,[P]);box=api('NewtonCreateBox',P,[P,F,F,F,I,P]);body=api('NewtonCreateBody',P,[P,P,P])
mass=api('NewtonBodySetMassMatrix',None,[P,F,F,F,F]);vel=api('NewtonBodySetVelocity',None,[P,P]);matrix=api('NewtonBodyGetMatrix',None,[P,P]);update=api('NewtonUpdate',None,[P,F]);freeze=api('NewtonBodySetFreezeState',None,[P,I])
Filter=C.CFUNCTYPE(F,P,P,I,P,F);Pre=C.CFUNCTYPE(C.c_uint,P,P,P)
ray=api('NewtonWorldRayCast',None,[P,P,P,Filter,P,Pre])
def mat(x):return V(1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1)
world=create();results={}
try:
 c=box(world,.2,.2,.2,1,None);b=body(world,c,mat(1));mass(b,1,.01,.01,.01)
 wallcol=box(world,.1,2,2,2,None);wall=body(world,wallcol,mat(.5))
 hits=[]
 @Filter
 def filt(b,norm,id,data,t):hits.append((b,t));return t
 @Pre
 def pre(b,col,data):return 1
 ray(world,Vec(0,0,0,0),Vec(2,0,0,0),filt,None,pre)
 nearest=min(hits,key=lambda h:h[1]);assert nearest[0]==wall and abs(nearest[1]-.225)<.002
 results['opaque_wall_blocks_selection']=True
 # Pull away from wall; an asleep prop must wake when velocity is assigned.
 freeze(b,1);vel(b,Vec(1,0,0,0));update(world,1/60);m=V();matrix(b,m)
 results['velocity_alone_wakes_frozen_body']=m[12]>1.001;results['position_after_velocity']=m[12]
 freeze(b,0);vel(b,Vec(1,0,0,0));update(world,1/60);matrix(b,m)
 results['explicit_wake_then_velocity']=m[12]>1.001
 # Match repeated corrections at each rate, testing real collision response.
 for hz in (60,120):
  bw=body(world,c,mat(1));mass(bw,1,.01,.01,.01)
  for i in range(hz):vel(bw,Vec(-1.5,0,0,0));update(world,1/hz)
  matrix(bw,m);assert m[12]>.57,(hz,m[12]);results[f'wall_collision_{hz}hz']=float(m[12])
finally:destroy(world)
(R/'audit/accessibility_newton.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
assert results['explicit_wake_then_velocity'],'Explicit wake failed'
