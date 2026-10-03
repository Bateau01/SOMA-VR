"""Production light reconstruction: independent projection/reprojection oracle.
This is mathematical/native-layout validation, not a headset render test.
"""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
static u8 r[0xc40];static int nativeCalls,checks;static void* frustum=(void*)1234;
static int h20_mem_readable(const void*p,u64 n){u64 a=(u64)p,b=(u64)r;return a>=b&&a-b<=sizeof(r)&&n<=sizeof(r)-(a-b);}
static int h20_mem_writable(void*p,u64 n){return h20_mem_readable(p,n);}
static void ext_Log(const char*f,...){(void)f;}
static void* ext_GetModuleHandleA(void*p){return 0;}
static int ext_MH_CreateHook(void*a,void*b,void**c){return -1;}static int ext_MH_EnableHook(void*a){return -1;}
static void __attribute__((ms_abi)) native(void*p){nativeCalls++;}
static volatile i32 p2Frame;static volatile i32* p2_frame_ptr(void){return &p2Frame;}
static int depthObserves,depthEye=-1;static void s26ed_depth_observe(const u8*q,i32 eye){(void)q;depthObserves++;depthEye=eye;}
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 float old[4],q[4],p[16]={0};p[0]=.603496f;p[5]=.595665f;p[10]=-1.0002f;p[11]=-1;p[14]=-.02f;
 old[0]=.942710f;old[1]=.951746f;old[2]=-1655.398438f;old[3]=-1722.660767f;
 CHECK(s26do_light_coefficients(p,1000,3512,3620,old,q));
 CHECK(fabsf(q[1]-old[1])>.02f); // Supplied log's first-eye discrepancy.
 for(int w=1024;w<=8192;w*=2)for(int h=1024;h<=8192;h*=2)for(int eye=0;eye<2;eye++)for(int asym=-2;asym<=2;asym++){
  p[0]=eye?.604084f:.603496f;p[5]=eye?.580497f:.595665f;p[8]=asym*.1f;p[9]=-asym*.07f;
  old[0]=1.23f;old[1]=.93f;old[2]=-old[0]*w*.5f;old[3]=-old[1]*h*.5f;
  CHECK(s26do_light_coefficients(p,1000,w,h,old,q));
  for(int x=0;x<=8;x++)for(int y=0;y<=8;y++)for(int depth=1;depth<=4;depth++){
   float px=w*x/8.f,py=h*y/8.f,d=depth*.15f;
   float X=(px*q[0]+q[2])*d,Y=(py*q[1]+q[3])*d,Z=-1000*d;
   // Independent homogeneous projection of the reconstructed point.
   float ndcx=(p[0]*X+p[8]*Z)/(-Z),ndcy=(p[5]*Y+p[9]*Z)/(-Z);
   CHECK(fabsf((ndcx+1)*w*.5f-px)<.01f);CHECK(fabsf((ndcy+1)*h*.5f-py)<.01f);
  }
 }
 float good[16];memcpy(good,p,sizeof(p));
 for(int fault=0;fault<10;fault++){
  memcpy(p,good,sizeof(p));old[0]=1;old[1]=1;old[2]=-1024;old[3]=-1024;float far=1000;int w=2048,h=2048;
  if(fault==0)p[0]=0;if(fault==1)p[5]=NAN;if(fault==2)p[11]=1;if(fault==3)p[15]=1;if(fault==4)p[1]=.1f;
  if(fault==5)old[2]-=100;if(fault==6)old[1]=0;if(fault==7)far=NAN;if(fault==8)w=0;if(fault==9)h=40000;
  float out[4]={42,42,42,42};CHECK(!s26do_light_coefficients(p,far,w,h,old,out));CHECK(out[0]==42&&out[3]==42);
 }
 memset(r,0,sizeof(r));memcpy(r+0xaa4,good,64);*(void**)(r+0x20)=frustum;*(i32*)(r+0x40)=2048;*(i32*)(r+0x44)=2048;*(float*)(r+0xbe4)=1000;
 old[0]=1;old[1]=1;old[2]=-1024;old[3]=-1024;memcpy(r+0xbf4,old,16);
 o_s26doLightSetup=native;u8 before[sizeof(r)];memcpy(before,r,sizeof(r));
 s26do_light_setup(r);CHECK(nativeCalls==1&&!memcmp(r,before,sizeof(r))&&depthObserves==0); // No VR scope.
 g_s26doLightRenderer=r;g_s26doLightFrustum=(void*)999;s26do_light_setup(r);CHECK(nativeCalls==2&&!memcmp(r,before,sizeof(r))&&depthObserves==0); // Reflection/other frustum.
 p2Frame=7;g_s26doLightFrustum=frustum;s26do_light_setup(r);CHECK(nativeCalls==3&&memcmp(r,before,sizeof(r)));
 CHECK(depthObserves==1&&depthEye==1); // Depth layer observes only the scoped main eye.
 CHECK(s26do_light_coefficients(good,1000,2048,2048,old,q));CHECK(!memcmp(r+0xbf4,q,16));
 CHECK(*(float*)(r+0x95c)==q[2]&&*(float*)(r+0x960)==q[3]&&*(float*)(r+0x964)==q[0]&&*(float*)(r+0x968)==q[1]);
 for(int n=0;n<sizeof(r);n++)if(!(n>=0x95c&&n<0x96c)&&!(n>=0xbf4&&n<0xc04))CHECK(r[n]==before[n]);
 printf("PASS %d projection/reprojection, rejection and native-layout scope checks\n",checks);return 0;
}
'''
c=B/'light_projection_test.c';c.write_text(head+(R/'source/light_projection_do.inc').read_text()+main)
exe=B/'light_projection_test.exe'
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
