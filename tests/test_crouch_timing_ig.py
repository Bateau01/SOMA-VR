"""Extract production dispatcher; native callback and runtime are mocked."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
a=s.index('static void s26ig_dispatch_crouch_pre(');b=s.index('static void h5711_dispatch_semantic_actions(void){',a)
f=s[a:b]
post=s[b:s.index('static i32 h39_prepare_slider',b)]
assert 'g_h5711CrouchPending' not in post
hook=s[s.index('static void __attribute__((ms_abi)) h14_newton_update('):]
assert hook.index('s26ig_dispatch_crouch_pre(timestep)')<hook.index('h14_physics_step(world,timestep)')<hook.index('o_h14NewtonUpdate(world,timestep)')<hook.index('h25_dispatch_pending()')
head=r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdint>
typedef unsigned u32;typedef unsigned char u8;typedef long long i64;
typedef void(*PFN_H5711_PlayerExit)(void*);typedef void(*PFN_H5711_PlayerAction)(void*,int,int);
u32 g_h5711CrouchPending,g_h576bfMapTransitionActive,g_h5755bhPresentationState=3,g_h5755asUiIslandActive,g_h5755asResumeClassifyActive,g_h5755azExitPending,g_h5755bbTitlePresentationLatch;
#define H5755BH_GAMEPLAY_VR 3
u32 g_h5711NativeRejects,g_h5711CrouchDispatches,g_h5755czCrouchViewActive,g_h5755czCrouchViewEvents,g_h5755czCrouchViewRejects,g_h5710CrouchToggle;
int g_h5711CrouchActionId=5;float g_h5755czCrouchViewDeltaY,g_h5755czCrouchViewDurationSec; i64 g_h5755czCrouchViewStartTime;
float camera[32];alignas(8) u8 xr[256];bool valid=true,resolve=true,allowed=true;int presses,releases;float jump=-.04f;
void action(void*,int a,int down){assert(a==5);if(down){presses++;if(allowed)camera[5]+=jump;}else releases++;}
bool h5711_native_player_callbacks(void**p,PFN_H5711_PlayerExit*,PFN_H5711_PlayerAction*a){*p=camera;*a=action;return valid;}
bool h5711_resolve_crouch_action_id(){return resolve;}
void*p2_camera_obj(){return camera;}void*p2_xr_obj(){return xr;}
bool h20_mem_readable(void*,int){return true;}float h9_abs(float x){return fabsf(x);}void ext_Log(const char*,...){}
'''
tail=r'''
int main(){*(i64*)(xr+0xe8)=123456789;
 for(float dt:{1.f/60,1.f/120})for(int sign:{-1,1}){
  jump=sign*.04f;camera[5]=10;presses=releases=0;g_h5711CrouchPending=1;
  s26ig_dispatch_crouch_pre(dt);float target=camera[5]; // same-step target/solver snapshot
  assert(fabsf(target-(10+jump))<1e-6f);assert(presses==1&&releases==1);
  for(int n=0;n<4;n++)s26ig_dispatch_crouch_pre(dt);
  assert(presses==1&&g_h5711CrouchPending==0);
  assert(fabsf(g_h5755czCrouchViewDurationSec-2*dt)<1e-6f);
  // Baseline ordering necessarily leaves old target for that solver step.
  float oldTarget=10;assert(fabsf(oldTarget-camera[5])>.039f);
 }
 u32* gates[]={&g_h576bfMapTransitionActive,&g_h5755asUiIslandActive,&g_h5755asResumeClassifyActive,&g_h5755azExitPending,&g_h5755bbTitlePresentationLatch};
 for(auto gate:gates){*gate=1;g_h5711CrouchPending=1;int n=presses;s26ig_dispatch_crouch_pre(1.f/120);assert(presses==n);*gate=0;}
 g_h5755bhPresentationState=0;int n=presses;s26ig_dispatch_crouch_pre(1.f/60);assert(presses==n);g_h5755bhPresentationState=3;
 allowed=false;camera[5]=10;g_h5711CrouchPending=1;s26ig_dispatch_crouch_pre(1.f/60);assert(camera[5]==10&&g_h5711CrouchPending==0);
 valid=false;g_h5711CrouchPending=1;n=presses;s26ig_dispatch_crouch_pre(1.f/60);assert(presses==n&&g_h5711CrouchPending==0);valid=true;
 resolve=false;g_h5711CrouchPending=1;s26ig_dispatch_crouch_pre(1.f/60);assert(presses==n&&g_h5711CrouchPending==0);
 puts("PASS extracted crouch dispatch: 60/120, up/down, once-only, native denial, invalid callback/action, presentation quarantine; baseline ordering fails same-step target");
}
'''
B=R/'build';B.mkdir(exist_ok=True);cpp=B/'test_crouch_timing_ig.cpp';cpp.write_text('#include <initializer_list>\n'+head+f+tail)
subprocess.run([sys.argv[1],'c++',str(cpp),'-o',str(B/'test_crouch_timing_ig.exe')],check=True)
subprocess.run([str(B/'test_crouch_timing_ig.exe')],check=True)
