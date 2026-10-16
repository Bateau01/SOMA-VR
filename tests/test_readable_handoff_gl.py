"""Execute the production same-grip readable handoff with fault injection."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8');B=R/'build';B.mkdir(exist_ok=True)
fn=s[s.index('static i32 s26ce_latch_readable('):s.index('static i32 s26ck_latch_tablet(')]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;
typedef struct {const void* newtonBody;void* bodyWrapper;void* entity;int jointed;u32 physicsStep;float contact[3];} H25PendingInteract;
static const void *g_h14GripBody[2],*g_s26glReadSource,*g_s26glReadBody,*g_s26bvReadableWrapper,*g_s26fkIndependentReadable,*g_h5755chGrabStateBody;
static int g_s26glReadHand,g_lastSqueezeActive[2],g_h30NativeMouseDown,g_h30NativeUseHand,g_h5755gwPreserveExistingGrabUse[2],g_h552ContactLatchBypass[2];
static u32 g_s26glReadStep,g_h14PhysicsSteps,g_s26bvReadableStep,g_h5755haGripEdgeStep[2],g_h5755cjGrabExpectedStep;
static float g_lastSqueeze[2];static void *g_h39NativeUseProp[2],*g_h5755chGrabStateWrapper,*g_h5755chGrabStateOwner;
static int g_h5755chGrabExpected,g_h5755chGrabStateActive,g_h5755chGrabPrimaryHand;
static struct {int valid;} g_h5755chGrabPending[2];
static int jointed,poseOK=1,pointOK=1,latchOK=1,beginCalls,latchCalls,checks;static float gap,mass=1;
static float h5755ea_world_units_per_meter(void){return 1;}
static void* h482_body_owner(const void*b,void**w){if(w)*w=(void*)b;return (void*)b;}
static const void* h568_first_external_joint(const void*b){return jointed?(void*)99:0;}
static int h14_hand_pose(int h,float*p,float*m){memset(p,0,12);memset(m,0,64);return poseOK;}
static int h15_grip_center_world(int h,const float*m,float*p){memset(p,0,12);return poseOK;}
static int s26eq_return_point(const void*b,const float*p,float*d,float*c){*d=gap;memset(c,0,12);return pointOK;}
static void getmass(const void*b,float*m,float*x,float*y,float*z){*m=mass;}
static void (*p_h14GetMass)(const void*,float*,float*,float*,float*)=getmass;
static void h30_native_use_begin(int h,void*w,int j,void*o){beginCalls++;g_s26bvReadableWrapper=0;}
static void h14_latch(int h,const void*b,float d,float m,const float*hm,const float*gc,float r,const float*cp,int i,int j,const void*k){latchCalls++;if(latchOK)g_h14GripBody[h]=b;}
static int h5755cj_reassert_native_grab_state(int h){g_h5755chGrabStateActive=1;return 1;}
static void h5729_state_boundary_observe(const char*s){}
static int h5755gw_adopt_existing_same_owner_grab(int h,void*o){return 1;}
static void h5755ch_verify_grab_script(void){}
static void ext_Log(const char*s,...){ }
static H25PendingInteract p;
static void reset(void){
 memset(g_h14GripBody,0,sizeof(g_h14GripBody));g_h14PhysicsSteps=g_s26glReadStep=g_s26bvReadableStep=100;
 g_h5755haGripEdgeStep[0]=100;g_lastSqueeze[0]=1;g_lastSqueezeActive[0]=1;
 g_s26glReadHand=0;g_s26glReadSource=(void*)1;g_s26glReadBody=(void*)2;g_s26bvReadableWrapper=(void*)2;
 p=(H25PendingInteract){(void*)1,(void*)1,(void*)1,0,100,{0}};
 g_s26fkIndependentReadable=0;g_h30NativeMouseDown=0;jointed=0;poseOK=pointOK=latchOK=1;gap=0.04f;mass=1;beginCalls=latchCalls=0;
}
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 reset();C(s26ce_latch_readable(0,&p,(void*)1,(void*)1));C(g_h14GripBody[0]==(void*)2&&beginCalls==1&&latchCalls==1);
 reset();g_s26fkIndependentReadable=(void*)2;g_h14GripBody[1]=(void*)3;g_h30NativeMouseDown=1;g_h30NativeUseHand=1;
 C(s26ce_latch_readable(0,&p,(void*)1,(void*)1));C(g_h14GripBody[1]==(void*)3&&beginCalls==0);
 reset();p.newtonBody=p.bodyWrapper=p.entity=(void*)2;C(s26ce_latch_readable(0,&p,(void*)2,(void*)2));
 reset();g_s26glReadStep--;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();g_s26glReadHand=1;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();g_s26glReadSource=(void*)9;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();g_s26bvReadableWrapper=(void*)9;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();gap=.101f;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));C(!latchCalls);
 reset();g_lastSqueeze[0]=0;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();g_h5755haGripEdgeStep[0]--;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();g_h14GripBody[0]=(void*)3;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));C(g_h14GripBody[0]==(void*)3);
 reset();jointed=1;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();mass=0;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();poseOK=0;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();pointOK=0;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));
 reset();latchOK=0;C(!s26ce_latch_readable(0,&p,(void*)1,(void*)1));C(!g_h552ContactLatchBypass[0]);
 printf("PASS: %d readable handoff checks\n",checks);return 0;
}
'''
c=B/'readable_handoff_gl.c';c.write_text(head+fn+main);exe=c.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
