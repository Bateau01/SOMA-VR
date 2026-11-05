"""Compiled exact detours with synthetic GUI identity. Tests early unregistered forwarding, not real widget pixels."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text();c=(r/'source/terminal_cursor_an.inc').read_text()
def fn(text,name):
 start=text.index('static ',text.index(name)-60);a=text.index('{',text.index(name));b=a+1;depth=1
 while depth:
  depth+=(text[b]=='{')-(text[b]=='}');b+=1
 return text[start:b]
code=r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;typedef unsigned long long u64;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
int g_s26GuiReady=1,g_s26GuiOwnFrame,g_s26GuiCapture,g_s26GuiHavePos,g_s26anCursorReady=1;
int g_h576mScriptRuntimePublished=0,g_h576bfMapTransitionActive=0;
void*g_s26TerminalImGui;struct{float remaining;}g_s26hsTouch;char g_s26GuiQueue[64];
int calls,registered,gate;void*seen;const float*seenPos;const float*seenRel;
int h576bo_terminal_event_gate(){return gate;}int p2_xr_on(){return 0;}int p2_xr_running(){return 0;}
int h20_mem_readable(void*p,unsigned n){return p!=0;}void zero_bytes(void*p,unsigned n){memset(p,0,n);}
void s26hs_touch_consumed(void*p,int x){}
static void __attribute__((ms_abi)) forward_action(void*s,int a,u8 d,u8 e){C(a==1&&d==1&&e==1);seen=s;calls++;}
static void __attribute__((ms_abi)) motion(void*s,const float*p,const float*r){seen=s;seenPos=p;seenRel=r;calls++;}
static void __attribute__((ms_abi)) end(void*s){seen=s;calls++;}
static void __attribute__((ms_abi)) mouse(void*s,void*g,const float*p,const float*r){seen=s;seenPos=p;seenRel=r;calls++;}
static u64 __attribute__((ms_abi)) legacy(void*s){seen=s;calls++;return 91;}
#define p_s26GuiAction forward_action
#define o_s26GuiMotion motion
#define o_s26anEnd end
#define o_s26anMouse mouse
#define o_s26anLegacyMouse legacy
"""
a=c.index('static const void* g_s26bvGui[');b=c.index('static void s26an_cursor_install')
code+=c[a:b]
code+=fn(s,'s26_gui_action_detour(')+fn(s,'s26_gui_motion_detour(')
code+=r"""
int main(){char menu[0x800]={0};float p[2]={.2f,.4f},v[2]={1,2};
 // Hooks installed at startup must forward unchanged before any terminal registers.
 s26_gui_action_detour(menu,1,1,1);C(calls==1&&seen==menu);
 s26_gui_motion_detour(menu,p,v);C(calls==2&&seenPos==p&&seenRel==v);
 s26an_gui_end(menu);C(calls==3);s26an_gui_mouse(menu,0,p,v);C(calls==4&&seenPos==p&&seenRel==v);
 C(s26an_legacy_mouse(menu)==91&&calls==5);C(g_s26bvGuiCount==0);
 // Registration still happens only on explicit native script handshake.
 g_s26GuiCapture=2;s26_gui_motion_detour(menu,p,v);C(g_s26bvGuiCount==1&&calls==5);g_s26GuiCapture=0;
 s26_gui_motion_detour(menu,p,v);C(calls==6);
 puts("PASS: five early detours preserve arguments/return and exact call count; registration needs handshake");
}
"""
b=r/'build/cpu16-early-gui';b.mkdir(exist_ok=True);(b/'test.c').write_text(code)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu16-early-gui.json').write_text(json.dumps({'scope':__doc__,'exit':x.returncode,'output':x.stdout+x.stderr},indent=2));raise SystemExit(x.returncode)
