"""Extracted production dispatch with engine stubs: input isolation/cancellation, not gameplay proof."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
header=r"""
#include <cstdio>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;
struct H14Scan{};struct Pull{void*body;};Pull g_s26hdPull[2];
int g_h14GripBody[2],g_h25PendingValid[2],g_h25AttemptBody[2],g_h30NativeMouseDown,g_h30NativeUseHand=-1,g_h5755haEdgeNativeActive[2],g_h576avThetaPendingHand=-1,g_s26xPhonePending,g_s26hdLaserHand=-1;
int g_s26CutsceneHandsHidden,g_h576bfMapTransitionActive,g_h34HandNewton[2]={1,1},g_h532Dormant[2],g_h532ArmState[2]={2,2};
int g_h545Pending[2],g_h545CandidateStable[2],g_h545AppliedSqueezeLevel[2],g_h5755eiContactPropAge[2],g_h5755eiContactPropCount[2],g_h5755hjStaticContactCount[2],g_lastSqueezeActive[2]={1,1};
u32 g_h5755eiContactPropStep[2],g_h5755hjStaticContactStep[2],g_h5755haGripEdgeStep[2],g_s26jbContactRequestStep[2],g_h14PhysicsSteps;
float g_lastSqueeze[2];int paused,mode,tracked=1,normal=1,builds,dispatches,winner;
int ni_native_input(){return mode;}int h5748_is_stump(int){return 0;}int h5754h_pause_active(){return paused;}int visual_pose_valid(int){return tracked;}
int h5755ha_exact_normal_state_now(){return normal;}int h5755gw_exact_grab_state_now(){return 0;}
float clamp01(float x){return x;}int h549_quantize_gesture_level(int,int,float f){return f>.55f?2:0;}
int h14_hand_pose(int,float*,float*){return 1;}int h558_build_authored_scan(int,const void*,float*,H14Scan*){++builds;return 1;}
int h5755gz_try_exact_current_loose_contact(int,const H14Scan*,const float*,int){++dispatches;return winner==1;}
int s26db_queue_contact_cable(int,const float*){++dispatches;return winner==2;}
int s26da_queue_contact_item(int,const float*){++dispatches;return winner==3;}
int s26cx_queue_contact_mechanism(int,const float*){++dispatches;return winner==4;}
"""
policy=(r/'source/closure_policy_jb.inc').read_text()
code=header+policy+'\nstatic JBClosureWindow g_s26jbClosure[2];\n'+(r/'source/closure_contact_jb.inc').read_text()+r"""
int checks;
#define C(x) do{++checks;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
int main(){for(int hz=60;hz<=120;hz+=60)for(int route=0;route<=4;++route){
 winner=route;builds=dispatches=0;g_h14PhysicsSteps+=100;g_h5755haGripEdgeStep[1]=g_h14PhysicsSteps;g_lastSqueeze[1]=1;
 s26jb_closure_contact((void*)1,1.f/hz);C(g_s26jbClosure[1].armed);C(builds==0);
 unsigned edge=g_h5755haGripEdgeStep[1];++g_h14PhysicsSteps;g_h5755eiContactPropStep[1]=g_h14PhysicsSteps;g_h5755eiContactPropCount[1]=1;
 s26jb_closure_contact((void*)1,1.f/hz);C(builds==1);C(dispatches==(route?route:4));C(g_h5755haGripEdgeStep[1]==edge);C(g_s26jbContactRequestStep[1]==g_h14PhysicsSteps);
 for(int k=0;k<30;++k){++g_h14PhysicsSteps;g_h5755eiContactPropStep[1]=g_h14PhysicsSteps;s26jb_closure_contact((void*)1,1.f/hz);C(builds==1);}
 }
 for(int reason=0;reason<9;++reason){builds=dispatches=0;g_h14PhysicsSteps+=10;g_h5755haGripEdgeStep[1]=g_h14PhysicsSteps;g_lastSqueeze[1]=1;s26jb_closure_contact((void*)1,1.f/120);
 ++g_h14PhysicsSteps;g_h5755eiContactPropStep[1]=g_h14PhysicsSteps;
 if(reason==0)g_h14GripBody[1]=1;if(reason==1)g_h25PendingValid[1]=1;if(reason==2)g_h25AttemptBody[1]=1;if(reason==3)g_lastSqueeze[1]=0;if(reason==4)paused=1;if(reason==5)tracked=0;if(reason==6)mode=1;if(reason==7)g_s26hdPull[1].body=(void*)1;if(reason==8)g_h14PhysicsSteps++;
 s26jb_closure_contact((void*)1,1.f/120);C(builds==0);C(!g_s26jbClosure[1].armed);
 g_h14GripBody[1]=g_h25PendingValid[1]=g_h25AttemptBody[1]=paused=mode=0;tracked=1;g_s26hdPull[1].body=0;g_lastSqueeze[1]=1;
 }
 printf("PASS %d dispatch/cancellation assertions; mocked engine only\n",checks);return 0;}
"""
p=r/'build/jb_closure_integration.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-closure-integration/test.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout},indent=2));print(v.stdout);raise SystemExit(v.returncode)
