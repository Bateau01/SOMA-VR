"""Run the production near-panel helper against SOMA's real Newton DLL, in a private world."""
from pathlib import Path
import ctypes as C,subprocess,math,json,sys
r=Path(__file__).resolve().parents[1];out=r/'audit/iz-panel';out.mkdir(parents=True,exist_ok=True)
s=(r/'source/s26n.c').read_text();a=s.index('typedef i32 (__attribute__((ms_abi)) *PFN_S26IZ_Closest)');b=s.index('static i32 h576j_decode_panel_token',a)
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
 p_h14GetCollision=getcol;p_h14GetMatrix=getmat;p_s26izClosest=distance;
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
 c=box(w,.2,.4,.04,0,None);panel=body(w,c,matrix(3,2,-1));release(w,c)
 c=box(w,.04,.1,.4,0,None);tool=body(w,c,matrix(3,2,-1));release(w,c)
 for gap in (.001,.04,.079,.081,.2):
  setmat(tool,matrix(3,2,-1+.02+.2+gap));value=h.check(w,tool,panel,n.NewtonBodyGetCollision,n.NewtonBodyGetMatrix,n.NewtonCollisionClosestPoint)
  assert value==int(gap<.08),(gap,value)
  result.append({'surface_gap':gap,'accepted':bool(value)})
 assert h.check(w,None,panel,n.NewtonBodyGetCollision,n.NewtonBodyGetMatrix,n.NewtonCollisionClosestPoint)==0
 # Author-defined compound panel and upgraded Omni-Tool collision primitives (boxes and cylinders).
 import xml.etree.ElementTree as ET
 compound=api('NewtonCreateCompoundCollision',P,[P,I,C.POINTER(P),I])
 cylinder=api('NewtonCreateCylinder',P,[P,F,F,I,FP])
 euler=api('NewtonSetEulerAngle',None,[FP,FP]);getmat=api('NewtonBodyGetMatrix',None,[P,FP]);getcol=api('NewtonBodyGetCollision',P,[P])
 pd=api('NewtonCollisionPointDistance',I,[P,FP,P,FP,FP,FP,I])
 def authored(file):
  tree=ET.parse(file);bd=tree.find('.//Body');scale=[float(v) for v in bd.get('Scale').split()];ids={e.get('ID') for e in bd.findall('Shape')};children=[]
  for sh in tree.findall('.//Shapes/Shape'):
   if sh.get('ID') not in ids:continue
   assert sh.get('ShapeType') in ('Box','Cylinder')
   dims=[float(v)*scale[i] for i,v in enumerate(sh.get('Scale').split())]
   pos=[float(v)*scale[i] for i,v in enumerate(sh.get('RelativeTranslation').split())]
   rot=(F*3)(*[float(v) for v in sh.get('RelativeRotation').split()]);m=matrix(*pos);euler(rot,m);m[12:15]=pos
   children.append(box(w,*dims,0,m) if sh.get('ShapeType')=='Box' else cylinder(w,dims[0],dims[1],0,m))
  c=compound(w,len(children),(P*len(children))(*children),0);obj=body(w,c,matrix(0,0,0));release(w,c)
  for child in children:release(w,child)
  return obj
 game=Path('D:/SteamLibrary/steamapps/common/SOMA')
 actualpanel=authored(game/'entities/station/panels/omnitool_panel/omnitool_panel.ent')
 actualtool=authored(game/'entities/station/gameplay/omnitool/omnitool_with_securitychip_cortexchip.ent')
 wins=[]
 for yaw in (0,math.pi/2,math.pi,3*math.pi/2):
  for j in range(10,65):
   m=matrix(0,0,j/100);euler((F*3)(0,yaw,0),m);m[14]=j/100;setmat(actualtool,m)
   before=(F*16)();getmat(actualtool,before)
   new=h.check(w,actualtool,actualpanel,n.NewtonBodyGetCollision,n.NewtonBodyGetMatrix,n.NewtonCollisionClosestPoint)
   cp=(F*4)(1e30,1e30,1e30,0);norm=(F*4)();point=(F*4)(m[12],m[13],m[14],0)
   outside=pd(w,point,getcol(actualpanel),matrix(0,0,0),cp,norm,0)
   distance=math.sqrt(sum((cp[i]-point[i])**2 for i in range(3)))
   old=int((outside or distance<=.00001) and distance<=.08)
   if new and not old:wins.append({'yaw':yaw,'z':j/100,'old_centre_distance':distance})
   after=(F*16)();getmat(actualtool,after);assert list(before)==list(after),'query mutated tool'
 assert wins,'No baseline rejection reproduced with authored compound shapes'
 result.append({'authored_compound_old_reject_new_accept_cases':len(wins),'examples':wins[:4]})
finally:destroy(w)
(out/'result.json').write_text(json.dumps({'passed':True,'scope':__doc__,'cases':result},indent=2));print(json.dumps(result))
