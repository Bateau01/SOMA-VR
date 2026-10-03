from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('static void s26cq_reconcile_menu_extent(void){');b=s.index('\n}',a)+2
head=r"""
#include <stdio.h>
#include <stdlib.h>
typedef unsigned u32;typedef int i32;
static u32 g_s26cqUiSyncPending,g_h5755asUiIslandActive=1,g_h5755asNativeUiScope;
static int title=1,pauseState,dw=1920,dh=1080,g_h5754eMenuW=1920,g_h5754eMenuH=1080,calls;
static int g_h5754dPanelAnchorValid=1;
static float g_h5754dPanelH,g_h5754dPanelW=1.5f;
static void *g_h5755adGraphicsOwner=(void*)1,*o_h5755adGraphicsOwnerSetSize=(void*)1;
static int h5754d_menu_wanted(void){return title;}
static int h5754h_pause_active(void){return pauseState;}
static int s26cb_flat_drawable_extent(int*w,int*h){*w=dw;*h=dh;return dw>0&&dh>0;}
static void s26cr_rebuild_native_menu(int w,int h){if(!g_h5755asNativeUiScope||w!=dw||h!=dh)abort();calls++;}
static void s26dy_checkpoint_menu_window(void){}
#define ext_Log(...) ((void)0)
#define CHECK(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
"""
body=r"""
int main(void){
 s26cq_reconcile_menu_extent();CHECK(calls==0);
 dw=3440;dh=1440;s26cq_reconcile_menu_extent();CHECK(calls==1&&g_h5754eMenuW==3440&&!g_h5755asNativeUiScope);
 for(int i=0;i<1000;i++)s26cq_reconcile_menu_extent();CHECK(calls==1);
 title=0;pauseState=1;dw=2560;s26cq_reconcile_menu_extent();CHECK(calls==2);
 g_h5755adGraphicsOwner=0;dw=1920;dh=1080;s26cq_reconcile_menu_extent();CHECK(calls==2&&g_h5754eMenuW==2560);
 g_h5755adGraphicsOwner=(void*)1;s26cq_reconcile_menu_extent();CHECK(calls==3&&g_h5754eMenuW==1920);
 dw=0;dh=0;s26cq_reconcile_menu_extent();CHECK(calls==3);
 dw=3840;dh=2160;pauseState=0;s26cq_reconcile_menu_extent();CHECK(calls==3);
 title=1;g_h5755asUiIslandActive=0;s26cq_reconcile_menu_extent();CHECK(calls==3);
 g_h5755asUiIslandActive=1;s26cq_reconcile_menu_extent();CHECK(calls==4);
 puts("PASS external drawable resize, ultrawide, pause, stable no-op, delayed owner, minimized and gameplay isolation");return 0;
}
"""
p=R/'build/menu_resize.c';p.parent.mkdir(exist_ok=True);p.write_text(head+s[a:b]+body)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True);subprocess.run([str(p.with_suffix('.exe'))],check=True)
