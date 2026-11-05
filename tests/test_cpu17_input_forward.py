from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'tests/cpu17_input.inc').read_text().split('static void cpu17_input_install')[0]
pre=r"""
#include <stdio.h>
#include <stdlib.h>
typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static u64 clockValue=10;static int calls,events,enabled=1;static void*seen;
static u64 cpu_detail_begin(){return enabled?clockValue++:0;}
static int counter(u64*p){*p=clockValue++;return 1;}static int(*cpuCounter)(u64*)=counter;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 v){C(k==17&&b>=a);events++;}
static void __attribute__((ms_abi)) del(i32 n,const u32*p){C(n==2);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) storage(u32 t,i32 n,u32 f,i32 w,i32 h){C(t==7&&n==3&&f==9&&w==128&&h==64);calls++;}
static void __attribute__((ms_abi)) sub(u32 t,i32 l,i32 x,i32 y,i32 w,i32 h,u32 f,i32 b,const void*p){C(t==7&&l==2&&x==1&&y==3&&w==64&&h==32&&f==9&&b==512);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) child(void*p){seen=p;calls++;}
"""
post=r"""
static float seenDt;
static void __attribute__((ms_abi)) action(void*p,float dt){seen=p;seenDt=dt;calls++;}
int main(){int token=1;cpu17_beginOriginal=child;cpu17_finishOriginal=child;cpu17_pollOriginal=child;cpu17_devicesOriginal=child;cpu17ActionsOriginal=action;
 cpu17_begin(&token);cpu17_finish(&token);cpu17_poll(&token);cpu17_devices(&token);cpu17_actions(&token,1.0f/120.0f);
 C(calls==5&&events==5&&seen==&token&&seenDt==1.0f/120.0f);
 enabled=0;cpu17_begin(&token);cpu17_finish(&token);cpu17_poll(&token);cpu17_devices(&token);cpu17_actions(&token,1.0f/60.0f);
 C(calls==10&&events==5&&seenDt==1.0f/60.0f);
 puts("PASS exact once input forwarding and unchanged timestep, capture on/off");}
"""
b=r/'build/cpu17-input-forward';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu17-input-forward.json').write_text(json.dumps({'scope':'Compiled exact observer functions with mocked original calls; not native input execution','exit':x.returncode,'output':x.stdout+x.stderr},indent=2));raise SystemExit(x.returncode)
