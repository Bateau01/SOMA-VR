static i32 h5716_ci_contains(const char*,const char*);
static void cpu12_install(void);static void cpu12_report(void);
/* Diagnostic only: original calls, arguments and ordering are preserved.
   No object pointers retained; totals are bounded by cpu_detail_begin. */
static void (__attribute__((ms_abi))*cpu11MeshOriginal)(void*,float,u8);
static void (__attribute__((ms_abi))*cpu11PhysicsOriginal)(void*,float);
static void (__attribute__((ms_abi))*cpu11ListenerOriginal)(void*);
static u64 cpu11Ticks[3];static u32 cpu11Calls[3];
static void cpu11_end(u32 slot,u64 t){if(t){u64 q=0;cpuCounter(&q);cpu11Ticks[slot]+=q-t;cpu11Calls[slot]++;}}
static void __attribute__((ms_abi)) cpu11_mesh(void*p,float dt,u8 phase){u64 t=cpu_detail_begin();cpu11MeshOriginal(p,dt,phase);cpu11_end(0,t);}
static void __attribute__((ms_abi)) cpu11_physics(void*p,float dt){
 if(CPU_WORK_PROFILE){static u32 once;if(!once){once=1;char name[96];if(h22_rtti_name(p,name,96)){ext_Log(">>> CPU12_WORLD type %s",name);void*m=ext_GetModuleHandleA("Newton.dll");i32 (__attribute__((ms_abi))*get)(void*)=(void*)ext_GetProcAddress(m,"NewtonGetThreadsCount");i32 (__attribute__((ms_abi))*max)(void*)=(void*)ext_GetProcAddress(m,"NewtonGetMaxThreadsCount");if(get&&max&&h20_mem_readable((u8*)p+0x354,4)&&h5716_ci_contains(name,"cPhysicsWorldNewton")){void*w=*(void**)((u8*)p+0x2a8);ext_Log(">>> CPU12_THREADS requested %d actual %d maximum %d",*(i32*)((u8*)p+0x354),get(w),max(w));}}}}
 u64 t=cpu_detail_begin();cpu11PhysicsOriginal(p,dt);cpu11_end(1,t);}
static void __attribute__((ms_abi)) cpu11_listener(void*p){u64 t=cpu_detail_begin();cpu11ListenerOriginal(p);cpu11_end(2,t);}
static void cpu11_report(void){cpu12_report();if(!CPU_WORK_PROFILE)return;for(u32 i=0;i<3;i++)ext_Log(">>> CPU11_SCENE stage %u calls %u mean_ms %.6f",i,cpu11Calls[i],cpu11Calls[i]?1000.0*cpu11Ticks[i]/cpuFreq/cpu11Calls[i]:0.0);}
static void cpu11_install(void){
 if(!CPU_WORK_PROFILE)return;cpu12_install();
 const u32 rvas[]={0x24d6c0,0x264550,0x29d230};
 const u8 sigs[3][15]={{0x48,0x89,0x5c,0x24,0x10,0x44,0x88,0x44,0x24,0x18,0x48,0x89,0x4c,0x24,0x08},{0x40,0x55,0x53,0x57,0x41,0x56,0x41,0x57,0x48,0x8b,0xec,0x48,0x83,0xec,0x70},{0x48,0x83,0xec,0x68,0x48,0x8b,0x81,0x88,0,0,0,0x48,0x85,0xc0,0x0f}};
 void*hooks[]={(void*)cpu11_mesh,(void*)cpu11_physics,(void*)cpu11_listener};
 void**orig[]={(void**)&cpu11MeshOriginal,(void**)&cpu11PhysicsOriginal,(void**)&cpu11ListenerOriginal};
 u8*b=(u8*)ext_GetModuleHandleA(0);
 for(u32 i=0;i<3;i++){u8*t=b+rvas[i];if(!h20_mem_executable(t))return;for(u32 j=0;j<15;j++)if(t[j]!=sigs[i][j])return;}
 for(u32 i=0;i<3;i++){i32 c=ext_MH_CreateHook(b+rvas[i],hooks[i],orig[i]);i32 e=c?c:ext_MH_EnableHook(b+rvas[i]);ext_Log(">>> CPU11_OBSERVE stage %u create %d enable %d",i,c,e);}
}

#include "cpu_physics_observe.inc"

