from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];baseline=r.parents[1]/'SOMA_VR_109_S26IC/repo'
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
int fails=0;void check(bool ok,const char*n){if(!ok)printf("FAIL %s\n",n);if(!ok)fails++;}
int main(){
 for(float step: {0.001f,0.01f,0.05f}) {
  reset();head[0]=step;check(token("QUERY"),"small_step_requested");
 }
 for(float metric: {.5f,1.f,2.f})for(float angle: {0.f,.7f,2.f}) {
  reset();scale=metric;yaw=angle;float body[3]={};
  for(int cycle=0;cycle<20;cycle++)for(int n=0;n<=120;n++) {
   float t=n<=60?n/60.f:(120-n)/60.f;head[0]=.25f*t;head[2]=.13f*t;frame();
   if(token("QUERY")){char ack[100];snprintf(ack,sizeof(ack),"%.9g,0,%.9g",published[0],published[2]);
    body[0]+=published[0];body[2]+=published[2];check(token("ACK",ack),"accepted_motion_ack");}
  }
  check(h10_len3(body[0],0,body[2])<.00005f,"repeated_lean_no_body_drift");
  check(h10_len3(origin[0],0,origin[2])<.00005f,"repeated_lean_no_origin_drift");
 }
 reset();head[0]=.01f;check(token("QUERY"),"blocked_setup");token("ACK","0,0,0");check(origin[0]==0,"blocked_no_origin_shift");
 reset();head[0]=.02f;check(token("QUERY"),"recenter_step");token("ACK",".02,0,0");float accepted=origin[0];g_h5735RecenterRequests++;origin[0]=head[0];frame();check(!token("QUERY")&&fabsf(accepted-.02f)<1e-6f,"recenter_keeps_accepted_body_movement");
 printf("FAILURES=%d\n",fails);return fails?1:0;
}
'''
results={}
for label,root in [('baseline',baseline),('candidate',r)]:
 src=('#define CANDIDATE\n' if label=='candidate' else '')+prefix.replace('#include <cmath>','#include <cmath>\n#include <initializer_list>')+(root/'source/roomscale_hr.inc').read_text().replace('#include "roomscale_commit_ie.inc"','')+support
 p=r/'build'/('roomscale_id_'+label+'.cpp');p.write_text(src)
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
 t=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
 results[label]={'exit':t.returncode,'output':t.stdout};print(label,t.stdout)
(r/'docs/v109-evidence/roomscale_id_bridge.json').write_text(json.dumps(results,indent=2))
assert results['baseline']['exit']!=0 and results['candidate']['exit']==0
