from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'tests/cpu17_texture.inc').read_text().split('static void cpu17_install')[0]
pre=r"""
#include <stdio.h>
#include <stdlib.h>
typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static u64 clockValue=10;static int calls,events,enabled=1;static void*seen;
static u64 cpu_detail_begin(){return enabled?clockValue++:0;}
static int counter(u64*p){*p=clockValue++;return 1;}static int(*cpuCounter)(u64*)=counter;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 v){C(k==16&&b>=a);events++;}
static void __attribute__((ms_abi)) del(i32 n,const u32*p){C(n==2);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) storage(u32 t,i32 n,u32 f,i32 w,i32 h){C(t==7&&n==3&&f==9&&w==128&&h==64);calls++;}
static void __attribute__((ms_abi)) sub(u32 t,i32 l,i32 x,i32 y,i32 w,i32 h,u32 f,i32 b,const void*p){C(t==7&&l==2&&x==1&&y==3&&w==64&&h==32&&f==9&&b==512);seen=(void*)p;calls++;}
static void __attribute__((ms_abi)) child(void*p){seen=p;calls++;}
"""
post=r"""
int main(){u32 ids[2]={19,20};cpu17DeleteOriginal=del;cpu17StorageOriginal=storage;cpu17SubOriginal=sub;cpu17ChildrenOriginal=child;
 cpu17_delete(2,ids);C(calls==1&&events==0&&seen==ids);
 cpu17RetireDepth=1;cpu17_delete(2,ids);C(calls==2&&events==1&&seen==ids);
 cpu17_storage(7,3,9,128,64);C(calls==3&&events==2);
 cpu17_sub(7,2,1,3,64,32,9,512,ids);C(calls==4&&events==3&&seen==ids);
 cpu17_children(ids);C(calls==5&&events==4&&seen==ids);
 enabled=0;cpu17_delete(2,ids);cpu17_children(ids);C(calls==7&&events==4);
 puts("PASS exact-once forwarding, all arguments, scope exclusion and disabled capture");}
"""
b=r/'build/cpu17-forward';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu17-forward.json').write_text(json.dumps({'scope':'Compiled exact observer functions with mocked original calls; not native GL execution','exit':x.returncode,'output':x.stdout+x.stderr},indent=2));raise SystemExit(x.returncode)
