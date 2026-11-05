from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'tests/cpu18_post.inc').read_text().split('static void cpu18_post_install')[0]
pre=r"""
#include <stdio.h>
#include <stdlib.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static u64 clockValue=10;static int calls,events,enabled=1;static void*seen;
static u64 cpu_detail_begin(){return enabled?clockValue++:0;}
static int counter(u64*p){*p=clockValue++;return 1;}static int(*cpuCounter)(u64*)=counter;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 v){C((k==21||k==23)&&b>=a);events++;}
static void __attribute__((ms_abi)) del(i32 n,const u32*p){C(n==2);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) storage(u32 t,i32 n,u32 f,i32 w,i32 h){C(t==7&&n==3&&f==9&&w==128&&h==64);calls++;}
static void __attribute__((ms_abi)) sub(u32 t,i32 l,i32 x,i32 y,i32 w,i32 h,u32 f,i32 b,const void*p){C(t==7&&l==2&&x==1&&y==3&&w==64&&h==32&&f==9&&b==512);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) child(void*p){seen=p;calls++;}
"""
post=r"""
static float seenDt;
static void __attribute__((ms_abi)) action(void*p,float dt){seen=p;seenDt=dt;calls++;}
static u64 __attribute__((ms_abi)) streaming(void*p,u64 arg){seen=p;calls++;C(arg==0x123456789abcdef0ULL);return 0xfedcba9876543210ULL;}
static void __attribute__((ms_abi)) preload(void*p,u64 a){seen=p;calls++;C(a==7);}
static void __attribute__((ms_abi)) update(void*p,u64 a,u64 b){seen=p;calls++;C(a==8&&b==9);}
int main(){int token=1;cpu18QueueOriginal=child;cpu18PackOriginal=child;cpu18VariableOriginal=action;
 cpu18_queue(&token);cpu18_pack(&token);cpu18_variable(&token,1.0f/120.0f);
 C(calls==3&&events==3&&seen==&token&&seenDt==1.0f/120.0f);
 enabled=0;cpu18_queue(&token);cpu18_pack(&token);cpu18_variable(&token,1.0f/60.0f);
 C(calls==6&&events==3&&seenDt==1.0f/60.0f);
 cpu18_clearOriginal=child;cpu18_destroyOriginal=child;cpu18_finishOriginal=child;cpu18_streamOriginal=streaming;
 for(int mode=0;mode<2;mode++){enabled=mode;cpu18_clear(&token);cpu18_destroy(&token);cpu18_finish(&token);C(cpu18_stream(&token,0x123456789abcdef0ULL)==0xfedcba9876543210ULL);}
 C(calls==14&&events==7&&seen==&token);
 cpu18PreloadOriginal=preload;cpu18UpdateOriginal=update;unsigned char object[128]={0};enabled=0;cpu18_preload(object,7);cpu18_update(object,8,9);C(calls==16);enabled=1;cpu18_preload(object,7);cpu18_update(object,8,9);C(calls==18&&events==9);
 puts("PASS exact once post-update forwarding and unchanged timestep, capture on/off");}
"""
b=r/'build/cpu18-post-forward';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu18-post-forward.json').write_text(json.dumps({'scope':'Compiled exact observer functions with mocked original calls; not native map execution','exit':x.returncode,'output':x.stdout+x.stderr},indent=2));raise SystemExit(x.returncode)

