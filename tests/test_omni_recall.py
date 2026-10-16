"""Production recall guards/queue + translated entity consent (mocked engine).
Does not claim native AngelScript compilation or VR gameplay validation.
"""
from pathlib import Path
import subprocess,sys,json,re
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
code=(R/'source/omni_recall_gb.inc').read_text()
header=r'''
#include <stdio.h>
#include <string.h>
typedef unsigned u32;typedef int i32;
#define ext_Log(...) ((void)0)
#define H5755BH_GAMEPLAY_VR 1
#define H5755BH_PAUSE_QUAD 2
#define H576AN_OMNI_STORAGE_RIGHT_SHOULDER 1
#define H576B_OMNI_LOOSE 5
#define H576AC_HAPTIC_CONFIRM 2
static int runtime=1,running=1;
static int p2_xr_on(void){return runtime;}static int p2_xr_running(void){return running;}
static int h5720_streq(const char*a,const char*b){return !strcmp(a,b);}
static u32 g_h576mScriptRuntimePublished,g_h5753cAuthorityEnabled,g_h576bfMapTransitionActive,
g_h5755bhPresentationState,g_h5755asUiIslandActive,g_h5755asResumeClassifyActive,g_h5755azExitPending,
g_h5755bbTitlePresentationLatch,g_s26CutsceneHandsHidden,g_s26ManualHeal,g_h576anOmniStorageMode,
g_h576bOmniState,g_h30NativeMouseDown,g_h576dDockReleasePending,g_h576dDockReleaseActive,
g_h576eBindPending,g_h576bCaptureNextInteract,g_h576aoOmniHidePending,g_h576aoOmniShoulderStoreAcks;
static void* g_h576bOmniBody,*g_h576bOmniWrapper,*g_h576bOmniOwner,*g_h14GripBody[2],*g_h576aoOmniStowArmedBody[2];
static unsigned g_h576aoOmniStowLastInsideStep[2],g_h576anOmniShoulderRetrieveArmed[2],g_h576anOmniShoulderInside[2];
static const char* g_h5729LastModuleName="player/PlayerState_Normal.hps",*g_h5729LastClassName="cScrPlayerState_Normal";
static char g_h576cCanonicalEntityName[96]="OmniTool";
static unsigned invoked=1,consent=1,calls,forgets,haptics;
static int h576aa_run_global(const char*a,const char*b,const char*c){calls++;if(invoked&&consent){g_h576aoOmniShoulderStoreAcks++;g_h576bOmniState=2;}return invoked;}
static void h576b_forget_body(const char*why){forgets++;g_h576bOmniBody=0;g_h576bOmniWrapper=0;g_h576bOmniOwner=0;}
static void h576ac_queue_haptic(int h,int level){haptics++;}
static int checks;
#define C(x) do{++checks;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
static void good(void){
 runtime=running=1;g_h576mScriptRuntimePublished=g_h5753cAuthorityEnabled=1;
 g_h576bfMapTransitionActive=g_h5755asUiIslandActive=g_h5755asResumeClassifyActive=g_h5755azExitPending=0;
 g_h5755bbTitlePresentationLatch=g_s26CutsceneHandsHidden=g_s26ManualHeal=0;
 g_h5755bhPresentationState=H5755BH_GAMEPLAY_VR;g_h576anOmniStorageMode=1;g_h576bOmniState=5;
 g_h576bOmniBody=(void*)1;g_h576bOmniWrapper=(void*)2;g_h576bOmniOwner=(void*)3;g_h14GripBody[0]=g_h14GripBody[1]=0;
 g_h30NativeMouseDown=g_h576dDockReleasePending=g_h576dDockReleaseActive=g_h576eBindPending=g_h576bCaptureNextInteract=g_h576aoOmniHidePending=0;
 invoked=consent=1;calls=forgets=haptics=0;
}
'''
body=r'''
int main(void){
 good();C(s26gb_recall_allowed());C(s26gb_recall_request(0));C(!calls);s26gb_recall_step();C(calls==1&&forgets==1&&haptics==1&&g_h576bOmniState==2);s26gb_recall_step();C(calls==1);
 unsigned* forbid[]={&g_h576bfMapTransitionActive,&g_h5755asUiIslandActive,&g_h5755asResumeClassifyActive,&g_h5755azExitPending,&g_h5755bbTitlePresentationLatch,&g_s26CutsceneHandsHidden,&g_s26ManualHeal,&g_h30NativeMouseDown,&g_h576dDockReleasePending,&g_h576dDockReleaseActive,&g_h576eBindPending,&g_h576bCaptureNextInteract,&g_h576aoOmniHidePending};
 for(unsigned i=0;i<sizeof(forbid)/sizeof(*forbid);i++){
  good();C(s26gb_recall_request(1));*forbid[i]=1;C(!s26gb_recall_allowed());s26gb_recall_step();C(!calls&&!forgets&&g_h576bOmniBody==(void*)1&&g_h576bOmniState==5);*forbid[i]=0;s26gb_recall_step();C(!calls);
 }
 for(unsigned state=0;state<8;state++)if(state!=5){good();C(s26gb_recall_request(0));g_h576bOmniState=state;s26gb_recall_step();C(!calls&&g_h576bOmniState==state);}
 for(int h=0;h<2;h++){good();C(s26gb_recall_request(0));g_h14GripBody[h]=(void*)99;s26gb_recall_step();C(!calls&&g_h14GripBody[h]==(void*)99);}
 void** ids[]={&g_h576bOmniBody,&g_h576bOmniWrapper,&g_h576bOmniOwner};
 for(unsigned i=0;i<3;i++){good();C(s26gb_recall_request(0));*ids[i]=0;s26gb_recall_step();C(!calls&&!forgets);}
 good();g_h5753cAuthorityEnabled=0;C(!s26gb_recall_allowed());good();g_h576anOmniStorageMode=0;C(!s26gb_recall_allowed());
 good();g_h576mScriptRuntimePublished=0;C(!s26gb_recall_request(1));good();runtime=0;C(!s26gb_recall_request(1));good();running=0;C(!s26gb_recall_request(1));
 good();g_h5729LastModuleName="player/PlayerState_Conversation.hps";C(!s26gb_recall_allowed());g_h5729LastModuleName="player/PlayerState_Normal.hps";
 good();g_h5729LastClassName="cScrPlayerState_Interact_Terminal";C(!s26gb_recall_allowed());g_h5729LastClassName="cScrPlayerState_Normal";
 good();g_h576cCanonicalEntityName[0]=0;C(!s26gb_recall_allowed());strcpy(g_h576cCanonicalEntityName,"OmniTool");
 // Menu command survives pause; never consumes through the pause physics quarantine.
 good();g_h5755bhPresentationState=H5755BH_PAUSE_QUAD;C(s26gb_recall_request(1));s26gb_recall_cancel_unavailable();C(g_s26gbRecallPending&&!calls);
 g_h5755bhPresentationState=H5755BH_GAMEPLAY_VR;s26gb_recall_step();C(forgets==1);
 // State changed before resume: cancel permanently, not postponed until next ordinary gameplay.
 good();C(s26gb_recall_request(1));g_s26CutsceneHandsHidden=1;s26gb_recall_cancel_unavailable();C(!g_s26gbRecallPending);good();s26gb_recall_step();C(!calls);
 good();C(s26gb_recall_request(1));g_h5755bhPresentationState=3;s26gb_recall_cancel_unavailable();C(!g_s26gbRecallPending);
 // Map teardown plus racing old-epoch publication cannot recall a destination tool.
 good();C(s26gb_recall_request(1));unsigned old=g_s26gbRecallPending;s26gb_recall_reset();g_s26gbRecallPending=old;s26gb_recall_step();C(!calls);
 for(int mode=0;mode<2;mode++){good();C(s26gb_recall_request(0));if(mode)invoked=0;else consent=0;s26gb_recall_step();C(calls==1&&!forgets&&!haptics&&g_h576bOmniState==5&&g_h576bOmniBody==(void*)1);}
 // Optional binding is neutral-armed and rising-edge-only; a held menu button cannot recall on resume.
 good();s26gb_recall_reset();s26gb_recall_button_sample(1,0);s26gb_recall_button_sample(1,1);C(!g_s26gbRecallPending);
 s26gb_recall_button_sample(0,1);s26gb_recall_button_sample(1,1);C(g_s26gbRecallPending);s26gb_recall_step();C(calls==1);
 good();s26gb_recall_button_sample(1,1);C(!g_s26gbRecallPending);s26gb_recall_button_sample(0,1);s26gb_recall_button_sample(1,1);s26gb_recall_step();C(calls==1);
 good();g_h5755bhPresentationState=H5755BH_PAUSE_QUAD;s26gb_recall_button_sample(0,1);g_h5755bhPresentationState=H5755BH_GAMEPLAY_VR;s26gb_recall_button_sample(1,1);C(!g_s26gbRecallPending);
 printf("PASS %d production recall lifecycle checks\n",checks);return 0;
}
'''
def run(name,text,cpp=False):
 p=B/(name+('.cpp' if cpp else '.c'));p.write_text(text);exe=p.with_suffix('.exe')
 subprocess.run([sys.argv[1],'c++' if cpp else 'cc','-O2',str(p),'-o',str(exe)],check=True)
 out=subprocess.check_output([str(exe)],text=True);print(out.strip());return out.strip()
results={'native':run('recall_native',header+code+body)}
# Execute the production consent method with only AngelScript handle syntax translated.
s=(R/'runtime/script/custom_depth/prop_catherine_tool.hps').read_text();a=s.index('    bool VR_TryRecall()');b=s.index('    bool VR_TryShoulderStore()',a)
f=s[a:b].replace(' !is null',' != nullptr')
h=r'''
#include <stdio.h>
#include <string>
using namespace std;
static bool runtime=1,owned=1,commit=1;static int stores=0,dirty=0,nativeCalls=0;
static bool _HPL3VR_RuntimeActive_Catherine(){return runtime;}
static bool Player_ToolIsInInventory(string n){return owned;}
static bool cScript_RunGlobalFunc(string a,string b,string c){nativeCalls++;return commit;}
struct Prop {bool active=1,disabled=0,parent=0;bool IsActive(){return active;}bool GetInteractionDisabled(){return disabled;}void*GetAttachmentParent(){return parent?(void*)1:nullptr;}string GetName(){return "LongCanonicalOmniToolName";}void SetSaveDataIsUpdated(bool x){dirty++;}};
struct Tool {bool mbVRBootstrapDone=1,mbInserted=0,mbVRReplacementSourceRetirePending=0,mbVRPhysicalPickupInProgress=0,mbVRHolstered=0;string msSlot="";Prop mBaseObj;
bool VR_TryShoulderStore(){stores++;mbVRHolstered=1;mBaseObj.active=0;return true;}
'''
b=r'''
};
#define C(x) do{checks++;if(!(x)){printf("FAIL entity %d\n",__LINE__);return 1;}}while(0)
int main(){int checks=0;
 for(int i=0;i<12;i++){
 Tool t;runtime=owned=commit=1;stores=dirty=nativeCalls=0;
 switch(i){case 0:runtime=0;break;case 1:owned=0;break;case 2:commit=0;break;case 3:t.mbVRBootstrapDone=0;break;case 4:t.mbInserted=1;break;case 5:t.mbVRReplacementSourceRetirePending=1;break;case 6:t.mbVRPhysicalPickupInProgress=1;break;case 7:t.mbVRHolstered=1;break;case 8:t.mBaseObj.active=0;break;case 9:t.mBaseObj.disabled=1;break;case 10:t.mBaseObj.parent=1;break;case 11:t.msSlot="active_socket";break;}
 C(!t.VR_TryRecall());C(!stores&&!dirty);
 }
 runtime=owned=commit=1;Tool t;C(t.VR_TryRecall());C(stores==1&&dirty==1&&t.mbVRHolstered&&!t.mBaseObj.active);C(!t.VR_TryRecall());C(stores==1);
 printf("PASS %d translated entity consent checks\n",checks);return 0;
}
'''
results['script_consent']=run('recall_entity',h+f+b,True)
# Integration boundaries: queue is after UI quarantine but cancellation precedes it;
# legacy store/draw and state transitions remain unmodified except explicit queue invalidation.
n=(R/'source/s26n.c').read_text();a=n.index('static void h14_physics_step(');a=n.index('static void h14_physics_step(',a) # sole definition
section=n[a:n.index('s26x_phone_step(dt);',a)]
assert section.index('s26gb_recall_cancel_unavailable()')<section.index('g_h5755atUiPhysicsQuarantineSteps')<section.index('s26gb_recall_step()')
assert 'h5748n_copy_tstring((void*)className,name,sizeof(name))' in n
menu=(R/'runtime/script/modules/MenuHandler.hps').read_text()
assert 'mvVRButtonMap={0,1,2,3,4,5,14}' in menu
assert 'HPL3VR_Option("RECALL OMNI-TOOL",8)' in menu and 'if(mlVRComfortCategory==0) return 12;' in menu
assert 'UNBIND RECALL' not in menu and 'HPL3VR_Option("CLEAR BINDING",2)' in menu
assert 'i==6 ? 14 : i' in menu and '(v<14 && seen[v])' in menu
results['integration']='PASS queue placement, long entity names, non-overlapping menu rows, legacy default/unassigned validation'
(B/'recall-results.json').write_text(json.dumps(results,indent=2));print(results['integration'])
