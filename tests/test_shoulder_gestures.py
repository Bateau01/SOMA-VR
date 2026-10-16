from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head=r'''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <assert.h>
typedef int i32;typedef uint32_t u32;typedef int64_t i64;typedef unsigned char u8;
#define ext_Cosf cosf
#define ext_Sinf sinf
#define H5755BH_GAMEPLAY_VR 4
static u32 g_s26fwCancelGeneration;
static u32 g_h14PhysicsSteps=1,g_h5745YawCaptures=1,g_frameCounter=1,g_h14LastVisualFrame=1,g_h14GrabCount[2];
static int g_lastActive[2]={1,1},g_lastFlags[2]={3,3},g_lastLocateResult[2],g_lastSqueezeActive[2]={1,1};
static int g_h5753cAuthorityEnabled=1,g_s26ManualHeal,g_s26CutsceneHandsHidden,g_h576bfMapTransitionActive,g_h5755asUiIslandActive,g_h5755asResumeClassifyActive,g_h5755azExitPending,g_h5755bbTitlePresentationLatch;
static int g_h5755bhPresentationState=4,g_h14VisualSeen=1,g_h576agPendingHand=-1,g_s26xPhonePending,g_h30NativeMouseDown,g_h30NativeUseHand;
static const void *g_h14GripBody[2],*g_h576aoOmniStowArmedBody[2],*g_h576aoLeftStowArmedBody[2];
static u32 g_h576aoOmniStowLastInsideStep[2],g_h576aoLeftStowLastInsideStep[2];
static u8 g_h15GripJointed[2],g_h484ClusterGrip[2];
static float g_h576anOmniShoulderRadius=.125f,g_h576aaShoulderRadius=.125f,g_h576apSlotDepthScale=.65f;
static float wrist[2][3],anchors[2][3]={{-.2f,-.2f,-.1f},{.2f,-.2f,-.1f}},yaw,metric=1;
static int reads,rawValid=1;static i64 xr[64];
static void* p2_xr_obj(void){return xr;}
static int h20_mem_readable(void*p,int n){return 1;}
static float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
static void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*sizeof(float));}
static int h14_hand_pose_raw(int h,float*p,float*m){reads++;h10_copy_f(p,wrist[h],3);memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;h10_copy_f(m+12,p,3);return rawValid;}
static int h576aa_shoulder_anchor(float*p){h10_copy_f(p,anchors[0],3);return 1;}
static int h576an_omni_shoulder_anchor(float*p){h10_copy_f(p,anchors[1],3);return 1;}
static float s26r_shoulder_yaw(void){return yaw;}
static float h5755ea_world_units_per_meter(void){return metric;}
static int h15_grip_center_world(int h,const float*m,float*p){h10_copy_f(p,m+12,3);return 1;}
'''
test=r'''
static char item,other;
static void tick(int ms){xr[0xE8/8]+=(i64)ms*1000000;g_h14PhysicsSteps++;s26fw_begin_step();}
static void at(int h,int slot,float dy){h10_copy_f(wrist[h],anchors[slot],3);wrist[h][1]+=dy;}
int main(){xr[0xE8/8]=1000000000;
 // Before: press outside then enter while held has no inside grip edge.
 // After: a fresh ticket permits exactly one attempt within 250 ms, both hands/slots.
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++){
  s26fw_reset();at(h,slot,.5f);tick(10);s26fw_update_entry(h,1,1);
  assert(!s26fw_take_entry(h,s26fw_near(h,slot,0,0,0),1));
  for(int i=0;i<10;i++){tick(10);s26fw_update_entry(h,1,0);}
  at(h,slot,0);tick(10);s26fw_update_entry(h,1,0);
  assert(s26fw_take_entry(h,s26fw_near(h,slot,0,0,0),1));
  assert(!s26fw_take_entry(h,1,1));
 }
 // Old held grip never arms; expiry, release, tracking, recenter and competing acquisition cancel.
 for(int mode=0;mode<7;mode++){
  s26fw_reset();tick(10);s26fw_update_entry(0,1,mode!=0);
  if(mode==1){for(int i=0;i<26;i++){tick(10);s26fw_update_entry(0,1,0);}}
  if(mode==2)s26fw_update_entry(0,0,0);
  if(mode==3){g_lastActive[0]=0;tick(10);g_lastActive[0]=1;}
  if(mode==4){g_h5745YawCaptures++;tick(10);s26fw_update_entry(0,1,0);}
  if(mode==5){g_h14GrabCount[0]++;tick(10);s26fw_update_entry(0,1,0);}
  if(mode==6)s26fw_cancel_retrieve(0);
  assert(!s26fw_take_entry(0,1,1));
 }
 // Menu authority cancels even if pause had no physics tick.
 tick(10);s26fw_update_entry(0,1,1);g_s26fwCancelGeneration++;tick(10);s26fw_update_entry(0,1,0);assert(!s26fw_take_entry(0,1,1));
 // Independent hands: cancellation on one cannot consume the other ticket.
 tick(10);s26fw_update_entry(0,1,1);s26fw_update_entry(1,1,1);s26fw_cancel_retrieve(0);assert(s26fw_take_entry(1,1,1));
 // Snapshot reused across position, buzz and release within the same physics step.
 s26fw_reset();at(0,0,0);tick(10);int n=reads;assert(s26fw_near(0,0,0,0,0));at(0,0,.5f);assert(s26fw_near(0,0,0,0,0));assert(reads==n+1);
 tick(10);assert(!s26fw_near(0,0,0,0,0));
 // Same eligible body and slot: 2cm exit margin, bounded extra grace; no stale extension.
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++){
  s26fw_reset();g_h14GripBody[h]=&item;at(h,slot,0);tick(10);assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  assert(!s26fu_shoulder_stow_ready(h,&item,1-slot,1));
  at(h,slot,.15f);tick(10);assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  for(int i=0;i<10;i++){tick(10);assert(s26fu_shoulder_stow_ready(h,&item,slot,1));}
  tick(20);assert(!s26fu_shoulder_stow_ready(h,&item,slot,1));
  // Never rearm by hovering in the grace-only shell.
  tick(10);assert(!s26fu_shoulder_stow_ready(h,&item,slot,1));
  at(h,slot,0);tick(10);assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  at(h,slot,.3f);tick(10);assert(!s26fu_shoulder_stow_ready(h,&item,slot,1));
  g_h14GripBody[h]=0;
 }
 // Revalidate ownership, eligibility, two-hand, joint, tracking, pause and map boundaries.
 for(int mode=0;mode<9;mode++){
  s26fw_reset();g_h14GripBody[0]=&item;at(0,0,0);tick(10);assert(s26fu_shoulder_stow_ready(0,&item,0,1));
  if(mode==0)g_h14GripBody[0]=0;if(mode==1)g_h14GripBody[1]=&item;if(mode==2)g_h15GripJointed[0]=1;
  if(mode==3)g_h484ClusterGrip[0]=1;if(mode==4)rawValid=0;if(mode==5)g_h5755asUiIslandActive=1;
  if(mode==6)g_h576bfMapTransitionActive=1;if(mode==7)g_h14GripBody[0]=&other;
  tick(10);assert(!s26fu_shoulder_stow_ready(0,&item,0,mode!=8));
  g_h14GripBody[0]=g_h14GripBody[1]=0;g_h15GripJointed[0]=g_h484ClusterGrip[0]=0;rawValid=1;g_h5755asUiIslandActive=g_h576bfMapTransitionActive=0;
 }
 // Rotation/scaling of snapshot ellipsoid agrees with its calibrated dimensions.
 int geometry=0;
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++)for(int sc=0;sc<3;sc++)for(int rot=-4;rot<=4;rot++){
  metric=sc==0?.7f:sc==1?1:1.4f;yaw=rot*.7f;at(h,slot,0);
  wrist[h][0]+=cosf(yaw)*.18f*metric;wrist[h][2]-=sinf(yaw)*.18f*metric;tick(10);assert(s26fw_near(h,slot,0,0,0));
  at(h,slot,.13f*metric);tick(10);assert(!s26fw_near(h,slot,0,0,0));geometry++;
 }
 printf("PASS: bounded fresh-grip entry, no old-grip retrieval, single attempt, independent hands, shared snapshots, same-body/slot grace with expiry, ownership and lifecycle cancellation; %d rotated/scaled geometry cases.\n",geometry);
}
'''
src=head+(R/'source/shoulder_geometry_fy.inc').read_text()+(R/'source/shoulder_gestures_fw.inc').read_text()+(R/'source/shoulder_stow_fu.inc').read_text()+test
p=B/'shoulder_gestures_test.c';p.write_text(src)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout);(B/'shoulder_gestures_results.json').write_text(json.dumps({'passed':True,'result':r.stdout,'scope':'Production gesture functions with mocked engine/tracking state; no hardware session.'},indent=2))
