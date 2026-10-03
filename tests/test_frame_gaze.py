"""Execute production tracking includes against a fault-injected OpenXR runtime.
These are contract tests, not a substitute for Steam Frame hardware testing.
"""
from pathlib import Path
import subprocess,sys,re
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=(R/'source/s26n.c').read_text()
types=s[s.index('typedef unsigned char'):s.index('#define XR_SUCCESS')]
defines='\n'.join(x for x in s.splitlines() if x.startswith('#define XR_'))
header=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static int checks,logs;
static void zero_bytes(void*p,u64 n){memset(p,0,n);}
static void ext_Log(const char*f,...){(void)f;++logs;}
static XrPath g_s26nProfiles[6]={10,11,12,13,14,15},g_handPath[2]={20,21};
static u8 g_s26dgFrameExtension=1,g_s26sEyeExtension=1;
static XrPath currentProfile=15;static int profileError;
static i32 mock_profile(Handle h,XrPath p,XrInteractionProfileState*s){s->interactionProfile=currentProfile;return profileError;}
static i32(*pGetCurrentInteractionProfile)(Handle,XrPath,XrInteractionProfileState*)=mock_profile;
static int optionalReject;
static int suggestError,spaceError,refError,actionError,attached,suggestCount;
static XrActionSuggestedBinding saved[51];
static i32 pStringToPath(Handle i,const char*s,XrPath*p){*p=strstr(s,"frame_controller")?15:strstr(s,"dpad_up")?31:strstr(s,"dpad_left")?32:40;return 0;}
static i32 pSuggestBindings(Handle i,const XrInteractionProfileSuggestedBinding*s){suggestCount=s->countSuggestedBindings;memcpy(saved,s->suggestedBindings,sizeof(*saved)*suggestCount);return optionalReject&&suggestCount>23?-1:suggestError;}
static Handle g_h5724FaceActionSet=(Handle)88,g_s26ebExtraAction[8];
static u8 g_s26ebExtraBound,g_s26ebExtraRaw[8],g_s26ebExtraActive[8];
static u64 nextAction=100;static i32 create_action(const char*n,const char*l,i32 t,Handle*p){*p=actionError?0:(Handle)(++nextAction);return actionError;}
static i32 create_action_in_set(Handle set,const char*n,const char*l,i32 t,Handle*p){return create_action(n,l,t,p);}
static Handle g_s26dlRestTouchAction[2][3],g_squeezeAction[2]={(Handle)10,(Handle)11},g_triggerAction[2]={(Handle)12,(Handle)13};
static u32 g_s26dlRestBindings,g_s26dlReleased[2],g_s26dlTouchKnown[2],g_s26dlTouched[2],g_s26dmReleasedMask[2];
static int groupBits;static int touchErr,touchActive=1,touchValue,floatErr,floatActive=1;static float gripValue,triggerValue;
static i32 mock_bool(Handle h,const XrActionStateGetInfo*i,XrActionStateBoolean*s){s->isActive=touchActive;s->currentState=touchValue;for(int h=0;h<2;h++)for(int g=0;g<3;g++)if(i->action==g_s26dlRestTouchAction[h][g])s->currentState=touchValue||((groupBits>>g)&1);return touchErr;}
static i32 mock_float(Handle h,const XrActionStateGetInfo*i,XrActionStateFloat*s){s->isActive=floatActive;s->currentState=(i->action==(Handle)10||i->action==(Handle)11)?gripValue:triggerValue;return floatErr;}
static i32 (*pGetActionStateBoolean)(Handle,const XrActionStateGetInfo*,XrActionStateBoolean*)=mock_bool;
static i32 (*pGetActionStateFloat)(Handle,const XrActionStateGetInfo*,XrActionStateFloat*)=mock_float;
static void s26q_hook_destroy(void*s){(void)s;}
static i32 pCreateActionSpace(Handle h,const XrActionSpaceCreateInfo*c,Handle*out){if(!attached)return -46;*out=spaceError?0:(Handle)2;return spaceError;}
typedef i32 (__attribute__((ms_abi)) *PFN_GIPA)(Handle,const char*,void**);
static i32 __attribute__((ms_abi)) mock_ref(Handle h,const void*c,Handle*out){*out=refError?0:(Handle)3;return refError;}
static i32 __attribute__((ms_abi)) get(Handle h,const char*n,void**p){if(strcmp(n,"xrCreateReferenceSpace"))return -7;*p=(void*)mock_ref;return 0;}
static int active=1,stateError,locError,headError,flags=15,badPose;static i64 sampleTime,headTime;
static i32 pGetActionStatePose(Handle h,const XrActionStateGetInfo*i,XrActionStatePose*s){s->isActive=active;return stateError;}
static i32 pLocateSpace(Handle s,Handle base,i64 t,XrSpaceLocation*l){
 l->locationFlags=s==(Handle)2?flags:3;l->pose.orientation.w=badPose?NAN:1;l->pose.position.y=1.6f;
 if(s==(Handle)2&&l->next)*(i64*)((char*)l->next+16)=sampleTime;
 if(s==(Handle)3){headTime=t;return headError;}return locError;
}
'''
main=r'''
int main(void){
 Handle session=(Handle)99;char self[512]={0};*(PFN_GIPA*)(self+0x1c8)=get;
 CHECK(s26u_controller_fingers_allowed(session,0));currentProfile=11;CHECK(s26u_controller_fingers_allowed(session,1));
 currentProfile=10;CHECK(s26u_controller_fingers_allowed(session,0));currentProfile=99;CHECK(s26u_controller_fingers_allowed(session,0));
 currentProfile=15;g_s26dgFrameExtension=0;CHECK(s26u_controller_fingers_allowed(session,0));g_s26dgFrameExtension=1;
 profileError=-1;CHECK(!s26u_controller_fingers_allowed(session,0));profileError=0;CHECK(!s26u_controller_fingers_allowed(session,-1));
 for(int repeat=0;repeat<5;repeat++){
  for(int profile=0;profile<6;profile++){
   currentProfile=g_s26nProfiles[profile];s26dj_set_finger_tracking(0);
   CHECK(!s26u_controller_fingers_allowed(session,0));CHECK(!s26u_controller_fingers_allowed(session,1));CHECK(!g_s26diFrameHand[0]&&!g_s26diFrameHand[1]);
   s26dj_set_finger_tracking(1);CHECK(s26u_controller_fingers_allowed(session,0)==1);
  }
 }
 currentProfile=15;
 XrActionSuggestedBinding binds[23];for(int i=0;i<23;i++){binds[i].action=(Handle)(u64)(i+1);binds[i].binding=100+i;}
 s26dg_frame_binding((Handle)1,binds,23);CHECK(g_s26nProfiles[5]==15&&suggestCount==51&&g_s26ebExtraBound&&g_s26dlRestBindings);
 for(int i=0;i<23;i++){CHECK(saved[i].action==binds[i].action);CHECK(saved[i].binding==(i==18?31:i==20?32:binds[i].binding));}
 for(int i=0;i<8;i++)CHECK(saved[23+i].action==g_s26ebExtraAction[i]);
 touchValue=1;s26eb_extra_tick(session,1);for(int i=0;i<8;i++)CHECK(g_s26ebExtraRaw[i]&&g_s26ebExtraActive[i]);
 s26eb_extra_tick(session,0);for(int i=0;i<8;i++)CHECK(!g_s26ebExtraRaw[i]&&!g_s26ebExtraActive[i]);
 touchValue=0;
 optionalReject=1;s26dg_frame_binding((Handle)1,binds,23);CHECK(g_s26nProfiles[5]==15&&suggestCount==23&&!g_s26dlRestBindings);optionalReject=0;
 s26dg_frame_binding((Handle)1,binds,23);CHECK(g_s26dlRestBindings);
 for(int contact=0;contact<2;contact++)for(int known=0;known<2;known++)for(int pressed=0;pressed<2;pressed++){
  touchValue=contact;touchActive=known;gripValue=pressed;
  s26dl_rest_tick(session,1);CHECK(g_s26dlReleased[0]==(known&&!contact&&!pressed));CHECK(g_s26dlReleased[1]==g_s26dlReleased[0]);
 }
 touchValue=0;touchActive=1;gripValue=triggerValue=0;s26dl_rest_tick(session,1);CHECK(g_s26dlReleased[0]);
 s26dl_rest_tick(session,0);CHECK(!g_s26dlReleased[0]);
 touchErr=-1;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]);touchErr=0;
 floatErr=-1;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]);floatErr=0;
 floatActive=0;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]);floatActive=1;
 triggerValue=.5;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]);triggerValue=0;
 gripValue=NAN;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]);gripValue=0;
 // Joystick-only/thumb, index-only, grip-only and combinations; both hands.
 for(int bits=0;bits<8;bits++)for(int press=0;press<4;press++){
  groupBits=bits;gripValue=(press&1)?1:0;triggerValue=(press&2)?1:0;
  s26dl_rest_tick(session,1);unsigned want=0;
  if(!(bits&1))want|=1;if(!(bits&2)&&!(press&2))want|=2;if(!(bits&4)&&!(press&1))want|=28;
  CHECK(g_s26dmReleasedMask[0]==want);CHECK(g_s26dmReleasedMask[1]==want);
 }
 groupBits=1;gripValue=triggerValue=0;s26dl_rest_tick(session,1);
 CHECK(g_s26dmReleasedMask[0]==30); // Thumb on stick cannot curl four other fingers.
 for(int h=0;h<2;h++)for(int k=0;k<10;k++)CHECK(saved[31+h*10+k].action==g_s26dlRestTouchAction[h][k==0?2:k<=2?1:0]);
 groupBits=0;
 suggestError=-1;s26dg_frame_binding((Handle)1,binds,23);CHECK(!g_s26nProfiles[5]&&suggestCount==21);suggestError=0;
 g_s26sEyeExtension=0;s26s_eye_binding(self,(Handle)1,session);CHECK(!g_s26sEyeAction);g_s26sEyeExtension=1;
 actionError=-1;s26s_eye_binding(self,(Handle)1,session);CHECK(!g_s26sEyeAction);actionError=0;
 s26s_eye_binding(self,(Handle)1,session);CHECK(g_s26sEyeAction&&!g_s26sEyeSpace);
 attached=1;s26s_eye_spaces(self,(Handle)1,session);CHECK(g_s26sEyeSpace&&g_s26dgEyeView);
 i64 now=1000000000;sampleTime=now-20000000;s26s_eye_tick(session,(Handle)4,now,0);
 CHECK(g_s26sEyeSample.valid&&g_s26sEyeSample.headValid);CHECK(headTime==sampleTime&&g_s26sEyeSample.time==sampleTime);
 active=0;s26s_eye_tick(session,(Handle)4,now,0);CHECK(!g_s26sEyeSample.valid&&g_s26sEyeReported==2);active=1;
 flags=3;s26s_eye_tick(session,(Handle)4,now,0);CHECK(!g_s26sEyeSample.valid&&g_s26sEyeReported==3);flags=15;
 sampleTime=now-100000001;s26s_eye_tick(session,(Handle)4,now,0);CHECK(!g_s26sEyeSample.valid&&g_s26sEyeReported==4);
 sampleTime=0;s26s_eye_tick(session,(Handle)4,now,0);CHECK(g_s26sEyeSample.valid&&headTime==now);
 badPose=1;s26s_eye_tick(session,(Handle)4,now,0);CHECK(!g_s26sEyeSample.valid);badPose=0;
 headError=-1;s26s_eye_tick(session,(Handle)4,now,0);CHECK(!g_s26sEyeSample.valid&&g_s26sEyeReported==5);headError=0;
 s26s_eye_tick(session,(Handle)4,now,1);CHECK(!g_s26sEyeSample.valid);
 s26s_eye_tick(session,(Handle)4,now,0);CHECK(g_s26sEyeSample.valid);
 s26s_eye_end((Handle)98);CHECK(g_s26sEyeSpace);s26s_eye_end(session);CHECK(!g_s26sEyeSpace&&!g_s26dgEyeView&&!g_s26sEyeSample.valid);
 s26s_eye_binding(self,(Handle)1,session);spaceError=-1;s26s_eye_spaces(self,(Handle)1,session);CHECK(!g_s26sEyeSpace);spaceError=0;
 refError=-1;s26s_eye_spaces(self,(Handle)1,session);CHECK(!g_s26dgEyeView);refError=0;
 printf("PASS: %d production Frame/gaze contract checks\n",checks);return 0;
}
'''
c=B/'frame_gaze_test.c';c.write_text(types+'\n'+defines+'\n'+header+'\n'+ '\n'.join((R/'source'/x).read_text() for x in ['controller_policy_u.inc','frame_dg.inc','eyes_s.inc'])+main)
exe=B/'frame_gaze_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-I',str(R/'source'),str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
