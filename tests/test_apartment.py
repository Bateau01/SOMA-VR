"""Exercise production readable acquisition and tool authorization with mocked engine boundaries."""
from pathlib import Path
import subprocess,sys,json,re,os
R=Path(__file__).resolve().parents[1]
s=Path(os.environ.get('SOMA_TEST_SOURCE',str(R/'source/s26n.c'))).read_text(encoding='utf-8')
def fn(name):
 a=re.search(r'static i32 '+name+r'\([^;{}]*\)\s*\{',s).start();b=s.index('{',a);n=1;i=b+1
 while n:
  n+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
header=r'''
#include <cstdio>
#include <cstring>
#include <cstdlib>
using i32=int;using u32=unsigned;
struct H25PendingInteract {int jointed;unsigned physicsStep;const void* newtonBody;float contact[3];};
struct Pending{int valid;};Pending g_h5755chGrabPending[2];
struct H576AAInvItem{int stowed;const void* raw;};
const void* g_h14GripBody[2];const void* g_s26bvReadableWrapper;
u32 g_s26bvReadableStep,g_h14PhysicsSteps=10,g_h5755haGripEdgeStep[2]={10,10};
int g_lastSqueezeActive[2]={1,1};float g_lastSqueeze[2]={1,1};
int g_h5755gwPreserveExistingGrabUse[2],g_h552ContactLatchBypass[2];
int g_h5755chGrabExpected,g_h5755chGrabStateActive,g_h5755chGrabPrimaryHand;
int g_h30NativeMouseDown,g_h30NativeUseHand;void* g_h39NativeUseProp[2];
const void* g_h5755chGrabStateBody;void* g_h5755chGrabStateWrapper;void* g_h5755chGrabStateOwner;
unsigned g_h5755cjGrabExpectedStep;
int g_h576mScriptRuntimePublished=1,g_h576bfMapTransitionActive,g_s26ManualHeal,g_s26CutsceneHandsHidden;
const char* g_h5729LastClassName="cScrPlayerState_Normal";
const char* g_h5729LastModuleName="player/PlayerState_Normal.hps";
int g_h5755chGrabButtonDetached,commits,alreadyObserved;
int g_h31NativeUseJointed,g_h44SliderAnchorValid[2],g_h39SliderValid[2],g_h481HingeValid[2],g_h484CurtainAnchorValid[2],g_h5755ceNativeSwingDoorActive[2];
int g_h38ThisUseConsumed[2],g_h38StateActivation[2],g_h5755gwSameOwnerGrabAdopts[2];
const void* g_h31NativeUseBody;
int h5755gw_exact_grab_state_now(){return commits>0;}
int xr=1,running=1,paused,grabAllowed,validPose=1,externalJoint,poseOK=1,latchOK=1,begins,latches,detaches,logs,checks;
void* owner=(void*)2;float mass=.2f;
void* h482_body_owner(const void*,void*){return owner;}
const void* h568_first_external_joint(const void*){return externalJoint?(void*)4:nullptr;}
void massFn(const void*,float* m,float*,float*,float*){*m=mass;}
void (*p_h14GetMass)(const void*,float*,float*,float*,float*)=massFn;
int h14_hand_pose(int,float*,float*){return poseOK;}int h15_grip_center_world(int,float*,float*){return poseOK;}
void h30_native_use_begin(int h,const void* b,int,void* o){begins++;g_h30NativeMouseDown=1;g_h30NativeUseHand=h;g_h39NativeUseProp[h]=o;g_h31NativeUseBody=b;}
void h14_latch(int h,const void* b,float,float,float*,float*,float,const float*,int,int,int){
 latches++;if(latchOK)g_h14GripBody[h]=b;
}
void h5755ch_detach_native_grab_button(int){detaches++;g_h5755chGrabButtonDetached=1;}
int h5755cj_reassert_native_grab_state(int){commits++;return 1;}
void h5729_state_boundary_observe(const char*){
 if(commits&&g_h5755chGrabExpected){
  g_h5729LastModuleName="player/PlayerState_Interact_Grab.hps";
  g_h5729LastClassName="cScrPlayerState_Interact_Grab";
  if(alreadyObserved)return;
  g_h5755chGrabExpected=0;g_h5755chGrabStateActive=1;
  h5755ch_detach_native_grab_button(g_h5755chGrabPrimaryHand);
 }
}
void h5755ch_verify_grab_script(){}
void ext_Log(const char*,...){logs++;}
int p2_xr_on(){return xr;}int p2_xr_running(){return running;}int h5754h_pause_active(){return paused;}
int h5720_streq(const char*a,const char*b){return !strcmp(a,b);}
int h5755cj_hand_matches_grab_owner(int h){return g_h14GripBody[h]&&g_h14GripBody[h]==g_h5755chGrabStateBody;}
int visual_pose_valid(int){return validPose;}
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
'''
main=r'''
int main(){
 H25PendingInteract p={0,10,(void*)7,{1,2,3}};void* wrapper=(void*)3;
 for(alreadyObserved=0;alreadyObserved<2;alreadyObserved++)for(int h=0;h<2;h++){
  for(int bad=0;bad<10;bad++){
   g_h14GripBody[h]=nullptr;g_s26bvReadableWrapper=wrapper;g_s26bvReadableStep=10;
   p.jointed=0;p.physicsStep=10;g_lastSqueezeActive[h]=1;g_lastSqueeze[h]=1;
   externalJoint=0;mass=.2f;poseOK=1;latchOK=1;begins=latches=detaches=0;
   commits=0;g_h30NativeMouseDown=0;g_h5755chGrabStateActive=0;g_h5755chGrabButtonDetached=0;
   g_h5729LastModuleName="player/PlayerState_Normal.hps";g_h5729LastClassName="cScrPlayerState_Normal";
   if(bad==1)p.jointed=1;if(bad==2)p.physicsStep=9;if(bad==3)g_s26bvReadableStep=9;
   if(bad==4)g_lastSqueezeActive[h]=0;if(bad==5)g_lastSqueeze[h]=.2f;
   if(bad==6)externalJoint=1;if(bad==7)mass=0;if(bad==8)poseOK=0;if(bad==9)latchOK=0;
   int result=s26ce_latch_readable(h,&p,owner,wrapper);
   CHECK(result==(bad==0));CHECK(!g_h552ContactLatchBypass[h]&&!g_h5755gwPreserveExistingGrabUse[h]);
   CHECK(detaches==(bad==0));
   if(!bad){CHECK(g_h14GripBody[h]==p.newtonBody);CHECK(g_h5755chGrabPrimaryHand==h);CHECK(begins==1&&latches==1);
    CHECK(s26ce_latch_readable(h,&p,owner,wrapper)==0);CHECK(begins==1&&latches==1);
    CHECK(h5755fm_grab_gameplay_actions_allowed());CHECK(commits==1);
    g_lastSqueeze[h]=0;g_h14GripBody[1-h]=nullptr;CHECK(!h5755fm_grab_gameplay_actions_allowed());}
  }
 }
 H576AAInvItem it={0,(void*)7};g_h14GripBody[0]=it.raw;g_h14GripBody[1]=nullptr;
 for(int bad=0;bad<12;bad++){
  g_h576mScriptRuntimePublished=1;xr=running=validPose=1;paused=0;
  g_h576bfMapTransitionActive=g_s26ManualHeal=g_s26CutsceneHandsHidden=0;
  g_h5729LastClassName="cScrPlayerState_Normal";grabAllowed=0;it.stowed=0;it.raw=(void*)7;
  if(bad==1)xr=0;if(bad==2)running=0;if(bad==3)paused=1;if(bad==4)validPose=0;
  if(bad==5)it.stowed=1;if(bad==6)it.raw=nullptr;if(bad==7)g_h576bfMapTransitionActive=1;
  if(bad==8)g_s26ManualHeal=1;if(bad==9)g_s26CutsceneHandsHidden=1;
  if(bad==10)g_h5729LastClassName="cScrPlayerState_Interact_Terminal";
  if(bad==11)g_h576mScriptRuntimePublished=0;
  CHECK(s26_tool_hand_authorized(&it)==(bad==0));
 }
 printf("PASS %d readable transaction and held-tool authorization checks\n",checks);
}
'''
B=R/'build';B.mkdir(exist_ok=True);(R/'audit').mkdir(exist_ok=True)
p=B/'apartment.cpp';exe=B/'apartment.exe'
p.write_text(header+fn('h5755gw_adopt_existing_same_owner_grab')+fn('s26ce_latch_readable')+fn('h5755fm_grab_gameplay_actions_allowed')+fn('s26_tool_hand_authorized')+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
v=subprocess.run([str(exe)],capture_output=True,text=True)
print(v.stdout+v.stderr)
(R/'audit/apartment_tests.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production C functions with engine mocks; native script VM tested separately.'},indent=2))
raise SystemExit(v.returncode)
