"""Exercise the production gaze acceptance and head-relative transform, not a stub."""
from pathlib import Path
import ctypes as c, subprocess,sys,json,os
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=Path(os.environ.get('SOMA_TEST_DFR_SOURCE',R/'source/foveation_ef.inc')).read_text();a=s.index('static i32 s26ei_read_foveation_gaze(');b=s.index('/* The light fix',a)
head=r'''
#include <math.h>
#include <string.h>
typedef unsigned char u8;typedef int i32;typedef long long i64;typedef unsigned u32;
typedef struct {float x,y,z,w;} XrQuaternionf;
typedef struct {XrQuaternionf orientation;float position[3];} XrPosef;
typedef struct {XrPosef eye,head;i64 time;u8 valid,headValid;} S26SEyeSample;
static u32 g_s26eiMeasureEpoch;static S26SEyeSample g_s26sEyeSample;static u32 g_s26ehGazeStats[7];static u8 xr[256];static int locked;
static int s26s_eye_lock(void){return !locked;}static void s26s_eye_unlock(void){}
static void*p2_xr_obj(void){return xr;}
static int s26s_pose_finite(const XrPosef*p){const float*f=(const float*)p;for(int i=0;i<7;i++)if(!isfinite(f[i]))return 0;return 1;}
static void s26s_quat_rotate(const XrQuaternionf*q,const float*v,float*out){
float t[3]={2*(q->y*v[2]-q->z*v[1]),2*(q->z*v[0]-q->x*v[2]),2*(q->x*v[1]-q->y*v[0])};
out[0]=v[0]+q->w*t[0]+q->y*t[2]-q->z*t[1];out[1]=v[1]+q->w*t[1]+q->z*t[0]-q->x*t[2];out[2]=v[2]+q->w*t[2]+q->x*t[1]-q->y*t[0];}
'''
tail=r'''
__declspec(dllexport) int check(i64 age,int valid,int hv,int lock,int bad,float angle,float*out){
memset(&g_s26sEyeSample,0,sizeof(g_s26sEyeSample));*(i64*)(xr+0xe8)=1000000000LL;
g_s26sEyeSample.time=1000000000LL-age;g_s26sEyeSample.valid=valid;g_s26sEyeSample.headValid=hv;locked=lock;
g_s26sEyeSample.eye.orientation.y=g_s26sEyeSample.head.orientation.y=sinf(angle/2);
g_s26sEyeSample.eye.orientation.w=g_s26sEyeSample.head.orientation.w=cosf(angle/2);
if(bad)g_s26sEyeSample.eye.orientation.x=NAN;
return s26ef_foveation_gaze(out);}
'''
p=B/'gaze_test.c';p.write_text(head+'\n#define ext_Sqrtf sqrtf\n#define ext_Sinf sinf\n#define ext_Cosf cosf\n'+(R/'source/foveation_tuning_ei.inc').read_text(encoding='utf-8-sig')+s[a:b]+tail);dll=B/'gaze_test.dll';subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-o',str(dll)],check=True)
l=c.CDLL(str(dll));l.check.argtypes=[c.c_longlong]+[c.c_int]*4+[c.c_float,c.POINTER(c.c_float)]
checks=0
for age in [-100000001,-100000000,-50000000,-10000001,0,50000000,50000001,75000000,100000000,100000001]:
 for angle in [-2.0,0,1.7]:
  out=(c.c_float*3)();expected=abs(age)<=100000000
  assert l.check(age,1,1,0,0,angle,out)==expected,(age,angle)
  if expected:assert abs(out[0])<1e-5 and abs(out[1])<1e-5 and abs(out[2]+1)<1e-5
  checks+=1
for flags in [(0,1,0,0),(1,0,0,0),(1,1,1,0),(1,1,0,1)]:
 out=(c.c_float*3)();assert not l.check(0,*flags,0,out);checks+=1
result={'passed':True,'checks':checks,'covers':['runtime delayed/predicted timestamp boundaries','invalid samples stay full rate','same-time eye/head rotation','lock failure','nonfinite pose']}
(B/'foveation_gaze_results.json').write_text(json.dumps(result,indent=2));print(result)
