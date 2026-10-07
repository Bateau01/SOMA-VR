"""Real Newton DLL validation of the production inventory-draw preparation."""
from pathlib import Path
import subprocess,sys,ctypes as c,json,math,re,os
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head=r"""
#include <windows.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
#define ext_Sqrtf sqrtf
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_GetProcAddress GetProcAddress
#define ext_Log(...) ((void)0)
typedef void (*S26EFBounds)(const void*,const float*,float*,float*);
static S26EFBounds p_s26efBounds;
static const char* s26el_grip_profile(const void*b,const char*n){return n;}
static int s26ej_grip_override(int h,int k,const char*n,float*r,float*f){return 0;}
static u8 g_s26efHolsterLatch[2],g_h552ContactLatchBypass[2];
static float g_s26efHolsterCurl[2][5];static const void*g_h14GripBody[2];
static u32 (*p_s26efGripThread)(void);
static void*g_h14NewtonWorld;static float testPhysical[16],testBasis[9];static int havePhysical;
static const void* collision(const void*p){return p;}
static const void*(*p_h14GetCollision)(const void*)=collision;
static int (*p_h14PointDistance)(void*,const float*,const void*,const float*,float*,float*,int);
static int h576c_ci_streq(const char*a,const char*b){return _stricmp(a,b)==0;}
static int h9_good(float v,float lim){return isfinite(v)&&fabsf(v)<lim;}
static void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
static void h10_matmul(const float*a,const float*b,float*o){float t[16];for(int j=0;j<4;j++)for(int i=0;i<4;i++){t[j*4+i]=0;for(int k=0;k<4;k++)t[j*4+i]+=a[k*4+i]*b[j*4+k];}memcpy(o,t,64);}
static void h14_rigid_inverse(const float*m,float*o){for(int i=0;i<16;i++)o[i]=0;for(int i=0;i<3;i++)for(int j=0;j<3;j++)o[i*4+j]=m[j*4+i];for(int i=0;i<3;i++)o[12+i]=-o[i]*m[12]-o[4+i]*m[13]-o[8+i]*m[14];o[15]=1;}
static void h14_transform_point(const float*m,const float*p,float*o){float t[3];for(int i=0;i<3;i++)t[i]=m[i]*p[0]+m[4+i]*p[1]+m[8+i]*p[2]+m[12+i];memcpy(o,t,12);}
static int h34_physical_hand_model(int h,float*m){if(!havePhysical)return 0;memcpy(m,testPhysical,64);return 1;}
static void quat_to_game_basis(int h,float*b){memcpy(b,testBasis,36);}
"""
tail=r"""
static void*(*createworld)(void);static void(*destroyworld)(void*);
static void*(*box)(void*,float,float,float,int,const float*);static void(*release)(void*,void*);
__declspec(dllexport) int setup(const char*path){HMODULE n=LoadLibraryA(path);if(!n)return 0;
createworld=(void*)GetProcAddress(n,"NewtonCreate");destroyworld=(void*)GetProcAddress(n,"NewtonDestroy");box=(void*)GetProcAddress(n,"NewtonCreateBox");release=(void*)GetProcAddress(n,"NewtonReleaseCollision");p_h14PointDistance=(void*)GetProcAddress(n,"NewtonCollisionPointDistance");
if(!createworld||!destroyworld||!box||!release||!p_h14PointDistance)return 0;g_h14NewtonWorld=createworld();return g_h14NewtonWorld!=0;}
__declspec(dllexport) int prepare(int hand,int kind,const char*name,float*hm,float*gc,float*out,float scale,int physical){
float id[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
void*col=box(g_h14NewtonWorld,.12f*scale,.20f*scale,.30f*scale,0,id);if(!col)return 0;
memcpy(testPhysical,hm,64);testPhysical[12]+=.025f;havePhysical=physical;
for(int a=0;a<3;a++)for(int b=0;b<3;b++)testBasis[a*3+b]=hm[a*4+b];
int ok=s26ef_prepare_holster(hand,kind,name,col,hm,gc,out);release(g_h14NewtonWorld,col);return ok;}
__declspec(dllexport) int scopes(void){for(int h=0;h<2;h++){s26ef_holster_latch_begin(h);if(!g_s26efHolsterLatch[h]||!g_h552ContactLatchBypass[h]||g_s26efHolsterLatch[1-h])return 0;s26ef_holster_latch_end(h);if(g_s26efHolsterLatch[h]||g_h552ContactLatchBypass[h])return 0;}return 1;}
__declspec(dllexport) int prepare_pose(int hand,int kind,const char*name,const float*raw,const float*physical,const float*controller,float*out){
float id[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},hm[16],gc[3]={raw[12],raw[13],raw[14]};
void*col=box(g_h14NewtonWorld,.12f,.20f,.30f,0,id);if(!col)return 0;
memcpy(hm,raw,64);memcpy(testPhysical,physical,64);havePhysical=1;
for(int a=0;a<3;a++)for(int b=0;b<3;b++)testBasis[a*3+b]=controller[a*4+b];
int ok=s26ef_prepare_holster(hand,kind,name,col,hm,gc,out);release(g_h14NewtonWorld,col);return ok;}
__declspec(dllexport) void close_world(void){destroyworld(g_h14NewtonWorld);}
"""
p=B/'holster_native_test.c';runtime_source=Path(os.environ.get('SOMA_TEST_HOLSTER_SOURCE',str(R/'source/holster_runtime_ef.inc')))
p.write_text(head+(R/'source/holster_grip_ef.inc').read_text()+runtime_source.read_text()+tail)
dll=B/'holster_native_test.dll';subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-o',str(dll)],check=True)
lib=c.CDLL(str(dll));F=c.c_float;P=c.POINTER(F);lib.setup.argtypes=[c.c_char_p];assert lib.setup(b'D:/SteamLibrary/steamapps/common/SOMA/Newton.dll')
lib.prepare.argtypes=[c.c_int,c.c_int,c.c_char_p,P,P,P,F,c.c_int]
checks=0
tool=(R/'runtime/script/modules/PlayerToolHandler.hps').read_text()
known=tool[tool.index('bool VR_IsKnownShoulderKeyItemName'):tool.index('bool VR_IsRegisteredShoulderKeyItemName')]
items=[(1,'OmniTool'),(2,'Phone')]+[(0,n) for n in re.findall(r'asName == "([^"]+)"',known)]
assert len(items)>=20
for hand in [0,1]:
 for scale in [.7,1,1.25]:
  for kind,item in items:
   previous=None
   for physical in [0,1]:
    hm=(F*16)(1,0,0,0,0,1,0,0,0,0,1,0,3,2,1,1);gc=(F*3)(3.04,2.07,.98);out=(F*16)()
    assert lib.prepare(hand,kind,item.encode(),hm,gc,out,scale,physical),(hand,item)
    assert all(math.isfinite(x) for x in out)
    for a in range(3):assert abs(sum(out[a*4+j]**2 for j in range(3))-1)<1e-5
    if previous:assert abs(out[12]-previous[12]-.025)<1e-5 and abs(gc[0]-3.065)<1e-5
    previous=list(out);checks+=1
assert lib.scopes();checks+=1
# End-to-end orientation composition used by h14_latch and the held solver.
# Calibration, inverted shoulder poses and collision-root rotations are distinct.
def mul(a,b):return [sum(a[k*4+i]*b[j*4+k] for k in range(4)) for j in range(4) for i in range(4)]
def inv(a):
 o=[a[(i%4)*4+i//4] if i%4<3 and i//4<3 else 0 for i in range(16)];o[15]=1
 for i in range(3):o[12+i]=-sum(o[k*4+i]*a[12+k] for k in range(3))
 return o
def rotation(axis,angle):
 c,s=math.cos(angle),math.sin(angle)
 if axis==0:return [1,0,0,0,0,c,s,0,0,-s,c,0,0,0,0,1]
 if axis==1:return [c,0,-s,0,0,1,0,0,s,0,c,0,0,0,0,1]
 return [c,s,0,0,-s,c,0,0,0,0,1,0,0,0,0,1]
profile=rotation(0,0) # Authored tool head -Z must follow OpenXR grip -Z.
lib.prepare_pose.argtypes=[c.c_int,c.c_int,c.c_char_p,P,P,P,P]
orientation_checks=0
for hand in [0,1]:
 for shoulder in [-math.pi,-1.5,0,1.5,math.pi]:
  controller=mul(rotation(1,.71),rotation(0,shoulder))
  calibration=mul(rotation(2,.8 if hand else -.8),rotation(0,-.4))
  raw=mul(controller,calibration)
  for axis in range(3):
   for blocked in [-1.57,-.6,0,.6,1.57]:
    physical=mul(raw,rotation(axis,blocked));out=(F*16)()
    assert lib.prepare_pose(hand,1,b'OmniTool',(F*16)(*raw),(F*16)(*physical),(F*16)(*controller),out)
    offset=mul(inv(raw),physical);relative=mul(inv(physical),list(out))
    for later in [-2.1,0,.9]:
     next_controller=mul(rotation(1,-.3),rotation(0,later));next_raw=mul(next_controller,calibration)
     held=mul(mul(next_raw,offset),relative);expected=mul(next_controller,profile)
     assert all(abs(held[col*4+row]-expected[col*4+row])<2e-5 for col in range(3) for row in range(3)),(hand,shoulder,axis,blocked,later)
     # Semantic check independent of a profile constant: head direction through
     # the held shaft follows the little-finger-to-thumb axis of the grip.
     assert sum(held[8+i]*next_controller[8+i] for i in range(3))>0.99999
     orientation_checks+=1
checks+=orientation_checks
lib.close_world()
# Inventory-only call sites: do not alter normal loose grabs or slot detachment.
s=(R/'source/s26n.c').read_text();phone=(R/'source/phone_x.inc').read_text()
assert s.count('s26ef_prepare_holster(')==2 and phone.count('s26ef_prepare_holster(')==1
assert s.count('s26ef_holster_latch_begin(hand);h14_latch')==2
assert 's26ef_holster_latch_begin(1);h14_latch' in phone
result={'passed':True,'checks':checks,'orientation_checks':orientation_checks,'native_dll':'Newton.dll','covers':['both hands','item categories','scaled shapes','physical-hand offset','unit object scale','draw-only scopes','inverted shoulder to upright controller','collision-root rotation excluded from held orientation']}
(B/'holster_native_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
