from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];src=r/'tests/cpu22_visibility.inc'
pre=r'''
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static u32 cpuMainThread=7,thread=7,g_frameCounter;static u64 cpuFreq=1000000,clockv;
static u32 tid(void){return thread;}static u32(*cpuThreadId)(void)=tid;
static int clk(u64*p){*p=++clockv;return 1;}static int(*cpuCounter)(u64*)=clk;
static int converted,prepared,events;static void*expected;
static u64 __attribute__((ms_abi)) convert(u64 w){converted++;*(u64*)(w+0x180)=w+0x200;*(u64*)(w+0x170)=*(u64*)(w+0x178)=0;return w+0x200;}
static u64(__attribute__((ms_abi))*cpu21ConvertOriginal)(u64)=convert;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 i){C(k==27&&d==3&&b>=a);events++;}
#define ext_Log(...) ((void)0)
'''
post=r'''
static void __attribute__((ms_abi)) prepare(void*p){C(p==expected);prepared++;}
int main(){u64 lw[128]={0},ww[128]={0};u8*l=(u8*)lw,*w=(u8*)ww;expected=l;cpu22PrepareOriginal=prepare;
*(void**)(l+0x1c8)=w;*(u32*)(l+0x54)=5;*(void**)(w+0xd8)=w;
cpu22_prepare(l);C(converted==1&&prepared==1&&events==1);cpu22_prepare(l);C(converted==1&&prepared==2);
*(u64*)(w+0x180)=0;thread=8;cpu22_prepare(l);C(converted==1);thread=7;
*(u32*)(l+0x54)=26;cpu22_prepare(l);C(converted==1);*(u32*)(l+0x54)=5;
*(u32*)(w+0x198)=1;cpu22_prepare(l);C(converted==1);*(u32*)(w+0x198)=0;
*(void**)(w+0xd8)=0;cpu22_prepare(l);C(converted==1);*(void**)(w+0xd8)=w;
*(void**)(l+0x1c8)=0;cpu22_prepare(l);C(converted==1);*(void**)(l+0x1c8)=w;
cpu21ConvertOriginal=0;cpu22_prepare(l);C(converted==1);cpu21ConvertOriginal=convert;
cpuThreadId=0;cpu22_prepare(l);C(converted==1);cpuThreadId=tid;
expected=0;cpu22_prepare(0);C(converted==1&&prepared==10&&events==1);
puts("PASS exact forwarding and stage/thread/initialization/null gates; mock only");}
'''
b=r/'build/cpu22-unit';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+src.read_text().split('static void cpu22_install')[0]+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu22-unit.json').write_text(json.dumps(dict(scope='Compiled guard mock, not native renderer proof',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest()),indent=2))
raise SystemExit(x.returncode)
