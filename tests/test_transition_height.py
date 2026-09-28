"""Run extracted production functions, with mocked HPL/OpenXR state, not headset proof."""
from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text(encoding='utf-8')
def fn(name):
 m=re.search(r'(?m)^static [^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s);assert m,name
 a=s.index('{',m.start());depth=0
 for i in range(a,len(s)):
  depth+=(s[i]=='{')-(s[i]=='}')
  if not depth:return s[m.start():i+1]
header=r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned u32;typedef unsigned char u8;typedef int i32;
#define ext_Log(...) ((void)0)
#define H5755BH_GAMEPLAY_VR 1
#define H5755BH_PAUSE_QUAD 2
static u32 hook,viewdone,pristine,g_h5755bhPresentationState,g_h5755biPauseTokens,g_h5755biLifeRejects;
static u32 g_h5755aoPauseOwnerStart,g_h5755adOwnerCaptures,g_h5755aoPauseOwnerDelta;
static u32 g_h5755biResumePending,g_h5755anHaveLast,g_h5754hLastUiPollEndFrame;
static u32 g_h5754hPauseActive,g_h5754hPauseRequested,g_h5754hPauseImageReady,g_h5754dPanelAnchorValid;
static u32 g_h5755asUiIslandActive,g_h5755asUiEnterArmed;
static u8 g_h5754atEyeRouteActive,g_h5754atSavedCameraHookValid;
static u32 g_h5754atSavedCameraHook,g_h5754atEnterCount,g_h5754atExitCount,g_h5754atEyeQuadFrames;
static i32 head,g_h5754atSavedHeadMode;
static void* frustum;
static u32* p2_camera_hook_ptr(void){return &hook;}
static i32* p2_head_mode_ptr(void){return &head;}
static u32* p2_view_rot_done_ptr(void){return &viewdone;}
static u32* p2_pristine_valid_ptr(void){return &pristine;}
static void** p2_pristine_frustum_ptr(void){return &frustum;}
static void h5755bh_set_presentation(u32 x,const char*r){(void)r;g_h5755bhPresentationState=x;}
static float metric;
static u32 g_s26bzStanceMillimetres;
static float h5755ea_world_units_per_meter(void){return metric;}
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line %d\n",__LINE__);exit(1);}}while(0)
static int near(float a,float b){return fabsf(a-b)<.00002f;}
'''
body=r'''
int main(void){
 for(int cycle=0;cycle<100;cycle++){
  hook=1;head=0;g_h5755bhPresentationState=1;g_h5755asUiIslandActive=0;
  g_h5755adOwnerCaptures=cycle;g_h5755biResumePending=1;
  s26bz_begin_pause();CHECK(hook==0&&head==6&&g_h5754atEyeRouteActive);
  CHECK(g_h5755bhPresentationState==2&&g_h5754hPauseActive&&g_h5755asUiEnterArmed);
  CHECK(g_h5755aoPauseOwnerStart==(u32)cycle&&!g_h5755biResumePending);
  g_h5755biResumePending=1;s26bz_begin_pause();CHECK(!g_h5755biResumePending);
  CHECK(g_h5754atSavedCameraHook==1&&g_h5754atSavedHeadMode==0);
  h5754at_exit_startup_eye_route();CHECK(hook==1&&head==0&&!g_h5754atEyeRouteActive);
  h5754at_exit_startup_eye_route();CHECK(hook==1&&head==0);
 }
 g_h5755bhPresentationState=0;s26bz_begin_pause();CHECK(hook==1&&head==0);
 printf("PASS %u checks: shared pause lifecycle and repeated resume; height-offset wiring removed\n",checks);
}
'''
# Check wiring, not just helper math. Vector/throw conversions must stay translation-free.
assert 's26bz_begin_pause();return;' in fn('h5755bi_on_lifecycle_token')
assert 'h5754at_enter_startup_eye_route' not in fn('h5710_update_controller_buttons')
assert 'g_h5755asUiEnterArmed,0u' in fn('h5755bi_resume_post_endframe')
assert 's26bz_rig_height_offset' not in fn('tracking_delta_to_game')
assert 'world-scale-change' not in fn('s26bb_apply_world_scale')
assert 's26bz_rig_height_offset' not in (R/'source/shoulders_r.inc').read_text()
for name in ['h5755gh_apply_raw_head_translation','h5749d_apply_head_translation_detour']:
 assert 's26bz_apply_view_height' not in fn(name)
assert 's26bz_rig_height_offset' not in s
assert 'g_s26bzStanceMillimetres' not in s
assert 'HPL3VR_PublishScaleHeight' not in s
assert 'HPL3VR_PublishScaleHeight' not in (R/'runtime/script/modules/PlayerHandsHandler.hps').read_text()
B=R/'build';B.mkdir(exist_ok=True)
c=B/'transition_height_test.c';exe=B/'transition_height_test.exe'
c.write_text(header+'\n'.join(fn(n) for n in ['h5754at_enter_startup_eye_route','h5754at_exit_startup_eye_route','s26bz_begin_pause'])+body)
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True)
res=subprocess.run([str(exe)],capture_output=True,text=True);print(res.stdout+res.stderr)
(R/'audit').mkdir(exist_ok=True)
(R/'audit/transition_height_tests.json').write_text(json.dumps({'exit':res.returncode,'output':res.stdout+res.stderr,'scope':'Extracted production functions with mocked engine globals; no headset validation.'},indent=2))
raise SystemExit(res.returncode)
