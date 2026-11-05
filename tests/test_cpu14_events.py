from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1];b=r/'build/cpu14';b.mkdir(parents=True,exist_ok=True)
head=r'''
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
typedef uint32_t u32;typedef uint64_t u64;typedef int32_t i32;
static u32 cpu13Phase=1,g_frameCounter=17,g_h14PhysicsSteps=3,g_h5755bhPresentationState=2,cpuMainThread=1;
static u64 cpuFreq=10000000;static int g_h5750vPrimeWrapperActive;
static u32 thread(void){return 1;}static u32(*cpuThreadId)(void)=thread;
static void*context=(void*)1;static void*ctx(void){return context;}static void*(*p_s26efContext)(void)=ctx;
static int s26ei_timer_init(void){return 1;}
static u32 bound=7,ready,reads,issued,nextq=1;
static void ext_glGetIntegerv(u32 a,i32*b){(void)a;*b=bound;}
static void p_s26eiTimerBindBuffer(u32 a,u32 b){(void)a;bound=b;}
static void p_s26eiQueryAvailable(u32 a,u32 b,u32*c){(void)a;(void)b;*c=ready;}
static void p_s26eiQueryResult(u32 a,u32 b,u64*c){(void)b;assert(ready);assert(!bound);reads++;*c=a*1000;}
static void p_s26eiGenQueries(i32 n,u32*q){while(n--)*q++=nextq++;}
static void p_s26eiQueryCounter(u32 a,u32 b){(void)a;(void)b;issued++;}
#define ext_fopen fopen
#define ext_fwrite fwrite
#define ext_fclose fclose
#define ext_Log(...) ((void)0)
'''
tail=r'''
int main(void){
 cpu14_event(1,0,10,20,0);assert(cpu14Count==1);cpu14_event(1,0,20,10,0);assert(cpu14Count==1);
 for(int i=0;i<32;i++){int t=cpu14_gpu_begin();assert(t>=0);cpu14_gpu_end(t);}assert(bound==7);
 for(int i=0;i<500;i++)assert(cpu14_gpu_begin()==-1);assert(reads==0&&issued==64&&cpu14GpuSkipped==500);
 g_frameCounter=40;cpu13Phase=2;ready=1;cpu14_collect(context);assert(reads==64&&cpu14Count==33&&bound==7);
 for(int i=1;i<33;i++){assert(cpu14Events[i].frame==17&&cpu14Events[i].phase==1&&cpu14Events[i].kind==7);}
 int t=cpu14_gpu_begin();context=(void*)2;cpu14_gpu_end(t);assert(cpu14Gpu[t].busy==0);
 cpu14Count=200000;cpu14_event(1,0,10,20,0);assert(cpu14Count==200000&&cpu14Dropped==1);
 cpu14Saved=1;cpu14_event(1,0,10,20,0);assert(cpu14Dropped==1&&cpu14_gpu_begin()==-1);
 puts("PASS bounded events, invalid spans, source-frame correlation, full queue skips, no unavailable reads, query buffer restoration, context change, saved gate");
}
'''
p=b/'test.c';p.write_text(head+(r/'tests/cpu14_events.inc').read_text()+tail)
zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc',str(p),'-o',str(b/'test.exe')],check=True)
subprocess.run([str(b/'test.exe')],check=True)
