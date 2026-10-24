"""Production cursor registration/filter with synthetic GUI objects, not pixel proof."""
from pathlib import Path
import argparse,subprocess,json
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--source',type=Path);a=p.parse_args()
r=Path(__file__).resolve().parents[1]
s=(a.source or r/'source/terminal_cursor_an.inc').read_text()
start=s.index('static const void* g_s26bvGui[');end=s.index('static void __attribute__((ms_abi)) s26an_gui_end',start)
code=r'''
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
int g_s26anCursorReady=1,g_h576mScriptRuntimePublished=1,g_h576bfMapTransitionActive=0,on=1,running=1;
int h20_mem_readable(void*p,unsigned n){return p!=0;}
int p2_xr_on(){return on;}int p2_xr_running(){return running;}
'''+s[start:end]+r'''
int main(){
 unsigned char gui[0x30]={0};int oldSet,newSet,menu;
 *(void**)(gui+0x18)=&oldSet;s26bv_register_terminal(gui);
 if(!s26bv_cursor_owned(gui,0)||!s26bv_cursor_owned(&oldSet,1)||s26bv_cursor_owned(&menu,1))return 1;
 *(void**)(gui+0x18)=&newSet;s26bv_register_terminal(gui);
 if(!s26bv_cursor_owned(&newSet,1)||s26bv_cursor_owned(&oldSet,1)||g_s26bvGuiCount!=1){puts("FAIL: stale backing-set registration");return 2;}
 on=0;if(s26bv_cursor_owned(gui,0))return 3;on=1;
 running=0;if(s26bv_cursor_owned(gui,0))return 4;running=1;
 g_h576bfMapTransitionActive=1;if(s26bv_cursor_owned(gui,0))return 5;g_h576bfMapTransitionActive=0;
 g_s26bvGuiCount=0;if(s26bv_cursor_owned(gui,0)||s26bv_cursor_owned(&newSet,1))return 6;
 puts("PASS: live backing-set refresh, unrelated menu, runtime OFF and world reset");return 0;
}
'''
name='cursor_baseline' if a.source else 'cursor_candidate'
b=r/'build';b.mkdir(exist_ok=True);f=b/(name+'.c');f.write_text(code)
subprocess.run([a.zig,'cc','-O2',str(f),'-o',str(f.with_suffix('.exe'))],check=True)
result=subprocess.run([str(f.with_suffix('.exe'))],capture_output=True,text=True)
out=r/'docs/v109-evidence';out.mkdir(exist_ok=True)
(out/(name+'.json')).write_text(json.dumps({'exit':result.returncode,'output':result.stdout,'scope':__doc__},indent=2))
print(result.stdout);raise SystemExit(result.returncode)
