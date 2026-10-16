"""Production accessibility functions, compiled with explicit engine boundaries.
Does not claim to replace headset or native-physics integration testing.
"""
from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1];src=(R/'source/accessibility_hd.inc').read_text()
def fn(name):
 a=re.search(r'static [^\n{};]+\b'+name+r'\([^;{}]*\)\s*\{',src).start();b=src.index('{',a);i=b+1;depth=1
 while depth:depth+=(src[i]=='{')-(src[i]=='}');i+=1
 return src[a:i]
header=r'''
#include <cmath>
#include <initializer_list>
#include <cstdio>
#include <cstdlib>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;using u64=unsigned long long;
void s26hf_diag(){}
int checks=0;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
float h9_abs(float f){return fabsf(f);}void zero_bytes(void*p,size_t n){memset(p,0,n);}
void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*sizeof(float));}
float h5755ea_world_units_per_meter(){return 1;}
struct H576BOTerminalSurface{float p0[3],uSpan[3],vSpan[3],normal[3];}g_h576boTerminalSurface;
int g_h576boTerminalSurfaceValid=1;
void* g_s26hdFixedOwner=nullptr;
void* h482_body_owner(const void*,void**){return nullptr;}
void p_s26hdWake(const void*,int){}
struct S26HDHit{const void* body;float t;};
struct S26HDPull{const void* body;void* wrapper;void* owner;float last[3],age;};
struct H14Scan{};
S26HDPull g_s26heOutline[2];u32 g_s26heOutlineStep[2],g_h14PhysicsSteps=9;
S26HDPull g_s26hgFocus[2];float g_s26hgScanAge[2];
S26HDPull g_s26hdPull[2];const void* g_s26hdHover[2];
const void* g_h14GripBody[2];int g_h25PendingValid[2],g_h30NativeMouseDown;
int g_s26hdRemoteEnabled=1,g_s26hdRemoteRange=2,g_s26hdLaserEnabled=1,g_s26CutsceneHandsHidden,g_h576bfMapTransitionActive;
int g_s26hdLaserHand=-1,g_h576boPointerDown,g_h576boPointerHand=-1,g_h576boEntryHand=-1,g_s26hdRemoteEntry;
u8 g_s26hdTriggerPrev[2];int g_lastTriggerActive[2]={1,1};float g_lastTrigger[2];
int running=1,pose[2]={1,1},terminal=0,paused=0,ready=1,fixedState=1;
int grabAllowed=0;int h5755fm_grab_gameplay_actions_allowed(){return grabAllowed;}
int freeState=1;int s26hd_free_state(){return freeState;}
int p_s26hdRay=1,grabs=0,writes=0,beams=0,haptics=0,presses=0,ups=0,interacts=0,contact=0,touch=-1;
int live=1,loose=1,latch=0,aim=1,target=1,moveOK=1,buttonOK=1;
const void* body=(void*)0x100;void* wrapper=(void*)0x200;void* owner=(void*)0x300;
S26HDHit rayResult={body,.5f};float velocity[4],gap=.8f;
S26HDHit s26hd_ray(const float*,const float*){return rayResult;}
int s26hd_live(S26HDPull*,float){return live;}
int s26hd_loose(const void*b,void**w,void**o,float*m){*w=wrapper;*o=owner;*m=1;return loose&&b==body;}
int s26hd_aim(int,float*a,float*d){a[0]=a[1]=0;a[2]=1;d[0]=d[1]=0;d[2]=-1;return aim;}
const void* s26hg_select(int,const float*a,const float*d,float range,float,float,float*p,void**w,void**o){float mass;auto hit=rayResult;if(!hit.body||hit.t*range<.18f||!s26hd_loose(hit.body,w,o,&mass))return nullptr;for(int i=0;i<3;i++)p[i]=a[i]+d[i]*range*hit.t;return hit.body;}
int p2_xr_running(){return running;}int visual_pose_valid(int h){return pose[h];}
int h5730_exact_terminal_state(void*,int,void*,int){return terminal;}
int h15_grip_center_world(int,const float*,float*p){p[0]=p[1]=p[2]=0;return 1;}
int h14_point_to_body(const void*,const float*,float*g,float*p){*g=gap;p[0]=gap;p[1]=p[2]=0;return 1;}
void p_h14GetMatrix(const void*,float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;m[12]=gap;}
void p_h14GetVelocity(const void*,float*v){memcpy(v,velocity,16);}
void p_h14SetVelocity(const void*,const float*v){memcpy(velocity,v,16);writes++;}
void s26hd_beam(int,const float*,const float*,u32){beams++;}
int h560_try_loose_latch(int h,const void*b,const H14Scan*,const float*,int){if(latch){grabs++;g_h14GripBody[h]=b;}return latch;}
enum{H576AC_HAPTIC_READY=1,H576AC_HAPTIC_CONFIRM=2,H576BO_TERMINAL_ICON=17};
void h576ac_queue_haptic(int,int){haptics++;}
int h5754h_pause_active(){return paused;}
int s26hd_fixed_state(){return terminal&&fixedState;}
struct H25TString{char storage[16];u64 size,capacity;};
using PFN_H25_OnInteract=u64(*)(void*,int,void*,const float*,H25TString*);
u64 interact(void*,int,void*,const float*,H25TString*){CHECK(g_s26hdRemoteEntry==1);interacts++;return 1;}
int s26hd_target(const void*b,void**w,void**o,int*i,void**on){*w=wrapper;*o=owner;*i=17;*on=(void*)interact;return b&&target;}
void h576bo_release_pointer(int,const char*){if(g_h576boPointerDown)ups++;g_h576boPointerDown=0;g_h576boPointerHand=-1;}
int h576bo_push_motion(float,float){return moveOK;}
int h576bo_push_button(int d){if(d)presses++;return buttonOK;}
int h576bo_terminal_tip(int h,float*u,float*v,float*p,float*r){*u=*v=.5f;*p=0;*r=.01f;return h==touch;}
#define H576BP_SURFACE_CAPTURE_M .002f
'''
header+=r'''
int p_h14WorldAABB=1,g_h14NewtonWorld=1;int g_h5755bhPresentationState=2;enum{H5755BH_GAMEPLAY_VR=2};u32 g_s26hiOutlinePosts,g_s26hiOutlinePhaseReject;int outlines=0;void s26he_submit_edge(void*){outlines++;}
'''
body=r'''
void reset(){
 s26hd_reset();g_s26hdTriggerPrev[0]=g_s26hdTriggerPrev[1]=0;
 g_s26hdRemoteEnabled=g_s26hdLaserEnabled=running=ready=live=loose=aim=target=moveOK=buttonOK=1;
 grabAllowed=0;g_s26CutsceneHandsHidden=g_h576bfMapTransitionActive=g_h30NativeMouseDown=terminal=paused=0;
 g_h25PendingValid[0]=g_h25PendingValid[1]=0;g_h14GripBody[0]=g_h14GripBody[1]=nullptr;
 freeState=1;g_lastTriggerActive[0]=g_lastTriggerActive[1]=1;pose[0]=pose[1]=1;g_s26hdRemoteRange=2;rayResult={body,.5f};gap=.8f;latch=0;
 memset(velocity,0,sizeof velocity);grabs=writes=beams=haptics=presses=ups=interacts=0;
 g_lastTrigger[0]=g_lastTrigger[1]=0;touch=-1;g_h576boPointerDown=0;g_h576boEntryHand=-1;fixedState=1;
 g_h576boTerminalSurface={{-.5f,.5f,0},{1,0,0},{0,-1,0},{0,0,1}};
}
int main(){float m[16]={0};H14Scan scan;
 // Release/hold without a fresh edge cannot start a pull. Hover is read-only.
 reset();s26hd_grab(0,m,&scan,0,0,.016f);CHECK(!g_s26hdPull[0].body&&writes==0&&haptics==1);
 s26hd_grab(0,m,&scan,0,0,.016f);CHECK(haptics==1);
 s26hd_grab(0,m,&scan,0,1,.016f);CHECK(!g_s26hdPull[0].body);
 s26hd_grab(0,m,&scan,1,1,.016f);CHECK(g_s26hdPull[0].body==body&&writes==0);
 s26hd_grab(0,m,&scan,0,1,1.f/120);CHECK(writes==1&&fabsf(velocity[0])<=.25001f&&grabs==0);
 s26hd_grab(0,m,&scan,0,0,.016f);CHECK(!g_s26hdPull[0].body&&writes==1);
 // Lifetime, obstruction, eligibility, pause/cutscene, other ownership guards.
 for(int bad=0;bad<12;bad++){reset();s26hd_grab(0,m,&scan,1,1,.016f);
  if(bad==0)live=0;if(bad==1)loose=0;if(bad==2)g_s26hdPull[0].age=4;
  if(bad==3)g_s26hdRemoteEnabled=0;if(bad==4)g_s26CutsceneHandsHidden=1;
  if(bad==5)pose[0]=0;if(bad==6)g_h14GripBody[0]=(void*)9;if(bad==7)terminal=1;
  if(bad==8)g_h25PendingValid[0]=1;if(bad==9)g_h30NativeMouseDown=1;
  if(bad==10)rayResult={(void*)9,.2f};if(bad==11)g_s26hdLaserHand=0;
  s26hd_grab(0,m,&scan,0,1,.016f);CHECK(!g_s26hdPull[0].body&&writes==0&&grabs==0);
 }
 reset();s26hd_grab(0,m,&scan,1,1,.016f);s26hd_grab(1,m,&scan,1,1,.016f);CHECK(!g_s26hdPull[1].body);
 gap=.02f;latch=1;s26hd_grab(0,m,&scan,0,1,.016f);CHECK(grabs==1&&!g_s26hdPull[0].body&&writes==0);
 // Plane intersections: center, corners, misses, backwards, parallel, skewed.
 reset();rayResult={nullptr,1};float a[3]={0,0,1},d[3]={0,0,-1},hit[3],u,v;
 CHECK(s26hd_screen_ray(a,d,3,&u,&v,hit)&&fabsf(u-.5f)<1e-6f&&fabsf(v-.5f)<1e-6f);
 for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++){a[0]=x*.5f;a[1]=y*.5f;CHECK(s26hd_screen_ray(a,d,3,&u,&v,hit));}
 a[0]=.6f;CHECK(!s26hd_screen_ray(a,d,3,&u,&v,hit));a[0]=a[1]=0;
 CHECK(!s26hd_screen_ray(a,d,.5f,&u,&v,hit));d[2]=1;CHECK(!s26hd_screen_ray(a,d,3,&u,&v,hit));
 d[2]=0;CHECK(!s26hd_screen_ray(a,d,3,&u,&v,hit));d[2]=-1;
 rayResult={body,.5f};CHECK(!s26hd_screen_ray(a,d,3,&u,&v,hit));rayResult={body,.99f};CHECK(s26hd_screen_ray(a,d,3,&u,&v,hit));
 rayResult={nullptr,1};g_h576boTerminalSurface.uSpan[1]=.2f;
 CHECK(s26hd_screen_ray(a,d,3,&u,&v,hit)&&fabsf(u-.5f)<1e-6f&&fabsf(v-.6f)<1e-6f);
 // First trigger enters native terminal once, without clicking its UI yet.
 reset();g_lastTrigger[1]=1;s26hd_step(.016f);CHECK(interacts==1&&presses==0&&!g_s26hdRemoteEntry);
 s26hd_step(.016f);CHECK(interacts==1);
 // Fixed GUI hover, fresh press/release, cancellation and physical priority.
 reset();terminal=1;rayResult={nullptr,1};s26hd_step(.016f);CHECK(g_s26hdLaserHand==1&&presses==0);
 g_lastTrigger[1]=1;s26hd_step(.016f);CHECK(g_h576boPointerDown&&presses==1);
 s26hd_step(.016f);CHECK(presses==1);g_lastTrigger[1]=0;s26hd_step(.016f);CHECK(!g_h576boPointerDown&&ups==1);
 g_lastTrigger[1]=1;s26hd_step(.016f);CHECK(presses==2);touch=0;s26hd_step(.016f);CHECK(g_s26hdLaserHand==-1&&!g_h576boPointerDown&&ups==2);
 reset();terminal=1;rayResult={nullptr,1};g_h576boPointerDown=1;s26hd_step(.016f);CHECK(g_s26hdLaserHand==-1&&presses==0&&ups==0);
 reset();terminal=1;rayResult={nullptr,1};g_lastTrigger[1]=1;s26hd_step(.016f);CHECK(presses==1);paused=1;s26hd_step(.016f);CHECK(ups==1&&g_s26hdLaserHand==-1);
 reset();g_s26hdRemoteEnabled=g_s26hdLaserEnabled=0;g_h576boPointerDown=1;s26hd_step(.016f);CHECK(ups==0&&g_h576boPointerDown&&interacts==0&&writes==0);
 // Outline publication shares exact target, clears on cancellation/handoff,
 // rejects stale or destroyed bodies, and deduplicates two-hand nominations.
 reset();s26hd_grab(0,m,&scan,0,0,.016f);CHECK(g_s26heOutline[0].body==body);
 outlines=0;s26he_outline_postupdate();CHECK(outlines==1);
 s26hd_grab(1,m,&scan,0,0,.016f);outlines=0;s26he_outline_postupdate();CHECK(outlines==1);
 g_s26heOutlineStep[0]--;g_s26heOutlineStep[1]--;outlines=0;s26he_outline_postupdate();CHECK(outlines==1);
 for(int why=0;why<10;why++){
  reset();outlines=0;s26hd_grab(0,m,&scan,0,0,.016f);
  if(why==0)live=0;if(why==1)g_s26heOutlineStep[0]-=2;
  if(why==2)paused=1;if(why==3)g_h576bfMapTransitionActive=1;
  if(why==4)g_s26CutsceneHandsHidden=1;if(why==5)g_h14GripBody[0]=body;
  if(why==6)pose[0]=0;if(why==7)g_s26hdRemoteEnabled=0;
  if(why==8)g_h25PendingValid[0]=1;if(why==9)g_s26hdLaserHand=0;
  s26he_outline_postupdate();CHECK(outlines==0);
 }
 reset();s26hd_grab(0,m,&scan,1,1,.016f);gap=.02f;latch=1;
 s26hd_grab(0,m,&scan,0,1,.016f);CHECK(!g_s26heOutline[0].body);
 reset();s26hd_grab(0,m,&scan,0,0,.016f);rayResult={nullptr,1};
 s26hd_grab(0,m,&scan,0,0,.016f);CHECK(!g_s26heOutline[0].body);
 reset();s26hd_grab(0,m,&scan,0,0,.016f);s26hd_reset();CHECK(!g_s26heOutline[0].body);

 // Additional loss/cancellation paths, both hands at both physics rates.
 for(int hand=0;hand<2;hand++)for(int hz: {60,120})for(int reason=0;reason<8;reason++){
  reset();g_h576boEntryHand=hand;terminal=1;rayResult={nullptr,1};g_lastTrigger[hand]=1;
  s26hd_step(1.f/hz);CHECK(g_h576boPointerDown&&presses==1);
  if(reason==0)paused=1;
  if(reason==1)g_h576bfMapTransitionActive=1;
  if(reason==2)g_s26CutsceneHandsHidden=1;
  if(reason==3)running=0;
  if(reason==4)pose[0]=pose[1]=0;
  if(reason==5)aim=0;
  if(reason==6)rayResult={(void*)9,.1f};
  if(reason==7){terminal=0;freeState=0;}
  s26hd_step(1.f/hz);CHECK(!g_h576boPointerDown&&ups==1&&g_s26hdLaserHand==-1);
  s26hd_step(1.f/hz);CHECK(ups==1&&presses==1);
 }
 // No motion writes across invalid timestep, expired ownership or held input.
 for(int hand=0;hand<2;hand++)for(int hz: {60,120}){
  reset();s26hd_grab(hand,m,&scan,1,1,1.f/hz);CHECK(g_s26hdPull[hand].body);
  s26hd_grab(hand,m,&scan,0,1,0);CHECK(!g_s26hdPull[hand].body&&writes==0);
  s26hd_grab(hand,m,&scan,0,1,1.f/hz);CHECK(!g_s26hdPull[hand].body);
  s26hd_grab(hand,m,&scan,0,0,1.f/hz);s26hd_grab(hand,m,&scan,1,1,1.f/hz);
  CHECK(g_s26hdPull[hand].body);paused=1;s26hd_step(1.f/hz);CHECK(!g_s26hdPull[hand].body&&writes==0);
 }
 // Ineligible/invalid aim cannot nominate an outline or begin a pull.
 for(int reason=0;reason<5;reason++){
  reset();if(reason==0)aim=0;if(reason==1)freeState=0;if(reason==2)loose=0;
  if(reason==3)rayResult={nullptr,1};if(reason==4)rayResult={body,.01f};
  s26hd_grab(0,m,&scan,1,1,.016f);CHECK(!g_s26hdPull[0].body&&!g_s26heOutline[0].body&&writes==0&&grabs==0);
 }
 // Each free hand can pull while the other owns the validated native Grab.
 for(int h=0;h<2;h++){
  reset();freeState=0;grabAllowed=1;g_h30NativeMouseDown=1;g_h14GripBody[1-h]=(void*)99;
  s26hd_grab(h,m,&scan,1,1,.016f);CHECK(g_s26hdPull[h].body);CHECK(g_h14GripBody[1-h]==(void*)99);
  outlines=0;s26he_outline_postupdate();CHECK(outlines==1);
  grabAllowed=0;s26hd_grab(h,m,&scan,0,1,.016f);CHECK(!g_s26hdPull[h].body); // real scripted state cancels
  reset();freeState=0;grabAllowed=1;g_h30NativeMouseDown=1;g_s26hdRemoteEnabled=0;
  s26hd_grab(h,m,&scan,1,1,.016f);CHECK(!g_s26hdPull[h].body);
 }
 printf("PASS %d accessibility boundary checks\n",checks);
}
'''
header+=r'''
u8 g_s26hlReadStage[2],g_s26hlHeld[2];u32 g_s26hlReadId[2];float g_s26hlReadPoint[2][3];
int g_s26hlInteractionEnabled;S26HDPull g_s26hlInteraction[2];
void s26hl_interaction_step(const u8*){}
struct S26HLAssembly{const void* body[32];u32 count;float mass;};
int s26hl_assembly(const void*b,void*,S26HLAssembly*a){a->count=1;a->body[0]=b;a->mass=1;return 1;}
int s26hl_same_free_prop(const void*b,const void*hit,void*){return !hit||hit==b;}
'''
code=header+fn('s26hk_remote_state')+fn('s26hk_remote_native_busy')+fn('s26he_nominate')+fn('s26he_outline_postupdate')+fn('s26hd_reset')+fn('s26hd_screen_ray')+fn('s26hg_pull_velocity')+fn('s26hd_grab')+fn('s26hd_step')+body
# Globals used only by the real renderer are reset here as well.
code=code.replace('int checks=0;','int checks=0;u32 g_s26hdBeamKind[2];')
B=R/'build';cpp=B/'accessibility_hd.cpp';exe=B/'accessibility_hd.exe';cpp.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(cpp),'-o',str(exe)],check=True)
v=subprocess.run([str(exe)],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/accessibility_hd.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production functions with mocked engine boundaries; no headset claim.'},indent=2))
raise SystemExit(v.returncode)
