"""Extract production functions; engine calls are mocked, not headset verification."""
from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
def fn(name):
 m=re.search(r'(?m)^(?:static )?[^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s);assert m,name
 a=s.index('{',m.start());d=0
 for i in range(a,len(s)):
  d+=(s[i]=='{')-(s[i]=='}')
  if not d:return s[m.start():i+1]
header=r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned u32;typedef unsigned char u8;typedef int i32;
typedef struct{float x,y,z,w;}XrQuaternionf;
typedef struct{float x,y,z;}XrVector3f;
typedef struct{XrQuaternionf orientation;XrVector3f position;}XrPosef;
#define ext_Log(...) ((void)0)
#define ext_Sqrtf sqrtf
#define H5755BH_TITLE_FLAT 0
#define H5755BH_GAMEPLAY_VR 1
static u32 checks,commits,gates,presentation,g_h5755bbTitlePresentationLatch;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
static u32 g_h5755asNativeUiScope,g_s26caMenuApplyDepth,g_s26caMenuSavedScope,g_s26caMenuApplyLogs;
static i32 nw,nh,g_s26caMenuSavedW,g_s26caMenuSavedH;
static volatile i32* p2_native_w_ptr(void){return &nw;}
static volatile i32* p2_native_h_ptr(void){return &nh;}
static u32 g_h5755biResumePending,g_s26vDeathActive,g_s26vDeathLoading,g_h5755asUiEnterArmed;
static u32 g_h5754wCaptureActive,g_h5754zCaptureActive,g_h5755anHaveLast;
static u32 g_h5754hPauseActive,g_h5754hPauseRequested,g_h5754hPauseImageReady,g_h5754tLastTargetEnd,g_h5754hPauseResumes;
static u32 g_h5755asResumeClassifyActive,g_h5755asResumeStableCount,g_s26wIntroActive;
static u32 g_s26cbIntroHandoffPending,g_s26cbIntroEndMapEnters,g_h576bfMapEnters;
static u32 g_h576bhMapReadySeen,g_h14PhysicsSteps,g_h576bhMapReadyStep;
static i32 dw,dh;static void* window;
static void h5755as_resolve_sdl_window_api(void){}
static void* get_window(void){return window;}
static void drawable(void* w,i32* x,i32* y){(void)w;*x=dw;*y=dh;}
static void* (*p_h5755asSDLGLGetCurrentWindow)(void)=get_window;
static void (*p_h5755asSDLGLGetDrawableSize)(void*,i32*,i32*)=drawable;
static void* dc;static void* g_h5755akWindow;
static void h5755ag_resolve_query_apis(void){}
static void* get_dc(void){return dc;}
static void* from_dc(void* v){return v?window:0;}
static void* (*p_h5755agWglGetCurrentDC)(void)=get_dc;
static void* (*p_h5755sWindowFromDC)(void*)=from_dc;
static u32 g_h5755adRefreshArmed,g_h5755atExactGameplayOwnerRefresh,g_h5755biResumeCommits;
static u32 g_h5754pResumeStickNeutralGate,g_h5754pResumeNeutralArms,g_h5735MoveWasNonzero,g_h5747LookWasNonzero;
static void h5754w_release_capture(int x){(void)x;g_h5754wCaptureActive=0;}
static void h5754z_release_capture(int x){(void)x;g_h5754zCaptureActive=0;}
static void h5754at_exit_startup_eye_route(void){}
static void h5755bh_set_presentation(u32 x,const char*r){(void)r;presentation=x;}
static void h5753c_gate_menu_camera(const char*r,int x){(void)r;(void)x;gates++;}
static i32 h5755as_commit_gameplay_resume(void){commits++;return 1;}
'''
body=r'''
int main(void){
 for(int oldScope=0;oldScope<2;oldScope++)for(int k=0;k<100;k++){
  nw=2688;nh=2880;g_h5755asNativeUiScope=oldScope;
  s26ca_menu_apply_scope(1);CHECK(g_h5755asNativeUiScope==1);
  nw=1920;nh=1080;s26ca_menu_apply_scope(1);
  nw=1280;nh=720;s26ca_menu_apply_scope(0);
  CHECK(g_h5755asNativeUiScope==1&&nw==1280&&nh==720);
  s26ca_menu_apply_scope(0);
  CHECK(g_h5755asNativeUiScope==(u32)oldScope&&nw==2688&&nh==2880);
  s26ca_menu_apply_scope(0);CHECK(nw==2688&&g_s26caMenuApplyDepth==0);
 }
 u8 xr[512]={0};XrPosef a={{0,0,0,1},{-.03f,1.7f,0}},b={{0,0,0,1},{.03f,1.7f,0}},l,r;
 memcpy(xr+0x8c,&a,sizeof(a));memcpy(xr+0xbc,&b,sizeof(b));
 CHECK(!s26ca_menu_eye_poses(xr,&l,&r));xr[0x78]=1;CHECK(!s26ca_menu_eye_poses(xr,&l,&r));
 xr[0xa8]=1;CHECK(s26ca_menu_eye_poses(xr,&l,&r));
 ((XrPosef*)(xr+0xbc))->position.y=NAN;CHECK(!s26ca_menu_eye_poses(xr,&l,&r));
 memcpy(xr+0xbc,&b,sizeof(b));
 for(int deg=-180;deg<=180;deg++){
  float t=deg*.0174532925f;
  XrPosef p={{0,sinf(t*.5f),0,cosf(t*.5f)},{0,1.7f,0}};
  XrVector3f n=h5754d_q_rotate_vec(p.orientation,(XrVector3f){0,0,1});
  a.position=(XrVector3f){2*n.x,1.7f,2*n.z};b=a;
  CHECK(!s26ca_panel_behind_viewer(&p,&a,&b));
  a.position=(XrVector3f){-2*n.x,1.7f,-2*n.z};b=a;
  CHECK(s26ca_panel_behind_viewer(&p,&a,&b));
 }
 for(int i=0;i<100;i++){
  g_s26wIntroActive=1;g_h5755biResumePending=1;g_h5755asUiEnterArmed=1;presentation=2;
  g_h5755adRefreshArmed=1;g_h5755atExactGameplayOwnerRefresh=1;
  h5755bi_resume_post_endframe();
  CHECK(presentation==0&&!g_h5755asUiEnterArmed&&!g_h5755biResumePending);
  CHECK(!g_h5755adRefreshArmed&&!g_h5755atExactGameplayOwnerRefresh&&commits==0);
 }
 CHECK(gates==100);
 g_s26wIntroActive=0;g_s26cbIntroHandoffPending=1;g_h5755biResumePending=1;
 h5755bi_resume_post_endframe();CHECK(presentation==0&&commits==0);
 for(u32 enter=0;enter<2;enter++)for(u32 ready=0;ready<2;ready++)for(u32 step=0;step<20;step++){
  g_h576bfMapEnters=enter;g_h576bhMapReadySeen=ready;g_h576bhMapReadyStep=100;g_h14PhysicsSteps=100+step;
  CHECK(s26cb_intro_destination_ready()==(enter&&ready&&step>=3));
 }
 g_s26cbIntroHandoffPending=0;CHECK(s26cb_intro_destination_ready());
 g_h5755bbTitlePresentationLatch=1;g_h5755biResumePending=1;
 h5755bi_resume_post_endframe();CHECK(presentation==0&&commits==0);
 g_h5755bbTitlePresentationLatch=0;
 dc=(void*)2;window=(void*)3;g_h5755akWindow=0;CHECK(s26cb_menu_render_window()==window);
 g_h5755akWindow=(void*)4;CHECK(s26cb_menu_render_window()==window);
 dc=0;CHECK(s26cb_menu_render_window()==g_h5755akWindow);
 g_h5755akWindow=0;CHECK(s26cb_menu_render_window()==0);
 int x=5,y=6;window=0;CHECK(!s26cb_flat_drawable_extent(&x,&y)&&x==5&&y==6);
 window=(void*)1;dw=0;dh=1080;CHECK(!s26cb_flat_drawable_extent(&x,&y));
 for(int width=640;width<=7680;width+=320)for(int height=480;height<=4320;height+=240){
  dw=width;dh=height;CHECK(s26cb_flat_drawable_extent(&x,&y)&&x==width&&y==height);
 }
 g_s26wIntroActive=0;g_h5755biResumePending=1;h5755bi_resume_post_endframe();CHECK(presentation==1&&commits==1);
 g_s26vDeathActive=1;g_h5755biResumePending=1;h5755bi_resume_post_endframe();CHECK(commits==1);
 printf("PASS %u checks: nested title/pause settings scope, stale/invalid eye poses, panel front/back, intro resume and ordinary gameplay resume\n",checks);
}
'''
menu=(R/'runtime/script/modules/MenuHandler.hps').read_text()
apply=menu[menu.index('void ApplySettings(bool'):menu.index('void DiscardSettings()')]
assert apply.index('"VRMENUC", "", "B"')<apply.index('mbRestartWarning = cLux_ApplyUserConfig()')<apply.index('"VRMENUC", "", "E"')
assert 'if(!g_s26caMenuApplyDepth&&bw>0&&bh>0)' in fn('h5750x_set_screen_size_detour')
ref=(R/'source/reference_q.inc').read_text()
assert 'g_h5754dPanelAnchorValid=0;h5754d_release_menu_inputs();' in ref
B=R/'build';B.mkdir(exist_ok=True)
c=B/'menu_recovery.c';exe=B/'menu_recovery.exe'
c.write_text(header+'\n'.join(fn(n) for n in ['s26ca_menu_apply_scope','h5754d_q_rotate_vec','s26ca_menu_eye_poses','s26ca_panel_behind_viewer','h5755bi_resume_post_endframe','s26cb_intro_destination_ready','s26cb_flat_drawable_extent','s26cb_menu_render_window'])+body)
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True)
result=subprocess.run([str(exe)],capture_output=True,text=True)
(R/'audit').mkdir(exist_ok=True)
(R/'audit/menu_recovery_tests.json').write_text(json.dumps({'exit':result.returncode,'output':result.stdout+result.stderr,'scope':'Extracted production functions and static call wiring; mocked engine state, not visual/headset proof.'},indent=2))
print(result.stdout+result.stderr);raise SystemExit(result.returncode)
