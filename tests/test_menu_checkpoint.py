from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text().replace('#include "desktop_window_ea.inc"','')
a=s.index('static i32 g_s26dySavedSDLW');b=s.index('static i32 h5755as_enter_native_ui_island',a)
head=r'''
#include <stdio.h>
#include <stdint.h>
typedef int i32;typedef unsigned u32;
typedef struct {int left,top,right,bottom;} H5754DRect;
static int g_h5755asUiIslandActive=1,g_h5755akPopupActive;
static void *g_h5755akWindow=(void*)1,*g_h5755asSDLWindow=(void*)2;
static int sw=2560,sh=1440,ok=1;
static H5754DRect client={0,0,2560,1440},outer={-2560,100,0,1578},g_h5755akSavedWindowRect;
static intptr_t g_h5755akSavedStyle;
static int g_h5755akSavedClientW,g_h5755akSavedClientH;
static u32 g_h5755akSnapshotValid;
static void size(void*w,int*x,int*y){*x=sw;*y=sh;}
static int rect(void*w,H5754DRect*r){*r=client;return ok;}
static int window(void*w,H5754DRect*r){*r=outer;return ok;}
static intptr_t style(void*w,int n){return 0x16cf0000;}
static void (*p_h5755asSDLGetWindowSize)(void*,int*,int*)=size;
static int (*p_h5754dGetClientRect)(void*,H5754DRect*)=rect;
static int (*p_h5755akGetWindowRect)(void*,H5754DRect*)=window;
static intptr_t (*p_h5755akGetWindowLongPtrA)(void*,int)=style;
#define ext_Log(...) ((void)0)
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
'''
body=r'''
int main(void){
 s26dy_checkpoint_menu_window();C(g_h5755akSnapshotValid&&g_h5755akSavedWindowRect.left==-2560&&g_s26dySavedSDLW==2560);
 // Move to a second monitor with a distinct coordinate origin and DPI ratio.
 outer=(H5754DRect){1920,-300,5776,1899};client.right=3840;client.bottom=2160;sw=2560;sh=1440;
 s26dy_checkpoint_menu_window();C(g_h5755akSavedWindowRect.left==1920&&g_h5755akSavedWindowRect.top==-300);
 C(g_h5755akSavedClientW==3840&&g_h5755akSavedClientH==2160&&g_s26dySavedSDLW==2560&&g_s26dySavedSDLH==1440);
 // Never replace the desktop snapshot with the oversized eye-rendering window.
 g_h5755akPopupActive=1;sw=5000;sh=5000;s26dy_checkpoint_menu_window();C(g_s26dySavedSDLW==2560);
 g_h5755akPopupActive=0;g_h5755asUiIslandActive=0;s26dy_checkpoint_menu_window();C(g_s26dySavedSDLW==2560);
 g_h5755asUiIslandActive=1;sw=0;sh=0;s26dy_checkpoint_menu_window();C(g_s26dySavedSDLW==2560);
 sw=3440;sh=1440;ok=0;s26dy_checkpoint_menu_window();C(g_s26dySavedSDLW==2560);
 ok=1;client.right=3440;client.bottom=1440;s26dy_checkpoint_menu_window();C(g_s26dySavedSDLW==3440&&g_h5755akSavedClientW==3440);
 puts("PASS menu geometry refresh: negative monitor origins, mixed logical/pixel sizes, ultrawide, minimized/API failures and gameplay isolation");return 0;
}
'''
B=R/'build';B.mkdir(exist_ok=True);p=B/'menu_checkpoint.c';p.write_text(head+s[a:b]+body)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
