from pathlib import Path
import re,sys,subprocess,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8')
def fn(name):
 m=re.search(r'(?m)^(?:static )?[^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s);assert m,name
 a=s.index('{',m.start());d=0
 for i in range(a,len(s)):
  d+=(s[i]=='{')-(s[i]=='}')
  if not d:return s[m.start():i+1]
header=r'''
#include <stdio.h>
#include <stdlib.h>
typedef unsigned u32;typedef int i32;
static void s26dy_checkpoint_menu_window(void){}
#define ext_Log(...) ((void)0)
static int checks;
static u32 g_s26cqStageReady=1,g_h5750yResolveFbo[2]={77,78};
static int g_h5750yResolveW=2912,g_h5750yResolveH=3112,ready=1;
static int h5750y_resolve_ready_for_eye(int eye){return ready&&eye==0;}
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
static u32 g_s26cpStartupUiDone,g_s26cpStartupUiAttempts,g_s26cpStartupUiDue,g_h5754dEndCalls;
static int g_h5755kGameplaySeen,g_s26wIntroActive,g_h5755asUiIslandActive,g_h5755akSnapshotValid;
static int g_h5755akSavedClientW,g_h5755akSavedClientH,g_h5754eMenuW,g_h5754eMenuH,g_h5754dPanelAnchorValid;
static void* g_h5755adGraphicsOwner=(void*)1;static u32 g_s26cqUiSyncPending,g_h5755asNativeUiScope;
static float g_h5754dPanelH,g_h5754dPanelW=2.0f;
static int replays;static void owner(void*p,u32 w,u32 h){(void)p;(void)w;(void)h;replays++;}
static void (*o_h5755adGraphicsOwnerSetSize)(void*,u32,u32)=owner;
static void s26cr_rebuild_native_menu(i32 w,i32 h){owner(g_h5755adGraphicsOwner,w,h);}
static int title=1,pauseState,result=1,calls,released,dw=3440,dh=1427;
static int h5754d_menu_wanted(void){return title;}static int h5754h_pause_active(void){return pauseState;}
static void h5755ag_resolve_query_apis(void){}
static void* dc(void){return (void*)1;}
static void* (*p_h5755agWglGetCurrentDC)(void)=dc;
static void h5755ak_cache_window_from_hdc(void*p){(void)p;}
static int h5755as_enter_native_ui_island(void){calls++;if(result)g_h5755asUiIslandActive=1;return result;}
static void h5754d_release_menu_inputs(void){released++;}
static int s26cb_flat_drawable_extent(int*w,int*h){*w=dw;*h=dh;return dw>0&&dh>0;}
'''
body=r'''
int main(void){
 g_h5755akSnapshotValid=1;g_h5755akSavedClientW=3440;g_h5755akSavedClientH=1427;
 g_h5754eMenuW=3440;g_h5754eMenuH=1440;g_h5754dPanelAnchorValid=1;
 s26cp_startup_native_ui();CHECK(calls==1&&g_s26cpStartupUiDone);CHECK(g_h5754eMenuH==1427);CHECK(!g_h5754dPanelAnchorValid&&released==1);
 for(int i=0;i<100;i++)s26cp_startup_native_ui();CHECK(calls==1);
 for(int island=0;island<2;island++)for(int t=0;t<2;t++)for(int p=0;p<2;p++){
  g_h5755asUiIslandActive=island;title=t;pauseState=p;u32 tex=99;int w=2528,h=2704;
  int expected=island&&(t||p);CHECK(s26cp_flat_submission(&tex,&w,&h)==expected);
  if(expected){CHECK(tex==77&&w==2912&&h==3112);}else CHECK(tex==99&&w==2528&&h==2704);
 }
 title=1;g_h5755asUiIslandActive=1;g_s26cqStageReady=0;u32 tex=99;int w=2528,h=2704;CHECK(!s26cp_flat_submission(&tex,&w,&h));CHECK(tex==99&&w==2528&&h==2704);
 g_s26cqStageReady=1;ready=0;CHECK(!s26cp_flat_submission(&tex,&w,&h));CHECK(tex==99);ready=1;
 g_s26cpStartupUiDone=0;g_h5755asUiIslandActive=0;g_h5754dEndCalls=60;g_h5754eMenuH=1440;result=0;
 s26cp_startup_native_ui();CHECK(!g_s26cpStartupUiDone&&g_h5754eMenuH==1440);
 int before=calls;s26cp_startup_native_ui();CHECK(calls==before);
 for(int i=0;i<20;i++){g_h5754dEndCalls+=60;s26cp_startup_native_ui();}CHECK(g_s26cpStartupUiAttempts==8);
 g_s26cpStartupUiAttempts=0;g_s26cpStartupUiDue=0;g_h5755kGameplaySeen=1;before=calls;s26cp_startup_native_ui();CHECK(calls==before);
 g_h5755kGameplaySeen=0;g_s26wIntroActive=1;s26cp_startup_native_ui();CHECK(calls==before);
 for(int island=0;island<2;island++)for(int t=0;t<2;t++)for(int p=0;p<2;p++){
  g_h5755asUiIslandActive=island;title=t;pauseState=p;g_s26cqUiSyncPending=1;
  dw=3440;dh=1440;g_h5754eMenuW=2560;g_h5754eMenuH=1440;g_h5754dPanelAnchorValid=1;
  int prev=replays; s26cq_reconcile_menu_extent();int expected=island&&(t||p);
  CHECK(replays==prev+expected);CHECK(!g_s26cqUiSyncPending);
  CHECK(g_h5754eMenuW==(expected?3440:2560));s26cq_reconcile_menu_extent();CHECK(replays==prev+expected);
 }
 title=1;g_h5755asUiIslandActive=1;dw=3440;dh=1440;g_h5754eMenuW=3440;g_h5754eMenuH=1440;g_s26cqUiSyncPending=1;
 int prev=replays;s26cq_reconcile_menu_extent();CHECK(replays==prev);
 g_s26cqUiSyncPending=1;dw=0;s26cq_reconcile_menu_extent();CHECK(replays==prev);
 printf("PASS %d startup UI ownership / staged-current-frame / flat-versus-stereo submission checks\n",checks);
}
'''
B=R/'build';B.mkdir(exist_ok=True);p=B/'menu_capture.c';p.write_text(header+fn('s26cp_startup_native_ui')+fn('s26cp_flat_submission')+fn('s26cq_reconcile_menu_extent')+body)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(B/'menu_capture.exe')],check=True)
r=subprocess.run([str(B/'menu_capture.exe')],capture_output=True,text=True);print(r.stdout+r.stderr)
(R/'audit').mkdir(exist_ok=True);(R/'audit/menu_capture_tests.json').write_text(json.dumps({'exit':r.returncode,'output':r.stdout+r.stderr,'scope':'Extracted production functions with mocked engine state. Not a headset visual test.'},indent=2))
raise SystemExit(r.returncode)
