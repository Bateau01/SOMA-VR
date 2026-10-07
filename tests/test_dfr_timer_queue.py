"""A busy GPU must never cause a blocking timestamp read or query overwrite."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build'
s=(R/'source/foveation_timing_ei.inc').read_text();a=s.index('static i32 s26ei_timer_init');b=s.index('static void s26ei_gpu_collect',a);s=s[:a]+'static i32 s26ei_timer_init(void){return 1;}\n'+s[b:];s=s[:s.index('static void s26ei_opaque_draw')]
head=r'''
#include <assert.h>
#include <stdio.h>
typedef unsigned u32;typedef int i32;typedef unsigned long long u64;
static u32 g_s26eiDFRConfig=1,g_s26eiMeasureEpoch;static int ready,reads,issued,bound=91,reports;
#define ext_Log(...) (++reports)
static void ext_glGetIntegerv(u32 key,i32*out){assert(key==0x9193);*out=bound;}
static void __attribute__((ms_abi)) gen(i32 n,u32*out){static u32 next=1;for(int i=0;i<n;i++)out[i]=next++;}
static void __attribute__((ms_abi)) stamp(u32 id,u32 target){assert(id&&target==0x8e28);issued++;}
static void __attribute__((ms_abi)) avail(u32 id,u32 pname,u32*out){assert(bound==0);assert(pname==0x8867);*out=ready;}
static void __attribute__((ms_abi)) result(u32 id,u32 pname,u64*out){assert(ready&&bound==0&&pname==0x8866);reads++;*out=id*1000;}
static void __attribute__((ms_abi)) bind(u32 target,u32 id){assert(target==0x9192);bound=id;}
'''
tail=r'''
int main(void){
p_s26eiGenQueries=gen;p_s26eiQueryCounter=stamp;p_s26eiQueryAvailable=avail;p_s26eiQueryResult=result;p_s26eiTimerBindBuffer=bind;
g_s26eiDFRTiming=1;
for(int i=0;i<8;i++){g_s26eiTimerCalls=30;int ticket=s26ei_gpu_begin(1,1024,1024);assert(ticket==i);s26ei_gpu_end(ticket);}
assert(issued==16&&reads==0&&bound==91);
for(int i=0;i<500;i++){g_s26eiTimerCalls=30;assert(s26ei_gpu_begin(1,1024,1024)==-1);}
assert(issued==16&&reads==0&&bound==91);
ready=1;s26ei_gpu_collect();assert(reads==16&&bound==91&&g_s26eiGPUStats[1].count==8);
g_s26eiTimerCalls=30;int t=s26ei_gpu_begin(0,1024,1024);assert(t>=0);s26ei_gpu_end(t);s26ei_gpu_collect();assert(g_s26eiGPUStats[0].count==1);
g_s26eiTimerCalls=30;int first=s26ei_gpu_begin(1,1024,1024);
g_s26eiTimerCalls=30;int nested=s26ei_gpu_begin(1,1024,1024);assert(first!=nested);s26ei_gpu_end(nested);s26ei_gpu_end(first);
g_s26eiMeasureEpoch++;s26ei_gpu_collect();assert(g_s26eiGPUStats[1].count==8); /* stale samples discarded */
g_s26eiDFRTiming=0;int old=issued;for(int i=0;i<100;i++)assert(s26ei_gpu_begin(1,1024,1024)==-1);assert(issued==old);
printf("PASS: ring saturation skips; no unavailable reads; query-buffer restored; off makes no new queries\n");}
'''
p=B/'timer_queue.c';p.write_text(head+s+tail);exe=B/'timer_queue.exe';subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
