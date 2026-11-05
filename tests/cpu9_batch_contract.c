#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint64_t u64;typedef uint32_t u32;typedef uint8_t u8;typedef int i32;
#define ABI __attribute__((ms_abi))
static void zero_bytes(void*p,u64 n){memset(p,0,n);}
static void ext_Log(const char*s,...){(void)s;}
static u64 cpu_detail_begin(void){return 0;}
static void cpu_detail_hook(u32 x,const u8*s,u32 n,void*h,void**o){(void)x;(void)s;(void)n;(void)h;(void)o;}
static u64 cpuJobBase,cpuFreq=1;
static u32 cpuMainThread=1,threadNow=1;static u32 tid(void){return threadNow;}
static u32(*cpuThreadId)(void)=tid;
static i32 ABI counter(u64*p){*p=0;return 1;}static i32(ABI*cpuCounter)(u64*)=counter;
static void(ABI*cpuQueueOriginal)(void*,void*,u8);
#define CPU_WORK_PROFILE 1
#define CPU_RENDER_JOBS 1
#define CPU9_CONTRACT 1
#include "../source/cpu9_render_trial.inc"
typedef struct{u64*vtable;u64 p1,p2;u8 done;u8 pad[3];u32 calls;}Job;
static Job jobs[70];static void*queued[128];static u32 queuedCount,njobs;static int unknown,waitEarly;
static u64 vt[2],badvt[2];
static void ABI run(void*p){Job*j=p;j->calls++;j->done=1;}
static void ABI queue(void*p,void*j,u8 d){(void)p;(void)d;queued[queuedCount++]=j;}
static void ABI dispatch(void*p){(void)p;for(u32 i=0;i<queuedCount;i++)run(queued[i]);queuedCount=0;}
static void ABI compile(void*l,u64 m,u8 o,void*p){(void)l;(void)m;(void)o;
 for(u32 i=0;i<njobs;i++){
 jobs[i].vtable=(unknown&&i==2)?badvt:vt;
 if(!cpu9_capture(p,jobs+i,0))queue(p,jobs+i,0);
 if(waitEarly&&i==1){cpu9_before_wait(p);dispatch(p);}
 }
 cpu9_dispatch(p);
}
int main(void){vt[1]=(u64)run;badvt[1]=(u64)run;cpuJobBase=(u64)vt-0x6e9f58;
 cpu9Ready=1;cpuQueueOriginal=queue;cpu9DispatchOriginal=dispatch;cpu9CompileOriginal=compile;
 unsigned cases=0;
 for(unsigned mode=0;mode<2;mode++)for(unsigned n=0;n<70;n++)for(int u=0;u<2;u++)for(int e=0;e<2;e++){
 memset(jobs,0,sizeof(jobs));cpu9Mode=mode;njobs=n;unknown=u;waitEarly=e;
 cpu9_compile(0,0,0,(void*)1);
 assert(!cpu9Batch&&!queuedCount);
 for(unsigned i=0;i<n;i++)assert(jobs[i].calls==1&&jobs[i].done);
 cases++;
 }
 /* A worker must not see or drain the main thread's stack batch. */
 CPU9Batch b={0};b.pool=(void*)1;cpu9Batch=&b;threadNow=2;
 assert(cpu9_capture((void*)1,jobs,0)==0);cpu9_before_wait((void*)1);assert(cpu9Batch==&b&&!b.count);
 threadNow=1;cpu9Ready=0;assert(cpu9_capture((void*)1,jobs,0)==0);cpu9_before_wait((void*)1);assert(cpu9Batch==&b);
 cpu9Batch=0;cpu9Ready=1;
 assert(cpu9Failed==0);printf("PASS %u native/inline/early-barrier/unknown/capacity cases; each job once\n",cases);
}
