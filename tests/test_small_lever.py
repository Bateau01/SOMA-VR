from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();start=s.index('static void s26dr_scan_small_lever(');end=s.index('static void __attribute__((ms_abi)) h14_scan_body',start);fn=s[start:end]
head=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
typedef int i32;typedef unsigned char u8;
typedef struct {int drEnabled,hand;float drHandM[16],drP[6][3],rad[6];const void* drBody;void* drOwner;float drGap,drSecondGap,drContact[3];} H14Scan;
static int can=1,icon=6,jointed=0,outside=0,validmesh=1,calls=0,ownerKind=1;static float meshgap=.006f,pointgap=.006f;static const void* raw=(void*)1;static void* g_h14NewtonWorld=(void*)10;
static int h25_owner_kind(void*o,char*r,int n){return ownerKind;}
static int h20_mem_readable(void*w,int size){return w!=0;}
static const void* h568_first_external_joint(const void*b){return jointed?(void*)2:0;}
static int h576ad_target_can_interact(void*w,void*o,const void**r,int*i){*r=raw;*i=icon;return can;}
static void p_h14GetMatrix(const void*b,float*m){(void)b;(void)m;}
static int p_h14PointDistance(void*w,const float*p,const void*c,const float*m,float*out,float*n,int t){calls++;out[0]=p[0]+pointgap;out[1]=p[1];out[2]=p[2];return outside;}
static float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
static void h14_rigid_inverse(const float*m,float*i){}
static void h14_transform_point(const float*m,const float*p,float*out){}
static int h20_nearest_hand_mesh_local(int h,const float*p,float*m,int*t,float*b,float*g){*g=meshgap;return validmesh;}
static int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){unsigned char wrapper[0x300]={0};*(void**)(wrapper+0x2c0)=(void*)4;wrapper[0xe4]=1;
for(int hand=0;hand<2;hand++)for(int fault=0;fault<13;fault++){
 H14Scan s={0};s.drEnabled=1;s.hand=hand;s.drGap=s.drSecondGap=999;for(int i=0;i<6;i++)s.rad[i]=.011f;
 ownerKind=1;can=validmesh=1;icon=6;raw=(void*)1;jointed=outside=calls=0;meshgap=pointgap=.006f;wrapper[0xe4]=1;wrapper[0x2e0]=0;float mass=0;
 switch(fault){case 1:outside=1;break;case 2:s.drEnabled=0;break;case 3:mass=1;break;case 4:wrapper[0xe4]=0;break;case 5:wrapper[0x2e0]=1;break;case 6:jointed=1;break;case 7:can=0;break;case 8:icon=13;break;case 9:raw=(void*)5;break;case 10:meshgap=.04f;break;case 11:outside=1;pointgap=.08f;break;case 12:ownerKind=2;break;}
 s26dr_scan_small_lever(&s,(void*)1,wrapper,(void*)8,mass);C((s26dr_small_lever_choice(&s)==1)==(fault<2));C(calls<=6);
 if(fault<2){C(s.drBody==(void*)1);C(s.drOwner==(void*)4);raw=(void*)2;meshgap=.007f;s26dr_scan_small_lever(&s,(void*)2,wrapper,(void*)8,0);C(s26dr_small_lever_choice(&s)==-1);}
}
C(s26dr_small_lever_choice(0)==0);printf("PASS %d non-colliding switch interior/exterior, eligibility, separation, ambiguity and bounded-query checks\n",checks);return 0;}
'''
B=R/'build';p=B/'small_lever_test.c';p.write_text(head+fn+main);e=p.with_suffix('.exe');subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(e)],check=True);subprocess.run([str(e)],check=True)
assert 's26dr_small_lever_choice(&ready)==1' in s and 's26dr_small_lever_choice(&authScan)' in s
assert 'poseSamples[h]<3u' in s and 'poseNextStep[h]=g_h14PhysicsSteps+120u' in s
print('PASS shared selector wiring and capped human pose capture. No engine/headset simulation.')
assert 'h,authScan.drBody,authScan.drHandM,authScan.drContact,0.0f,0' in s
