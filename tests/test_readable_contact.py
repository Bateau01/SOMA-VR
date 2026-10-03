"""Execute the production readable selector with controlled native contracts.
No Newton/AngelScript simulation; hardware pickup still needs confirmation.
"""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('static i32 s26da_queue_contact_item(');b=s.index('// S26DB:',a);fn=s[a:b]
post=s[s.index('static i32 h5755hj_queue_current_zero_mass_contact('):s.index('#include "texture_streaming_i.inc"')]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;
#define H5755HJ_STATIC_CONTACT_MAX 4
#define H481_MECH_NONE 0
static void* g_h14GripBody[2];static int g_h30NativeMouseDown;
static unsigned g_h14PhysicsSteps=100,g_h5755hjStaticContactStep[2],g_h5755hjStaticContactCount[2];
static const void* g_h5755hjStaticContactBody[2][4];static int g_h5755hjStaticContactPointValid[2][4];static float g_h5755hjStaticContactPoint[2][4][3];
static const void* g_s26dpReadableContactBody,*g_s26daItemClaim[2];static unsigned g_s26daItemClaimStep[2];
static int icon,can,jointed,kind,meshOK,queueOK,calls,scopeSeen,checks;static float distance;static const void* wrongRaw;
static void* fakeOwner;
static void* h482_body_owner(const void*b,void**w){if(w)*w=(void*)b;return fakeOwner?fakeOwner:(void*)b;}
static int h576ad_target_can_interact(void*w,void*o,const void**r,int*i){*r=wrongRaw?wrongRaw:w;*i=icon;return can;}
static const void* h568_first_external_joint(const void*b){return jointed?(void*)1:0;}
static int h553_body_semantic_mechanism(const void*b,void*o){return kind;}
static void h14_rigid_inverse(const float*m,float*i){}
static void h14_transform_point(const float*m,const float*p,float*out){}
static int h20_nearest_hand_mesh_local(int h,const float*p,float*m,int*t,float*b,float*g){*g=distance;return meshOK;}
static int h25_queue_native_interact(int h,const void*b,const float*m,const float*c,float g,int j){calls++;scopeSeen=g_s26dpReadableContactBody==b;return queueOK&&(distance<=.012f||scopeSeen);}
static void ext_Log(const char*f,...){(void)f;}
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
head+=r'''
typedef unsigned char u8;
#define H482_POKE_SWITCH_ICON 13
#define H483_CURTAIN_ICON 12
static unsigned g_h5755hjStaticSemanticAmbiguous[2],g_h5755hkControlDefers[2],g_h5755hjStaticSemanticAttempts[2],g_h5755hlBlockStep[2],g_h5755hmBlockEdgeStep[2],g_h5755haGripEdgeStep[2],g_h5755hjStaticSemanticQueueRejects[2],g_h5755hjStaticSemanticQueued[2];
static const void *g_h5755hlBlockBody[2];static void *g_h5755hlBlockOwner[2];static int g_h5755hlBlockRayValid[2];static float g_h5755hlBlockRayDir[2][3],g_h5755hlBlockRayStart[2][3];
typedef int (*PFN_H25_GetInteractIconId)(void*,int,void*);
static int h5755hj_classify_contact_cLuxProp(const void*b,float*m){*m=0;return 1;}
static int h20_mem_readable(void*p,int n){return 1;}
static int h25_soma_code_ptr(void*p){return 1;}
static int h15_grip_center_world(int h,const float*m,float*p){return 0;}
static float h10_len3(float a,float b,float c){return 0;}
static int geticon(void*a,int b,void*c){return icon;}
'''
main=r'''
int main(void){float m[16]={0};
for(int h=0;h<2;h++)for(int fault=0;fault<17;fault++){
 memset(g_h14GripBody,0,sizeof(g_h14GripBody));g_h14GripBody[1-h]=(void*)99;
 memset(g_h5755hjStaticContactBody,0,sizeof(g_h5755hjStaticContactBody));memset(g_s26daItemClaim,0,sizeof(g_s26daItemClaim));
 g_h5755hjStaticContactStep[h]=100;g_h5755hjStaticContactCount[h]=1;g_h5755hjStaticContactBody[h][0]=(void*)1;g_h5755hjStaticContactPointValid[h][0]=1;
 icon=22;can=meshOK=queueOK=1;kind=jointed=calls=scopeSeen=g_h30NativeMouseDown=0;distance=.036f;wrongRaw=0;
 switch(fault){case 1:distance=.006f;break;case 2:g_h5755hjStaticContactStep[h]=99;break;case 3:g_h5755hjStaticContactStep[h]=98;break;case 4:can=0;break;
 case 5:icon=13;break;case 6:icon=2;break;case 7:icon=14;break;case 8:jointed=1;break;case 9:kind=1;break;case 10:wrongRaw=(void*)3;break;
 case 11:g_h5755hjStaticContactPointValid[h][0]=0;break;case 12:meshOK=0;break;case 13:queueOK=0;break;case 14:g_h30NativeMouseDown=1;break;
 case 15:g_h5755hjStaticContactCount[h]=2;g_h5755hjStaticContactBody[h][1]=(void*)2;g_h5755hjStaticContactPointValid[h][1]=1;break;
 case 16:g_h5755hjStaticContactStep[h]=99;distance=.006f;break;}
 int r=s26da_queue_contact_item(h,m);C((r==1)==(fault==0||fault==1||fault==2||fault==16));C(g_s26dpReadableContactBody==0);C(g_h14GripBody[1-h]==(void*)99);
 if(r==1){C(calls==1);C(g_s26daItemClaim[h]==(void*)1);C(scopeSeen==1);}else C(!g_s26daItemClaim[h]);
}

// Actual production phase order: contacts publish at N; fresh grip begins N+1.
// No new squeeze is required; the queued transaction belongs to N+1.
for(int h=0;h<2;h++){
 memset(g_h14GripBody,0,sizeof(g_h14GripBody));g_h30NativeMouseDown=0;
 g_h14PhysicsSteps=200;g_h5755hjStaticContactStep[h]=200;g_h5755hjStaticContactCount[h]=1;
 g_h5755hjStaticContactBody[h][0]=(void*)1;g_h5755hjStaticContactPointValid[h][0]=1;
 icon=22;can=meshOK=queueOK=1;kind=jointed=0;distance=.036f;wrongRaw=0;
 ++g_h14PhysicsSteps;g_h5755haGripEdgeStep[h]=g_h14PhysicsSteps;
 C(s26da_queue_contact_item(h,m)==1);C(g_s26daItemClaimStep[h]==201);
 // First contact can also appear in THIS solver after pre-solver selection.
 g_h5755hjStaticContactCount[h]=0;C(s26da_queue_contact_item(h,m)==0);
 g_h5755hjStaticContactCount[h]=1;g_h5755hjStaticContactStep[h]=201;
 void* vt[15]={0};vt[13]=(void*)geticon;void** obj=vt;fakeOwner=&obj;
 C(h5755hj_queue_current_zero_mass_contact(h,m)==1);C(scopeSeen);C(!g_s26dpReadableContactBody);
 can=0;C(h5755hj_queue_current_zero_mass_contact(h,m)==0);C(!g_s26dpReadableContactBody);
 can=1;wrongRaw=(void*)3;C(h5755hj_queue_current_zero_mass_contact(h,m)==0);
 wrongRaw=0;icon=13;C(h5755hj_queue_current_zero_mass_contact(h,m)==0);
 icon=22;g_h5755hjStaticContactStep[h]=200;C(h5755hj_queue_current_zero_mass_contact(h,m)==0);
 fakeOwner=0;
}
C(!s26da_queue_contact_item(-1,m));C(!s26da_queue_contact_item(0,0));printf("PASS %d readable contact selection / expiry / ambiguity / other-hand checks\n",checks);return 0;}
'''
B=R/'build';c=B/'readable_contact_test.c';c.write_text(head+fn+post+main);exe=c.with_suffix('.exe');subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
# Ensure the tested scope is consumed by the production generic queue.
a=s.index('static i32 h25_queue_native_interact(');b=s.index('static void h5755em_queue_native_grab_semantics_ex',a)
assert 'meshGap>gate&&body!=g_s26dpReadableContactBody' in s[a:b]
assert 'g_h25AttemptBody[hand]==body' in s[a:b]
assert 'g_s26dpReadableContactBody=exactRead?chosen:0;' in s[s.index('static i32 h5755hj_queue_current_zero_mass_contact('):s.index('#include "texture_streaming_i.inc"')]
print('PASS production queue retains per-squeeze deduplication and scoped contact gate')
