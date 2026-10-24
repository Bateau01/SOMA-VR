from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];baseline=r.parents[1]/'SOMA_VR_109_S26IB/repo'
old=(r/'tests/test_roomscale_bridge_hr.py').read_text()
prefix=old.split("c=r'''",1)[1].split("'''+",1)[0]+r'''
using u8=unsigned char; unsigned g_h14PhysicsSteps; float camera[12]; void*p2_camera_obj(){return camera;} void ext_Log(const char*,...){} int s26ie_room_apply(const float*){return 1;}
''' 
support=r'''
int token(const char*fn,const char*arg=""){H5730TString f{fn},a{arg};return s26hr_room_token(&a,&f);}
void frame(){g_frameCounter++;g_s26nHeadValidFrame=g_frameCounter;}
void reset(){memset(origin,0,sizeof(origin));memset(head,0,sizeof(head));g_frameCounter+=10;g_s26nHeadValidFrame=g_frameCounter;g_s26hrRoomFrame=0xffffffffu;g_s26hrRoomPending=0;g_h576bfMapTransitionActive=0;g_s26CutsceneHandsHidden=0;scale=1;yaw=0;
#ifdef CANDIDATE
g_s26icRoomSample=0;g_s26icRoomSuspend=0;g_s26icRoomEpoch=g_h5735RecenterRequests;memset(g_s26icRoomNeutral,0,sizeof(g_s26icRoomNeutral));
#endif
}
int fails=0;void check(bool ok,const char*n){printf("%s %s\n",ok?"PASS":"FAIL",n);if(!ok)fails++;}
int main(){
 reset();head[0]=1.2f;check(token("QUERY")&&h10_len3(published[0],0,published[2])<=.10001f,"large_initial_offset_bounded");
 reset();token("RESET");head[0]=.4f;frame();check(!token("QUERY")&&origin[0]==0,"restricted_motion_discarded_without_camera_change");
 head[0]+=.15f;frame();check(token("QUERY"),"fresh_motion_after_restriction");
 reset();head[0]=.02f;token("QUERY");head[0]=.7f;frame();check(!token("QUERY")&&origin[0]==0,"tracking_jump_no_body_catchup");head[0]+=.15f;frame();check(token("QUERY"),"jump_recovery_new_motion");
 reset();token("QUERY");g_frameCounter+=10;g_s26nHeadValidFrame=g_frameCounter;head[0]=.4f;check(!token("QUERY"),"tracking_gap_no_catchup");
 reset();g_s26CutsceneHandsHidden=1;head[0]=.4f;check(!token("QUERY"),"hidden_hands_reject");g_s26CutsceneHandsHidden=0;frame();check(!token("QUERY")&&origin[0]==0,"hidden_hands_resume_no_catchup");
 reset();head[0]=.3f;check(token("QUERY"),"ack_setup");check(token("ACK",".05,0,0")&&fabsf(origin[0]-.05f)<1e-6f,"accepted_only_compensation");check(!token("ACK",".05,0,0"),"ack_once");
 reset();token("RESET");head[0]=.4f;frame();token("QUERY");g_h5735RecenterRequests++;origin[0]=head[0];frame();check(!token("QUERY"),"recenter_discards_neutral");head[0]+=.15f;frame();check(token("QUERY"),"recenter_new_motion");
 reset();head[0]=.3f;token("QUERY");g_h576bfMapTransitionActive=1;check(!token("ACK",".05,0,0")&&origin[0]==0,"transition_cancels_pending");
 printf("FAILURES=%d\n",fails);return fails?1:0;
}
'''
results={}
for label,root in [('baseline',baseline),('candidate',r)]:
 src=('#define CANDIDATE\n' if label=='candidate' else '')+prefix+(root/'source/roomscale_hr.inc').read_text().replace('#include "roomscale_commit_ie.inc"','')+support
 p=r/'build'/('roomscale_ic_'+label+'.cpp');p.write_text(src)
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
 t=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
 results[label]={'exit':t.returncode,'output':t.stdout};print(label,t.stdout)
(r/'docs/v109-evidence/roomscale_ic_bridge.json').write_text(json.dumps(results,indent=2))
assert results['baseline']['exit']!=0 and results['candidate']['exit']==0
