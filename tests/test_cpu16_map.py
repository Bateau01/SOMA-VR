from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1];b=r/'build/cpu16';b.mkdir(exist_ok=True)
head=r'''#include <stdint.h>
#include <assert.h>
#include <stdio.h>
typedef uint64_t u64;typedef unsigned u32;typedef unsigned char u8;typedef int i32;
static u32 cpu13Phase=99;static u64 cpuFreq=10000000;
static i32 h5748n_copy_tstring(void*p,char*s,u32 n){(void)p;(void)n;s[0]=0;return 0;}
#define ext_Log(...) ((void)0)
static u64 clockValue=100;static unsigned enabled=1,called,events;static float wanted;static void*expected;static u64 identity;
static u64 cpu_detail_begin(void){return enabled?++clockValue:0;}
static void counter(u64*p){*p=++clockValue;}static void(*cpuCounter)(u64*)=counter;
static void*ext_GetModuleHandleA(const char*p){(void)p;return (void*)0x1000;}
static void cpu14_event(u32 k,u32 d,u64 a,u64 z,u64 id){assert(k==15&&d<5&&z>a);identity=id;events++;}
static void cpu_detail_hook(u32 r,const u8*s,u32 n,void*h,void**o){assert(r&&s&&n==16&&h&&o);}
static void __attribute__((ms_abi)) native_dt(void*p,float dt){assert(p==expected&&dt==wanted);called++;*(u64*)p=0;}
static u64 __attribute__((ms_abi)) native_script(void*p){assert(p==expected);called++;*(u64*)p=0;return 0xfedcba9876543210ull;}
'''
tail=r'''int main(void){
 cpu16_map_original=native_dt;cpu16_transient_original=native_dt;cpu16_timer_original=native_dt;cpu16_entity_original=native_dt;cpu16_script_original=native_script;
 void(__attribute__((ms_abi))*fn[])(void*,float)={cpu16_map,cpu16_transient,cpu16_timer,cpu16_entity};
 u64 object;expected=&object;
 for(unsigned gate=0;gate<2;gate++){enabled=gate;for(unsigned rate=60;rate<=120;rate+=60){wanted=1.0f/rate;
 for(unsigned i=0;i<4;i++){object=0x4321;unsigned c=called,e=events;fn[i](&object,wanted);assert(called==c+1&&events==e+gate&&object==0);if(gate)assert(identity==0x3321);}
 object=0x4321;unsigned c=called,e=events;assert(cpu16_script(&object)==0xfedcba9876543210ull);assert(called==c+1&&events==e+gate);if(gate)assert(identity==0x3321);
 }}cpu16_install();puts("PASS exact-once original calls, 60/120 dt, script return, disabled capture, pre-callback identity after object mutation");}
'''
p=b/'test.c';p.write_text(head+(r/'tests/cpu16_map.inc').read_text()+tail)
zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc','-O2',str(p),'-o',str(b/'test.exe')],check=True);subprocess.run([str(b/'test.exe')],check=True)
