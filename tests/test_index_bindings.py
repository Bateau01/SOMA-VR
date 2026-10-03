"""Execute the production Valve Index binding, shared-action and controller-policy
code against a fault-injecting OpenXR mock. Contract tests only; they do not
replace a headset test with Index controllers.
"""
from pathlib import Path
import subprocess,sys
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
static int checks;
static void zero_bytes(void*p,u64 n){memset(p,0,n);}
static void ext_Log(const char*f,...){(void)f;}
static XrPath g_s26nProfiles[6]={10,11,12,13,14,15},g_handPath[2]={20,21};
static u8 g_s26dgFrameExtension=1;
static XrPath currentProfile=11;
static i32 mock_profile(Handle h,XrPath p,XrInteractionProfileState*s){(void)h;(void)p;s->interactionProfile=currentProfile;return 0;}
static i32(*pGetCurrentInteractionProfile)(Handle,XrPath,XrInteractionProfileState*)=mock_profile;
/* Every path string gets a stable id so bindings can be checked by name. */
static char pathNames[256][96];static int pathCount;static const char* rejectPath;
static i32 pStringToPath(Handle i,const char*s,XrPath*p){(void)i;
 if(rejectPath&&!strcmp(s,rejectPath))return -5;
 for(int k=0;k<pathCount;k++)if(!strcmp(pathNames[k],s)){*p=1000+k;return 0;}
 strcpy(pathNames[pathCount],s);*p=1000+pathCount++;return 0;}
static const char* pathName(XrPath p){return p>=1000&&p<1000u+pathCount?pathNames[p-1000]:"?";}
/* Mock runtime: optionally rejects any suggestion containing a given path
   suffix, as a runtime that lacks support for that input would. */
static const char* rejectSuffix[4];static int suggestCalls,lastCount;static XrPath lastProfile;
static XrActionSuggestedBinding saved[64];
static int endsWith(const char*a,const char*b){size_t x=strlen(a),y=strlen(b);return x>=y&&!strcmp(a+x-y,b);}
static i32 pSuggestBindings(Handle i,const XrInteractionProfileSuggestedBinding*sb){(void)i;
 ++suggestCalls;lastCount=sb->countSuggestedBindings;lastProfile=sb->interactionProfile;
 memcpy(saved,sb->suggestedBindings,sizeof(*saved)*lastCount);
 for(int k=0;k<lastCount;k++){if(!sb->suggestedBindings[k].action)return -99;
  for(int r=0;r<4;r++)if(rejectSuffix[r]&&endsWith(pathName(sb->suggestedBindings[k].binding),rejectSuffix[r]))return -6;}
 return 0;}
static Handle g_h5724FaceActionSet=(Handle)88,g_s26ebExtraAction[8];
static u8 g_s26ebExtraBound,g_s26ebExtraRaw[8],g_s26ebExtraActive[8];
static u64 nextAction=100;static int actionError,actionCreates;static char actionNames[64][64];
static i32 create_action_in_set(Handle set,const char*n,const char*l,i32 t,Handle*p){(void)set;(void)l;(void)t;
 if(actionError){*p=0;return actionError;}
 for(int k=0;k<actionCreates;k++)if(!strcmp(actionNames[k],n))return -48; /* XR_ERROR_NAME_DUPLICATED */
 strcpy(actionNames[actionCreates++],n);*p=(Handle)(++nextAction);return 0;}
static i32 create_action(const char*n,const char*l,i32 t,Handle*p){return create_action_in_set((Handle)77,n,l,t,p);}
static Handle g_s26ecForceAction[2],g_s26ecFaceTouchAction[2][2];
static Handle g_s26dlRestTouchAction[2][3],g_squeezeAction[2]={(Handle)10,(Handle)11},g_triggerAction[2]={(Handle)12,(Handle)13};
static u32 g_s26dlRestBindings,g_s26dlReleased[2],g_s26dlTouchKnown[2],g_s26dlTouched[2],g_s26dmReleasedMask[2];
static int touchBits[2],touchActive=1;static float gripValue,triggerValue;
static i32 mock_bool(Handle h,const XrActionStateGetInfo*i,XrActionStateBoolean*s){(void)h;s->isActive=touchActive;s->currentState=0;
 for(int hh=0;hh<2;hh++){for(int g=0;g<3;g++)if(i->action==g_s26dlRestTouchAction[hh][g])s->currentState=(touchBits[hh]>>g)&1;
  for(int k=0;k<8;k++)if(i->action==g_s26ebExtraAction[k])s->currentState=1;for(int b=0;b<2;b++)if(i->action==g_s26ecFaceTouchAction[hh][b])s->currentState=1;}return 0;}
static i32 mock_float(Handle h,const XrActionStateGetInfo*i,XrActionStateFloat*s){(void)h;s->isActive=1;s->currentState=(i->action==(Handle)10||i->action==(Handle)11||i->action==g_s26ecForceAction[0]||i->action==g_s26ecForceAction[1])?gripValue:triggerValue;return 0;}
static i32 (*pGetActionStateBoolean)(Handle,const XrActionStateGetInfo*,XrActionStateBoolean*)=mock_bool;
static i32 (*pGetActionStateFloat)(Handle,const XrActionStateGetInfo*,XrActionStateFloat*)=mock_float;
static void reset_runtime(void){
 memset(g_s26ebExtraAction,0,sizeof(g_s26ebExtraAction));memset(g_s26dlRestTouchAction,0,sizeof(g_s26dlRestTouchAction));
 memset(g_s26ecForceAction,0,sizeof(g_s26ecForceAction));memset(g_s26ecFaceTouchAction,0,sizeof(g_s26ecFaceTouchAction));actionCreates=0;g_s26dlRestBindings=0;g_s26ebExtraBound=0;for(int r=0;r<4;r++)rejectSuffix[r]=0;rejectPath=0;actionError=0;}
static int count_suffix(const char*suffix){int n=0;for(int k=0;k<lastCount;k++)if(endsWith(pathName(saved[k].binding),suffix))n++;return n;}
static Handle action_for(const char*path){for(int k=0;k<lastCount;k++)if(!strcmp(pathName(saved[k].binding),path))return saved[k].action;return 0;}
'''
main=r'''
int main(void){
 Handle session=(Handle)99;
 XrActionSuggestedBinding base[23];for(int i=0;i<23;i++){base[i].action=(Handle)(u64)(i+1);base[i].binding=500+i;}
 XrPath index=11;
 /* Full Index suggestion: 23 established + 2 trackpad presses + 12 contact surfaces. */
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 CHECK(lastProfile==index&&lastCount==43&&g_s26dlRestBindings==2u&&g_s26ebExtraBound==2u&&g_s26ecLayers==7u);
 for(int i=0;i<23;i++)CHECK(saved[i].action==base[i].action&&saved[i].binding==base[i].binding);
 CHECK(action_for("/user/hand/left/input/trackpad/force")==g_s26ebExtraAction[0]&&g_s26ebExtraAction[0]);
 CHECK(action_for("/user/hand/right/input/trackpad/force")==g_s26ebExtraAction[1]&&g_s26ebExtraAction[1]);
 CHECK(!count_suffix("/trackpad/click")&&!count_suffix("/squeeze/touch")&&!count_suffix("/system/touch")&&!count_suffix("/system/click"));
 const char* hands[2]={"/user/hand/left/input/","/user/hand/right/input/"};
 const char* thumb[4]={"thumbstick/touch","trackpad/touch","a/touch","b/touch"};
 for(int h=0;h<2;h++){char p[96];
  for(int k=0;k<4;k++){snprintf(p,96,"%s%s",hands[h],thumb[k]);CHECK(action_for(p)==g_s26dlRestTouchAction[h][0]);}
  snprintf(p,96,"%strigger/touch",hands[h]);CHECK(action_for(p)==g_s26dlRestTouchAction[h][1]);
  snprintf(p,96,"%ssqueeze/value",hands[h]);CHECK(action_for(p)==g_s26dlRestTouchAction[h][2]);
  for(int g=0;g<3;g++)CHECK(g_s26dlRestTouchAction[h][g]);}
 CHECK(g_s26dlRestTouchAction[0][0]!=g_s26dlRestTouchAction[1][0]);
 for(int h=0;h<2;h++){char p[96];snprintf(p,96,"%ssqueeze/force",hands[h]);CHECK(action_for(p)==g_s26ecForceAction[h]&&g_s26ecForceAction[h]);}
 for(int h=0;h<2;h++){char p[96];snprintf(p,96,"%sa/touch",hands[h]);CHECK(action_for(p)==g_s26dlRestTouchAction[h][0]);int n=0;for(int k=0;k<lastCount;k++)if(!strcmp(pathName(saved[k].binding),p)&&saved[k].action==g_s26ecFaceTouchAction[h][0])n++;CHECK(n==1);}
 /* Every bound path must exist in the Valve Index interaction profile. */
 static const char* allowed[]={"system/click","system/touch","a/click","a/touch","b/click","b/touch","squeeze/value","squeeze/force",
  "trigger/click","trigger/value","trigger/touch","thumbstick/x","thumbstick/y","thumbstick/click","thumbstick/touch",
  "trackpad/x","trackpad/y","trackpad/force","trackpad/touch","grip/pose","aim/pose"};
 for(int k=23;k<lastCount;k++){const char* n=pathName(saved[k].binding);int okp=0;
  for(int h=0;h<2;h++)if(!strncmp(n,hands[h],strlen(hands[h])))for(unsigned a=0;a<sizeof(allowed)/sizeof(*allowed);a++)if(!strcmp(n+strlen(hands[h]),allowed[a]))okp=1;
  CHECK(okp);}
 /* Fallbacks: each optional layer drops independently; established bindings survive. */
 reset_runtime();rejectSuffix[0]="/squeeze/value";suggestCalls=0;CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 CHECK(lastCount==31&&suggestCalls==5&&!(g_s26dlRestBindings&2u)&&(g_s26ebExtraBound&2u)&&g_s26ecLayers==5u);
 reset_runtime();rejectSuffix[0]="/trackpad/force";suggestCalls=0;CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 CHECK(lastCount==41&&suggestCalls==5&&g_s26dlRestBindings==2u&&!g_s26ebExtraBound&&g_s26ecLayers==6u);
 reset_runtime();rejectSuffix[0]="/squeeze/force";suggestCalls=0;CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 CHECK(lastCount==37&&suggestCalls==6&&g_s26ecLayers==3u&&!count_suffix("/squeeze/force"));
 { /* haptics also rejected: the established 21-binding suggestion remains */
  XrPath haptic;pStringToPath(0,"/user/hand/right/output/haptic",&haptic);XrPath bclick;pStringToPath(0,"/user/hand/right/input/b/click",&bclick);
  reset_runtime();base[22].binding=haptic;rejectSuffix[0]="/trackpad/force";rejectSuffix[1]="/output/haptic";suggestCalls=0;
  CHECK(s26ec_index_binding((Handle)1,index,base,23)==0&&lastCount==39&&suggestCalls==7&&g_s26dlRestBindings==2u&&!g_s26ebExtraBound);base[22].binding=522;
  /* a rejected core input is reported, never hidden by the optional layers */
  reset_runtime();base[16].binding=bclick;rejectSuffix[0]="/b/click";
  CHECK(s26ec_index_binding((Handle)1,index,base,23)<0&&!g_s26dlRestBindings&&!g_s26ebExtraBound);base[16].binding=516;}
 reset_runtime();rejectPath="/user/hand/left/input/trackpad/force";CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 CHECK(lastCount==41&&!g_s26ebExtraBound&&g_s26dlRestBindings==2u&&action_for("/user/hand/left/input/thumbstick/touch")==g_s26dlRestTouchAction[0][0]);
 reset_runtime();actionError=-1;CHECK(s26ec_index_binding((Handle)1,index,base,23)==0&&lastCount==23&&!g_s26dlRestBindings&&!g_s26ebExtraBound);
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,21)==0&&lastCount==41);
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,20)<0&&s26ec_index_binding((Handle)1,0,base,23)<0);
 /* Index and Frame share one set of actions (no duplicate names) and keep separate bound bits. */
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);int created=actionCreates;Handle keep=g_s26ebExtraAction[0];
 s26dg_frame_binding((Handle)1,base,23);CHECK(actionCreates==created&&created==20&&g_s26ebExtraAction[0]==keep);
 CHECK(g_s26dlRestBindings==3u&&g_s26ebExtraBound==3u&&g_s26nProfiles[5]);
 g_s26dgFrameExtension=0;s26dg_frame_binding((Handle)1,base,23);CHECK(g_s26dlRestBindings==2u&&g_s26ebExtraBound==2u);g_s26dgFrameExtension=1;
 CHECK(s26ec_index_binding((Handle)1,index,base,23)==0&&actionCreates==created);
 reset_runtime();s26dg_frame_binding((Handle)1,base,23);created=actionCreates;CHECK(s26ec_index_binding((Handle)1,index,base,23)==0&&actionCreates==created+6);
 /* Controller policy: Index and Frame use the capacitive/skeletal path; others do not. */
 for(int p=0;p<6;p++){currentProfile=g_s26nProfiles[p];for(int h=0;h<2;h++){CHECK(s26u_controller_fingers_allowed(session,h));CHECK(g_s26diFrameHand[h]==(p==1||p==5));}}
 currentProfile=11;s26dj_set_finger_tracking(0);CHECK(!s26u_controller_fingers_allowed(session,0)&&!g_s26diFrameHand[0]);s26dj_set_finger_tracking(1);
 /* Index contact groups through the production release tick. */
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);
 for(int bits=0;bits<8;bits++)for(int press=0;press<4;press++){
  touchBits[0]=touchBits[1]=bits;gripValue=(press&1)?.5f:0;triggerValue=(press&2)?.5f:0;s26dl_rest_tick(session,1);
  unsigned want=0;if(!(bits&1))want|=1;if(!(bits&2)&&!(press&2))want|=2;if(!(bits&4)&&!(press&1))want|=28;
  for(int h=0;h<2;h++){CHECK(g_s26dmReleasedMask[h]==want&&g_s26dlTouchKnown[h]==31u);CHECK(g_s26dlReleased[h]==(want==31u));}}
 touchBits[0]=touchBits[1]=0;gripValue=.01f;triggerValue=0;s26dl_rest_tick(session,1);CHECK(g_s26dlReleased[0]&&g_s26dlReleased[1]);
 gripValue=.03f;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]&&g_s26dmReleasedMask[0]==3u);gripValue=0;
 touchActive=0;s26dl_rest_tick(session,1);CHECK(!g_s26dlReleased[0]&&!g_s26dlTouchKnown[0]);touchActive=1;
 s26dl_rest_tick(session,0);CHECK(!g_s26dlReleased[0]);
 /* Extra sources tick when bound by Index only. */
 s26eb_extra_tick(session,1);for(int k=0;k<8;k++)CHECK(g_s26ebExtraActive[k]&&g_s26ebExtraRaw[k]);
 g_s26ebExtraBound=0;s26eb_extra_tick(session,1);for(int k=0;k<8;k++)CHECK(!g_s26ebExtraActive[k]);
 /* Feel tick: force and A/B thumb rest only from active, bound Index input. */
 reset_runtime();CHECK(s26ec_index_binding((Handle)1,index,base,23)==0);gripValue=.7f;touchBits[0]=touchBits[1]=0;
 s26ec_index_tick(session,1);for(int h=0;h<2;h++){CHECK(g_s26ecForceValid[h]&&fabsf(g_s26ecForce[h]-.7f)<1e-6f);for(int b=0;b<2;b++)CHECK(g_s26ecFaceTouchValid[h][b]&&g_s26ecFaceTouch[h][b]);}
 gripValue=1.5f;s26ec_index_tick(session,1);CHECK(!g_s26ecForceValid[0]&&g_s26ecForce[0]==0);gripValue=.7f;
 s26ec_index_tick(session,0);CHECK(!g_s26ecForceValid[0]&&!g_s26ecFaceTouchValid[0][0]);
 touchActive=0;s26ec_index_tick(session,1);CHECK(!g_s26ecFaceTouchValid[1][1]&&!g_s26ecFaceTouch[1][1]);touchActive=1;
 g_s26ecLayers=3;s26ec_index_tick(session,1);CHECK(!g_s26ecForceValid[1]&&!g_s26ecFaceTouchValid[1][0]);
 printf("PASS: %d production Valve Index binding/policy/contact checks\n",checks);return 0;
}
'''
c=B/'index_bindings_test.c'
c.write_text(types+'\n'+defines+'\n'+header+'\n'+'\n'.join((R/'source'/x).read_text() for x in ['controller_policy_u.inc','frame_dg.inc','index_ec.inc'])+main)
exe=B/'index_bindings_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-Wall','-I',str(R/'source'),str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
menu=(R/'runtime/script/modules/MenuHandler.hps').read_text(encoding='utf-8')
line=next(x for x in menu.splitlines() if 'if(profile==1)' in x)
for label in ('"RIGHT A"','"RIGHT B"','"LEFT A"','"LEFT B"','buttons[6]="LEFT TRACKPAD"','buttons[7]="RIGHT TRACKPAD"','for(int i=8;i<14;i++) buttons[i]="UNAVAILABLE"'):
    assert label in line,label
src=(R/'source/s26n.c').read_text()
assert '#include "index_ec.inc"' in src and 's26ec_index_binding(inst,profile,indexBinds,oculusBindCount)' in src
print('PASS: Index menu labels and controller-setup wiring')
