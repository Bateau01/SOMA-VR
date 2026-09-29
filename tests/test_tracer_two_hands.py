"""Production helpers and actual Grab-exit block, with mocked engine boundaries."""
from pathlib import Path
import re,subprocess,sys,json,os
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8')
def block(start):
 a=s.index(start);b=s.index('{',a);i=b+1;n=1
 while n:n+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def fn(n):return block('static i32 '+n+'(')
header=r'''
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cstdlib>
using i32=int;using u32=unsigned;
int g_h30NativeUseHand,g_h30NativeMouseDown,g_h5755chGrabStateActive,g_h5755chGrabButtonDetached;
int g_h31NativeUseJointed,g_h31NativePrevPosValid,g_h15GripJointed[2],g_lastSqueezeActive[2];
float g_lastSqueeze[2];int g_h38ThisUseConsumed[2];void* g_h39NativeUseProp[2];
void* g_h5755chGrabStateOwner;const void* g_h31NativeUseBody;const void* g_h14GripBody[2];
const void* g_h5755chGrabStateBody;void* g_h5755chGrabStateWrapper;
int g_h5755chGrabPrimaryHand,g_h5755chGrabExpected,g_h5755cjGrabExpectedStep;
int g_h5755chGrabStateExits,g_h5755chGrabEarlyExits,releases,checks;
int p_h16MouseEvent=1,g_s26ceDirectGrabDispatch,g_s26bvReadableStep,g_h14PhysicsSteps;
const void* g_s26bvReadableWrapper;
int h5720_streq(const char*a,const char*b){return a&&b&&!strcmp(a,b);}
int h5755cj_hand_matches_grab_owner(int h){return g_h14GripBody[h]&&g_h14GripBody[h]==g_h5755chGrabStateBody;}
void ext_Log(const char*,...){}
void h14_release(int h,const char*){g_h14GripBody[h]=nullptr;releases++;}
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line %d\n",__LINE__);exit(1);}}while(0)
void seed(int h){
 g_h30NativeUseHand=h;g_h30NativeMouseDown=1;g_h5755chGrabStateActive=1;g_h5755chGrabButtonDetached=1;
 g_h5755chGrabStateOwner=(void*)3;g_h5755chGrabStateBody=(void*)4;g_h31NativeUseBody=(void*)5;
 g_h5755chGrabPrimaryHand=h;g_h5755chGrabExpected=0;
 for(int j=0;j<2;j++){g_h14GripBody[j]=j==h?(void*)4:nullptr;g_h15GripJointed[j]=0;g_lastSqueezeActive[j]=1;g_lastSqueeze[j]=1;g_h39NativeUseProp[j]=j==h?(void*)3:nullptr;}
 releases=0;
}
'''
exitblock=block('if(oldKind==7&&newKind!=7){')
main=r'''
int main(){
 const char* types[]={"Slide","SwingDoor","Lever","Wheel","Push","Tear"};
 for(int h=0;h<2;h++)for(auto type:types){
  char mp[160],cn[160];sprintf(mp,"player/PlayerState_Interact_%s.hps",type);sprintf(cn,"cScrPlayerState_Interact_%s",type);
  seed(h);CHECK(beginGate(1-h,(void*)7,0,(void*)6));CHECK(g_h14GripBody[h]==(void*)4);CHECK(g_h30NativeUseHand==-1);
  // The new native-use begin now owns the other hand and exact mechanism.
  g_h30NativeMouseDown=1;g_h30NativeUseHand=1-h;g_h39NativeUseProp[1-h]=(void*)6;
  CHECK(s26ci_keep_independent_grip(h,mp,cn));exitGrab(mp,cn);CHECK(!releases);CHECK(g_h14GripBody[h]==(void*)4);CHECK(!g_h5755chGrabStateActive);
 }
 for(int h=0;h<2;h++)for(int bad=0;bad<9;bad++){
  seed(h);void* owner=(void*)6;int other=1-h;
  if(bad==0)other=h;if(bad==1)owner=nullptr;if(bad==2)owner=(void*)3;
  if(bad==3)g_h5755chGrabStateActive=0;if(bad==4)g_h5755chGrabButtonDetached=0;
  if(bad==5)g_h14GripBody[h]=nullptr;if(bad==6)g_h15GripJointed[h]=1;
  if(bad==7)g_lastSqueezeActive[h]=0;if(bad==8)g_lastSqueeze[h]=0;
  CHECK(!s26ci_yield_grab_use(other,owner));CHECK(g_h30NativeUseHand==h);
 }
 for(int h=0;h<2;h++){
  for(auto state:{"Normal","Conversation","Dead","Interact_Terminal","Interact_Read"}){
   char mp[160],cn[160];sprintf(mp,"player/PlayerState_%s.hps",state);sprintf(cn,"cScrPlayerState_%s",state);
   seed(h);g_h30NativeUseHand=1-h;g_h39NativeUseProp[1-h]=(void*)6;exitGrab(mp,cn);CHECK(releases==1);CHECK(!g_h14GripBody[h]);
  }
  seed(h);exitGrab("player/PlayerState_Interact_Slide.hps","cScrPlayerState_Interact_Slide");CHECK(releases==1); // no opposite-hand ownership
 }
 float head[3]={5,2,-4};
 for(float scale:{0.5f,0.7f,1.0f,1.5f,2.0f})for(int axis=0;axis<3;axis++)for(int sign:{-1,1}){
  float m[16]={};m[0]=m[5]=m[10]=m[15]=1;
  // Place neck on a sphere around the actual head, in every direction.
  auto place=[&](float d){for(int j=0;j<3;j++)m[12+j]=head[j];m[13]-=.123452800f;m[12+axis]+=sign*d*scale;};
  place(.26f);CHECK(s26ci_tracer_near(m,head,scale,0));
  place(.30f);CHECK(s26ci_tracer_near(m,head,scale,1));
  place(.70f);CHECK(!s26ci_tracer_near(m,head,scale,0));CHECK(!s26ci_tracer_near(m,head,scale,1));
  // Body near mouth also works when the bottle points away.
  for(int j=0;j<3;j++)m[12+j]=head[j];m[12]+=.20f*scale;CHECK(s26ci_tracer_near(m,head,scale,0));
  CHECK(!s26ci_tracer_near(m,head,0,0));
 }
 float invalid[16];for(auto&v:invalid)v=NAN;CHECK(!s26ci_tracer_near(invalid,head,1,0));
 printf("PASS %d tracer geometry and independent-hand transition checks\n",checks);
}
'''
B=R/'build';p=B/'tracer_two_hands.cpp';exe=B/'tracer_two_hands.exe'
prefix=block('static void h30_native_use_begin(').split('    i32 readable=')[0]
prefix=prefix.replace('static void h30_native_use_begin','static i32 beginGate').replace('return;','return 0;')+'return 1;}\n'
production='#include <initializer_list>\n'+header+fn('s26ci_yield_grab_use')+fn('s26ci_keep_independent_grip')+fn('s26ci_tracer_near')+prefix+'\nvoid exitGrab(const char* newMp,const char* newCn){int oldKind=7,newKind=2;'+exitblock+'}\n'+main
p.write_text(production)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
v=subprocess.run([str(exe)],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/tracer_two_hands_tests.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production functions and actual Grab-exit block with engine mocks. No headset trajectory.'},indent=2))
old=R.parents[1]/'SOMA_VR_S26CH_BOB_COMFORT/repo/source/s26n.c'
if v.returncode==0 and old.is_file():
 # Prove this regression is detected in the preceding release's actual exit block.
 s=old.read_text(encoding='utf-8');oldexit=block('if(oldKind==7&&newKind!=7){')
 p=B/'tracer_two_hands_previous_exit.cpp';exe=B/'tracer_two_hands_previous_exit.exe'
 p.write_text(production.replace(exitblock,oldexit))
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
 before=subprocess.run([str(exe)],capture_output=True,text=True)
 assert before.returncode!=0,'Previous release must reproduce dropped prop'
 (R/'audit/previous_grab_exit_regression.json').write_text(json.dumps({'exit':before.returncode,'output':before.stdout,'expected_failure':True,'scope':'Previous production Grab-exit block under the same two-hand scenario.'},indent=2))
 print('Previous production Grab-exit block reproduces the dropped-prop regression.')
raise SystemExit(v.returncode)
