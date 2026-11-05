from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1];b=r/'build/cpu15';b.mkdir(parents=True,exist_ok=True)
head=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef uint32_t u32;typedef uint64_t u64;typedef int32_t i32;
#define CPU15_TEST 1
'''
tail=r'''
static void*(__attribute__((ms_abi))*allocate)(u64);
static void(__attribute__((ms_abi))*release)(void*);
static volatile LONG freed;
static void __attribute__((ms_abi)) checked_free(void*p){assert(((u8*)p)[0]==0x5a);InterlockedIncrement(&freed);release(p);}
static void __attribute__((ms_abi)) fake_submit(void*p){(void)p;}
typedef struct{u8 object[80];u64 entries[6];void*base;}Fixture;
static void fixture(Fixture*f,u32 bytes){memset(f,0,sizeof(*f));f->base=allocate(bytes);assert(f->base);((u8*)f->base)[0]=0x5a;f->entries[0]=(u64)f->base;f->entries[1]=bytes/2;f->entries[2]=(u64)f->base+bytes/2;f->entries[3]=bytes/2;*(u64*)f->object=(u64)f->entries;*(u64*)(f->object+8)=(u64)(f->entries+4);f->object[0x21]=1;}
int main(void){
 HMODULE crt=LoadLibraryA("msvcr100.dll");assert(crt);allocate=(void*)GetProcAddress(crt,"??_U@YAPEAX_K@Z");release=(void*)GetProcAddress(crt,"??_V@YAXPEAX@Z");assert(allocate&&release);
 cpu15DeleteArray=checked_free;cpu15Submit=fake_submit;cpu15FreeReady=1;
 Fixture f[5];for(int i=0;i<5;i++)fixture(f+i,32*1024*1024);
 for(int i=0;i<4;i++){assert(cpu15_defer_pixels(f[i].object));assert(!f[i].entries[0]&&!f[i].entries[2]);}
 assert(cpu15PendingBytes==CPU15_MAX_BYTES);assert(!cpu15_defer_pixels(f[4].object));assert(f[4].entries[0]==(u64)f[4].base);
 for(int i=0;i<4;i++)cpu15_free_worker(0,cpu15FreeSlots+i,0);assert(cpu15PendingBytes==0&&freed==4);
 f[4].object[0x21]=0;assert(!cpu15_defer_pixels(f[4].object));f[4].object[0x21]=1;
 f[4].entries[2]++;assert(!cpu15_defer_pixels(f[4].object));f[4].entries[2]--;
 f[4].entries[1]=0;assert(!cpu15_defer_pixels(f[4].object));release(f[4].base);
 cpu15Submit=(void*)SubmitThreadpoolWork;
 for(int i=0;i<4;i++){cpu15FreeSlots[i].work=CreateThreadpoolWork((PTP_WORK_CALLBACK)cpu15_free_worker,cpu15FreeSlots+i,0);assert(cpu15FreeSlots[i].work);}
 int accepted=0;
 for(int i=0;i<200;i++){Fixture q;fixture(&q,2*1024*1024);if(cpu15_defer_pixels(q.object)){accepted++;assert(!q.entries[0]&&!q.entries[2]);}else{assert(q.entries[0]==(u64)q.base);release(q.base);}}
 for(int i=0;i<4;i++){WaitForThreadpoolWorkCallbacks(cpu15FreeSlots[i].work,FALSE);CloseThreadpoolWork(cpu15FreeSlots[i].work);}
 assert(cpu15PendingBytes==0&&freed==accepted+4);
 printf("PASS native MSVCR100 new[]/delete[], exact-once free, transfer, queue/memory cap, malformed/unowned fallback, concurrent jobs: %d accepted\n",accepted);
}
'''
p=b/'test.c'
core=(r/'source/cpu_texture_release.inc').read_text().split('#define CPU15_SLOTS',1)[1].split('static CPUObjectCall',1)[0]
p.write_text(head+'#define CPU15_SLOTS'+core+tail)
zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc','-O2',str(p),'-o',str(b/'test.exe')],check=True);subprocess.run([str(b/'test.exe')],check=True)
