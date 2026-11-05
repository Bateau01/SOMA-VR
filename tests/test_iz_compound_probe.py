"""Run the production near-panel helper against SOMA's real Newton DLL, in a private world."""
from pathlib import Path
import ctypes as C,subprocess,math,json,sys
r=Path(__file__).resolve().parents[1];out=r/'audit/iz-compound';out.mkdir(parents=True,exist_ok=True)
s=(r/'source/s26n.c').read_text();a=s.index('static i32 s26iy_panel_near(');b=s.index('static i32 h576j_decode_panel_token',a)
prefix='''
#include <math.h>
typedef int i32;
static void *g_h14NewtonWorld,*g_h576jPanelCapturedRaw,*g_h576bOmniBody;
static const void* (*p_h14GetCollision)(const void*);
static void (*p_h14GetMatrix)(const void*,float*);
static int (*p_h14PointDistance)(const void*,const float*,const void*,const float*,float*,float*,int);
static int h9_good(float x,float limit){return isfinite(x)&&fabsf(x)<limit;}
static float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
'''
code=prefix+s[a:b]+'''
__declspec(dllexport) int check(void* w,void* tool,void* panel,void* getcol,void* getmat,void* distance){
 g_h14NewtonWorld=w;g_h576bOmniBody=tool;g_h576jPanelCapturedRaw=panel;
 p_h14GetCollision=getcol;p_h14GetMatrix=getmat;p_h14PointDistance=distance;
 float cp[3],cn[3];return s26iy_panel_near(cp,cn);
}
'''
(out/'helper.c').write_text(code)
subprocess.run([sys.argv[1],'cc','-shared','-O2',str(out/'helper.c'),'-o',str(out/'helper.dll')],check=True)
n=C.CDLL('D:/SteamLibrary/steamapps/common/SOMA/Newton.dll');P=C.c_void_p;F=C.c_float;I=C.c_int;FP=C.POINTER(F)
def api(name,ret,args):
 f=getattr(n,name);f.restype=ret;f.argtypes=args;return f
create=api('NewtonCreate',P,[P,P]);destroy=api('NewtonDestroy',None,[P]);box=api('NewtonCreateBox',P,[P,F,F,F,I,FP]);body=api('NewtonCreateBody',P,[P,P,FP]);setmat=api('NewtonBodySetMatrix',None,[P,FP]);release=api('NewtonReleaseCollision',None,[P,P])
def matrix(x,y,z):return (F*16)(1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1)
h=C.CDLL(str(out/'helper.dll'));h.check.argtypes=[P]*6;h.check.restype=I
w=create(None,None);result=[]
try:
 compound=api('NewtonCreateCompoundCollision',P,[P,I,C.POINTER(P),I])
 c1=box(w,.2,.4,.04,0,None);c2=box(w,.04,.04,.04,0,matrix(.2,0,0));children=(P*2)(c1,c2)
 c=compound(w,2,children,0);panel=body(w,c,matrix(3,2,-1));release(w,c);release(w,c1);release(w,c2)
 c=box(w,.04,.1,.02,0,None);tool=body(w,c,matrix(3,2,-1));release(w,c)
 closest=api('NewtonCollisionClosestPoint',I,[P,P,FP,P,FP,FP,FP,FP,I])
 getcol=api('NewtonBodyGetCollision',P,[P])
 for gap in (.001,.04,.079,.081,.2):
  setmat(tool,matrix(3,2,-1+.02+gap));value=h.check(w,tool,panel,n.NewtonBodyGetCollision,n.NewtonBodyGetMatrix,n.NewtonCollisionPointDistance)
  ca=(F*4)(1e20,1e20,1e20,0);cb=(F*4)(1e20,1e20,1e20,0);normal=(F*4)()
  ok=closest(w,getcol(tool),matrix(3,2,-1+.02+gap),getcol(panel),matrix(3,2,-1),ca,cb,normal,0)
  print("compound gap/result/closest",gap,value,ok,list(ca),list(cb),flush=True)
  result.append({'surface_gap':gap,'accepted':bool(value)})
 assert h.check(w,None,panel,n.NewtonBodyGetCollision,n.NewtonBodyGetMatrix,n.NewtonCollisionPointDistance)==0
finally:destroy(w)
(out/'result.json').write_text(json.dumps({'passed':True,'scope':__doc__,'cases':result},indent=2));print(json.dumps(result))
