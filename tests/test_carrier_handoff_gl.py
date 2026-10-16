from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8');B=R/'build';B.mkdir(exist_ok=True)
a=s.index('static void h576av_update_theta_handoff(');b=s.index('/* BJ:',a);fn=s[a:b]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;
typedef struct {int stowed;const void*raw;void*owner;char logical[96];} H576AAInvItem;
static H576AAInvItem item;static int haveItem=1,poseOK=1,pointOK=1,latchOK=1,ownerOK=1,rate=1,releases,checks;
static float gap,mass=1;
static int g_h576avThetaPendingHand,g_lastSqueezeActive[2],g_h552ContactLatchBypass[2];
static float g_lastSqueeze[2];static const void*g_h14GripBody[2],*g_s26gkThetaSourceBody;
static char g_h576avThetaPendingLogical[96];
static u32 g_h14PhysicsSteps,g_h576avThetaPendingLastStep,g_h576avThetaPendingStartStep,g_h576avThetaTimeouts,g_h576avThetaLatches,g_h576avThetaDistanceWaits,g_h14GrabCount[2];
static void ext_Log(const char*f,...){ }
static u32 s26gd_steps(u32 n){return n*rate;}
static void h576av_theta_clear_pending(const char*s){g_h576avThetaPendingHand=-1;g_s26gkThetaSourceBody=0;}
static H576AAInvItem*h576aa_inv_find_logical(const char*s){return haveItem?&item:0;}
static int h14_hand_pose_raw(int h,float*p,float*m){return poseOK;}
static int h15_grip_center_world(int h,const float*m,float*p){return poseOK;}
static int s26eq_return_point(const void*b,const float*p,float*d,float*c){*d=gap;return pointOK;}
static float h5755ea_world_units_per_meter(void){return 1;}
static void getmass(const void*b,float*m,float*x,float*y,float*z){*m=mass;}
static void(*p_h14GetMass)(const void*,float*,float*,float*,float*)=getmass;
static void h14_release(int h,const char*s){releases++;g_h14GripBody[h]=0;}
static void*h482_body_owner(const void*b,void**w){return ownerOK?item.owner:0;}
static void h14_latch(int h,const void*b,float g,float m,const float*hm,const float*gc,float r,const float*cp,int a,int j,const void*k){if(latchOK){g_h14GripBody[h]=b;g_h14GrabCount[h]++;}}
static void reset(void){
 item=(H576AAInvItem){0,(void*)2,(void*)22,"chip"};g_h576avThetaPendingHand=0;g_h14PhysicsSteps=101;g_h576avThetaPendingLastStep=g_h576avThetaPendingStartStep=100;
 g_lastSqueezeActive[0]=1;g_lastSqueeze[0]=1;g_h14GripBody[0]=(void*)1;g_h14GripBody[1]=0;g_s26gkThetaSourceBody=(void*)1;g_h14GrabCount[0]=0;
 haveItem=poseOK=pointOK=latchOK=ownerOK=1;gap=.04f;mass=1;releases=0;
}
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){for(rate=1;rate<=2;rate++){
 reset();h576av_update_theta_handoff();C(releases==1&&g_h14GripBody[0]==(void*)2&&g_h576avThetaPendingHand==-1);C(g_h14GrabCount[0]==1&&!g_h552ContactLatchBypass[0]);h576av_update_theta_handoff();C(releases==1&&g_h14GrabCount[0]==1);
 reset();g_h14GripBody[0]=(void*)3;h576av_update_theta_handoff();C(!releases&&g_h14GripBody[0]==(void*)3&&g_h576avThetaPendingHand==-1);
 reset();g_h14GripBody[1]=(void*)2;h576av_update_theta_handoff();C(!releases&&g_h14GripBody[0]==(void*)1);
 reset();g_lastSqueeze[0]=0;h576av_update_theta_handoff();C(!releases&&g_h576avThetaPendingHand==-1);
 reset();gap=.101f;h576av_update_theta_handoff();C(!releases&&g_h576avThetaPendingHand==0);
 reset();mass=0;h576av_update_theta_handoff();C(!releases);
 reset();haveItem=0;h576av_update_theta_handoff();C(!releases);
 reset();item.stowed=1;h576av_update_theta_handoff();C(!releases);
 reset();ownerOK=0;h576av_update_theta_handoff();C(releases==1&&!g_h14GrabCount[0]);
 reset();g_h14PhysicsSteps=100+12*rate+1;h576av_update_theta_handoff();C(!releases&&g_h576avThetaPendingHand==-1);
 reset();g_h14GripBody[0]=0;g_s26gkThetaSourceBody=0;h576av_update_theta_handoff();C(!releases&&g_h14GripBody[0]==(void*)2);
 }printf("PASS %d carrier handoff checks at 60/120 Hz\n",checks);return 0;}
'''
c=B/'carrier_handoff_gl.c';c.write_text(head+fn+main);exe=c.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
