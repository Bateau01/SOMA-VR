static void cpu_near_probe(const void* world);
static void __attribute__((ms_abi)) cpu_metadata_body(const void*body,void*data){
 u32*counts=data;if(counts[0]>=128||!body||!p_h14GetUserData)return;counts[0]++;
 void*w=p_h14GetUserData(body);char name[96];name[0]=0;
 if(w&&h22_rtti_name(w,name,sizeof(name)))counts[1]++;
 if(w&&h20_mem_readable((u8*)w+0x2c0,8)){
  void*owner=*(void**)((u8*)w+0x2c0);name[0]=0;if(owner&&h22_rtti_name(owner,name,sizeof(name)))counts[2]++;
 }
}
static void cpu_metadata_census(const void*world){
 if(!CPU_WORK_PROFILE||!world||!p_h14WorldAABB)return;
 float lo[4]={-10000,-10000,-10000,0},hi[4]={10000,10000,10000,0};u32 counts[3]={0};
 p_h14WorldAABB(world,lo,hi,cpu_metadata_body,counts);
 ext_Log(">>> CPU_METADATA_CENSUS bodies %u wrapper_names %u owner_names %u; read-only fixture, not interaction validation",counts[0],counts[1],counts[2]);
}
/* Isolated observation only. Production compiler eliminates all counters/timers.
   Existing native calls/order unchanged. Stage buckets nest under PRE/POST. */
static i32 (__attribute__((ms_abi))*cpuCounter)(u64*);
static u64 cpuFreq,cpuBucket[H5755EG_P_COUNT],cpuTotal[H5755EG_P_COUNT];
static u32 cpuWarm,cpuRows,cpuSamples;static u64 cpuQueries,cpuRtti;
static void cpu11_install(void);static void cpu11_report(void);
static void cpu_engine_install(void);
static void cpu_texture_production_install(void);
static void cpu_render_production_install(void);
static void s29_install(void);
static void h5755eg_prof_try_init(void){
 cpu_texture_production_install();cpu_render_production_install();s29_install();
 if(!CPU_WORK_PROFILE||cpuCounter)return;void*k=ext_GetModuleHandleA("kernel32.dll");
 cpuCounter=(void*)ext_GetProcAddress(k,"QueryPerformanceCounter");
 i32 (__attribute__((ms_abi))*f)(u64*)=(void*)ext_GetProcAddress(k,"QueryPerformanceFrequency");if(f)f(&cpuFreq);cpu_engine_install();
}
static u64 h5755eg_tick(void){u64 t=0;if(CPU_WORK_PROFILE&&cpuWorkActive&&cpuCounter)cpuCounter(&t);return t;}
static void h5755eg_phys_add_since(i32 b,u64 t0){if(CPU_WORK_PROFILE&&cpuWorkActive&&t0&&b>=0&&b<H5755EG_P_COUNT)cpuBucket[b]+=h5755eg_tick()-t0;}
static void h5755ei_phys_frame_begin(void){
 cpuWorkActive=0;if(!CPU_WORK_PROFILE||!cpuFreq||cpuRows>=12)return;
 if(__atomic_load_n(&g_h5755bhPresentationState,__ATOMIC_ACQUIRE)!=H5755BH_GAMEPLAY_VR)return;
 if(cpuWarm++<120)return;
 zero_bytes(cpuBucket,sizeof(cpuBucket));cpuWorkQueries=cpuWorkRtti=0;cpuWorkActive=1;
}
static void h5755ei_phys_spike_finish(const void*world){(void)world;}
static void h5755eg_phys_reset(const void*world){(void)world;}
static void h5755eg_phys_finish_sample(const void*world){
 (void)world;if(!CPU_WORK_PROFILE||!cpuWorkActive)return;cpuWorkActive=0;
 for(u32 i=0;i<H5755EG_P_COUNT;i++)cpuTotal[i]+=cpuBucket[i];cpuQueries+=cpuWorkQueries;cpuRtti+=cpuWorkRtti;
 if(++cpuSamples<60)return;double k=1000.0/(double)cpuFreq/(double)cpuSamples;
 if(cpuRows<3)ext_Log(">>> CPU_INPUT sync %d active %u/%u flags %llu/%llu locate %d/%d stable %u/%u draw %d seen %u",g_lastSyncResult,g_lastActive[0],g_lastActive[1],(unsigned long long)g_lastFlags[0],(unsigned long long)g_lastFlags[1],g_lastLocateResult[0],g_lastLocateResult[1],g_h34ControllerStable[0],g_h34ControllerStable[1],*p2_hand_draw_ptr(),g_h14VisualSeen);
 ext_Log(">>> CPU_WORK row %u step %u rate %u hands %u/%u pre_ms %.6f newton_ms %.6f post_ms %.6f root_ms %.6f rig_ms %.6f curl_ms %.6f auth_ms %.6f held_ms %.6f contacts_ms %.6f postheld_ms %.6f queries_per_step %.2f rtti_per_step %.2f",cpuRows,g_h14PhysicsSteps,g_s26gdRateMultiplier,g_h34HandNewton[0]!=0,g_h34HandNewton[1]!=0,cpuTotal[0]*k,cpuTotal[1]*k,cpuTotal[2]*k,cpuTotal[5]*k,cpuTotal[6]*k,cpuTotal[7]*k,cpuTotal[9]*k,cpuTotal[10]*k,cpuTotal[12]*k,cpuTotal[13]*k,(double)cpuQueries/cpuSamples,(double)cpuRtti/cpuSamples);
 ext_Log(">>> CPU_METHOD row %u spans %u",cpuRows,(u32)(CPU_STRING_SPANS&&!cpuAsciiBaseline));
 ext_Log(">>> CPU_DETAIL row %u near_ms %.6f exactcurl_ms %.6f",cpuRows,cpuTotal[CPU_P_NEAR]*k,cpuTotal[CPU_P_CURL_EXACT]*k);
 ++cpuRows;if(cpuRows==12){cpu_metadata_census(world);cpu_near_probe(world);}cpuSamples=0;cpuQueries=cpuRtti=0;zero_bytes(cpuTotal,sizeof(cpuTotal));
}
static u32 cpuRenderWarm,cpuRenderCount,cpuRenderRows,cpuWorldCount;
static u64 cpuRenderTotal,cpuRenderXr,cpuRenderScene,cpuWorldTotal;
static u64 cpu_observe_tick(void){
 u64 t=0;if(CPU_WORK_PROFILE&&cpuCounter&&cpuRenderRows<10&&g_h5755bhPresentationState==H5755BH_GAMEPLAY_VR)cpuCounter(&t);return t;
}
static void cpu_observe_world(u64 t0){u64 t=cpu_observe_tick();if(t0&&t>=t0){cpuWorldTotal+=t-t0;cpuWorldCount++;}}
static void cpu_engine_report(void);
static void cpu_detail_report(void);
static void cpu_job_report(void);
static void cpu_texture_report(void);
static void h5755eg_render_finish(u64 t0,u64 xrTicks,u64 sceneTicks){
 u64 t=cpu_observe_tick();if(!t0||t<t0)return;
 if(cpuRenderWarm++<120){cpuWorldTotal=0;cpuWorldCount=0;return;}
 cpuRenderTotal+=t-t0;cpuRenderXr+=xrTicks;cpuRenderScene+=sceneTicks;
 if(++cpuRenderCount<120)return;
 double k=1000.0/(double)cpuFreq/(double)cpuRenderCount;
 ext_Log(">>> CPU_FRAME row %u render_wrapper_ms %.6f xr_begin_ms %.6f scene_ms %.6f outer_physics_per_render_ms %.6f world_calls %u frames %u",cpuRenderRows,cpuRenderTotal*k,cpuRenderXr*k,cpuRenderScene*k,cpuWorldTotal*k,cpuWorldCount,cpuRenderCount);
 cpu_detail_report();cpu_job_report();cpu_texture_report();if(cpuRenderRows==9)cpu_engine_report();
 cpuRenderRows++;cpuRenderCount=cpuWorldCount=0;cpuRenderTotal=cpuRenderXr=cpuRenderScene=cpuWorldTotal=0;
}

/* Steam observation only: per-module native dispatcher preserves every event. */
typedef void (__attribute__((ms_abi))*CPUModuleCall)(void*,i32,float);
static CPUModuleCall cpuModuleOriginal;
typedef struct {u64 vtable,ticks;u32 calls,event;char name[96];} CPUModuleRow;
static CPUModuleRow cpuModules[128];static u32 cpuModuleCount;
static void __attribute__((ms_abi)) cpu_module_call(void* object,i32 event,float dt){
 u64 t0=cpu_observe_tick(),vt=0;u32 slot=128;
 if(t0&&object&&event>=4&&event<=6){
  vt=*(u64*)object;
  for(u32 i=0;i<cpuModuleCount;i++)if(cpuModules[i].vtable==vt&&cpuModules[i].event==(u32)event){slot=i;break;}
  if(slot==128&&cpuModuleCount<128){slot=cpuModuleCount++;cpuModules[slot].vtable=vt;cpuModules[slot].event=(u32)event;h22_rtti_name(object,cpuModules[slot].name,96);}
  t0=cpu_observe_tick();
 }
 cpuModuleOriginal(object,event,dt);
 u64 t1=cpu_observe_tick();if(slot<128&&t0&&t1>=t0){cpuModules[slot].ticks+=t1-t0;cpuModules[slot].calls++;}
}
static void cpu_detail_install(void);
static void cpu_job_install(void);
static void cpu_job_report(void);
static void cpu_texture_install(void);
static void cpu_engine_install(void){
 if(!CPU_WORK_PROFILE)return;
 cpu_detail_install();cpu_job_install();cpu_texture_install();cpu11_install();
 u8*b=(u8*)ext_GetModuleHandleA(0);if(!b)return;
 const u8 sig[16]={0x48,0x83,0xec,0x28,0x80,0x79,0x32,0,0x4c,0x8b,0xc1,0x0f,0x84,0x0f,0x01,0};
 u8*t=b+0x15a390;if(!h20_mem_executable(t))return;
 for(u32 i=0;i<16;i++)if(t[i]!=sig[i]){ext_Log(">>> CPU_ENGINE rejected target signature");return;}
 i32 a=ext_MH_CreateHook(t,(void*)cpu_module_call,(void**)&cpuModuleOriginal),e=a?a:ext_MH_EnableHook(t);
 ext_Log(">>> CPU_ENGINE observation hook create %d enable %d",a,e);
}
static void cpu_engine_report(void){
 cpu11_report();
 if(!CPU_WORK_PROFILE)return;
 for(u32 i=0;i<cpuModuleCount;i++){
  CPUModuleRow*r=cpuModules+i;
  ext_Log(">>> CPU_MODULE event %u calls %u mean_ms %.6f total_ms %.3f name %s",r->event,r->calls,r->calls?1000.0*(double)r->ticks/(double)cpuFreq/(double)r->calls:0.0,1000.0*(double)r->ticks/(double)cpuFreq,r->name);
 }
}

/* CPU3 isolated native cost boundaries; original engine ownership is unchanged. */
static u32 (__attribute__((ms_abi))*cpuThreadId)(void);static u32 cpuMainThread;
typedef void (__attribute__((ms_abi))*CPUTextureCall)(void*,float);
typedef void (__attribute__((ms_abi))*CPUObjectCall)(void*);
static CPUTextureCall cpuTextureOriginal;static CPUObjectCall cpuMeshOriginal,cpuWaitOriginal;
typedef struct{u64 ticks,max;u32 calls,empty,nonempty;} CPUDetailRow;
static CPUDetailRow cpuDetails[3];
static u64 cpu_detail_begin(void){return cpuThreadId&&cpuThreadId()==cpuMainThread?cpu_observe_tick():0;}
static void cpu_detail_end(u32 slot,u64 t0,u32 empty){
 if(!t0)return;u64 end=0;cpuCounter(&end);CPUDetailRow*r=cpuDetails+slot;u64 d=end-t0;r->ticks+=d;if(d>r->max)r->max=d;r->calls++;if(empty)r->empty++;else r->nonempty++;
}
static u32 cpuStorageStreamingDepth;
static void __attribute__((ms_abi)) cpu_texture_call(void*p,float dt){
 u64 t=cpu_detail_begin();u32 empty=0;if(t&&p){u64*q=p;empty=q[0x5822]==q[0x5824]&&q[0x5821]==q[0x5823];}
 if(cpuThreadId&&cpuThreadId()==cpuMainThread){cpuStorageStreamingDepth++;cpuTextureOriginal(p,dt);cpuStorageStreamingDepth--;}else cpuTextureOriginal(p,dt);cpu_detail_end(0,t,empty);
}
static void __attribute__((ms_abi)) cpu_mesh_call(void*p){
 u64 t=cpu_detail_begin();u32 empty=0;if(t&&p){u64*q=p;empty=q[0x1018]==q[0x1019];}
 cpuMeshOriginal(p);cpu_detail_end(1,t,empty);
}
typedef struct{u64 identity,ticks,max;u32 waits,jobs,items,kinds[5];} CPU9Pool;
static CPU9Pool cpu9Pools[32];static u32 cpu9PoolCount;
static CPU9Pool* cpu9_pool(void*p){
 for(u32 i=0;i<cpu9PoolCount;i++)if(cpu9Pools[i].identity==(u64)p)return cpu9Pools+i;
 if(cpu9PoolCount>=32)return 0;
 CPU9Pool*r=cpu9Pools+cpu9PoolCount++;r->identity=(u64)p;return r;
}
typedef struct{u64 caller,ticks,max;u32 calls;} CPU9Caller;
static CPU9Caller cpu9Callers[48];static u32 cpu9CallerCount;
static void cpu9_before_wait(void*pool);
static void __attribute__((ms_abi)) cpu_wait_call(void*p){
 u64 t=cpu_detail_begin();u32 empty=0;if(t&&p){u8*q=p;empty=*(volatile u64*)(q+0x08)==*(volatile u64*)(q+0x10)&&*(volatile u64*)(q+0x28)==0;}
 u64 caller=t?(u64)__builtin_return_address(0)-(u64)ext_GetModuleHandleA(0):0;
 cpu9_before_wait(p);cpuWaitOriginal(p);cpu_detail_end(2,t,empty);
 if(t){u64 end=0;cpuCounter(&end);u32 i=0;for(;i<cpu9CallerCount;i++)if(cpu9Callers[i].caller==caller)break;if(i<48){if(i==cpu9CallerCount)cpu9CallerCount++;CPU9Caller*r=cpu9Callers+i;r->caller=caller;r->ticks+=end-t;if(end-t>r->max)r->max=end-t;r->calls++;}}
 if(t){u64 end=0;cpuCounter(&end);CPU9Pool*r=cpu9_pool(p);if(r){u64 elapsed=end-t;r->ticks+=elapsed;if(elapsed>r->max)r->max=elapsed;r->waits++;}}
}
static void cpu_detail_hook(u32 rva,const u8*sig,u32 count,void*hook,void**original){
 u8*t=(u8*)ext_GetModuleHandleA(0)+rva;for(u32 i=0;i<count;i++)if(t[i]!=sig[i]){ext_Log(">>> CPU_DETAIL_HOOK reject %x",rva);return;}
 i32 a=ext_MH_CreateHook(t,hook,original),e=a?a:ext_MH_EnableHook(t);ext_Log(">>> CPU_DETAIL_HOOK %x create %d enable %d",rva,a,e);
}
static void cpu_detail_install(void){
 if(!CPU_WORK_PROFILE)return;cpuThreadId=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"GetCurrentThreadId");if(!cpuThreadId)return;cpuMainThread=cpuThreadId();
 const u8 a[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x56,0x48,0x83,0xec,0x40};
 const u8 b[]={0x40,0x57,0x48,0x83,0xec,0x50,0x48,0x8b,0x81,0xc0,0x80,0,0,0x48,0x8b,0xf9};
 const u8 c[]={0x40,0x56,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x83,0xc1,0x30,0x48,0x89,0x6c,0x24,0x38};
 cpu_detail_hook(0x2df7e0,a,sizeof(a),(void*)cpu_texture_call,(void**)&cpuTextureOriginal);
 cpu_detail_hook(0x29f0e0,b,sizeof(b),(void*)cpu_mesh_call,(void**)&cpuMeshOriginal);

}
static void cpu_detail_report(void){
 if(!CPU_WORK_PROFILE)return;for(u32 i=0;i<3;i++){CPUDetailRow*r=cpuDetails+i;ext_Log(">>> CPU_NATIVE_DETAIL row %u slot %u calls %u total_ms %.4f max_ms %.4f empty %u pending %u",cpuRenderRows,i,r->calls,1000.0*r->ticks/cpuFreq,1000.0*r->max/cpuFreq,r->empty,r->nonempty);}
 for(u32 i=0;i<cpu9PoolCount;i++){CPU9Pool*r=cpu9Pools+i;ext_Log(">>> CPU9_POOL row %u slot %u waits %u jobs %u items %u total_ms %.6f max_ms %.6f animation %u particle %u sound %u character %u other %u",cpuRenderRows,i,r->waits,r->jobs,r->items,1000.0*r->ticks/cpuFreq,1000.0*r->max/cpuFreq,r->kinds[0],r->kinds[1],r->kinds[2],r->kinds[3],r->kinds[4]);u64 id=r->identity;zero_bytes(r,sizeof(*r));r->identity=id;}
 for(u32 i=0;i<cpu9CallerCount;i++){CPU9Caller*r=cpu9Callers+i;ext_Log(">>> CPU9_CALLER row %u rva %llx calls %u total_ms %.6f max_ms %.6f",cpuRenderRows,(unsigned long long)r->caller,r->calls,1000.0*r->ticks/cpuFreq,1000.0*r->max/cpuFreq);u64 id=r->caller;zero_bytes(r,sizeof(*r));r->caller=id;}
 zero_bytes(cpuDetails,sizeof(cpuDetails));
}

typedef void (__attribute__((ms_abi))*CPUQueueCall)(void*,void*,u8);
static CPUQueueCall cpuQueueOriginal;static u64 cpuJobBase;static u32 cpuJobCalls[5],cpuJobEmpty[5];
#include "cpu9_render_trial.inc"
static u64 cpu9JobVtables[32];static u32 cpu9JobTypes;
static void __attribute__((ms_abi)) cpu_queue_call(void*pool,void*job,u8 dispatch){
 if(cpu_detail_begin()&&job){u64 vt=*(u64*)job;u32 kind=4,offset=0x10;
  if(vt==cpuJobBase+0x6d5528)kind=0;else if(vt==cpuJobBase+0x6d52d0)kind=1;else if(vt==cpuJobBase+0x6d52e8)kind=2;else if(vt==cpuJobBase+0x6d6f08){kind=3;offset=0x14;}
  u32 found=0;for(u32 i=0;i<cpu9JobTypes;i++)if(cpu9JobVtables[i]==vt)found=1;
  if(!found&&cpu9JobTypes<32){cpu9JobVtables[cpu9JobTypes++]=vt;char name[128];name[0]=0;h22_rtti_name(job,name,128);ext_Log(">>> CPU9_JOB_TYPE vtable %llx execute %llx name %s",(unsigned long long)(vt-cpuJobBase),(unsigned long long)(*(u64*)(vt+8)-cpuJobBase),name);}
  cpuJobCalls[kind]++;if(kind<4&&*(i32*)((u8*)job+offset)==0)cpuJobEmpty[kind]++;
  CPU9Pool*r=cpu9_pool(pool);if(r){r->jobs++;r->kinds[kind]++;if(kind<4){i32 count=*(i32*)((u8*)job+offset);if(count>0&&count<100000)r->items+=(u32)count;}}
 }
 if(!cpu9_capture(pool,job,dispatch))cpuQueueOriginal(pool,job,dispatch);
}
static void cpu_job_install(void){
 if(!CPU_WORK_PROFILE)return;cpuJobBase=(u64)ext_GetModuleHandleA(0);
 const u8 sig[]={0x48,0x83,0xec,0x28,0x48,0x85,0xd2,0x74,0x1c,0x4c,0x8b,0x49,0x18,0x48,0x8b,0x01};

 cpu9_install();

}
static void cpu_job_report(void){

 if(!CPU_WORK_PROFILE)return;ext_Log(">>> CPU_JOB_CENSUS row %u animation %u/%u particle %u/%u sound %u/%u character %u/%u other %u",cpuRenderRows,cpuJobEmpty[0],cpuJobCalls[0],cpuJobEmpty[1],cpuJobCalls[1],cpuJobEmpty[2],cpuJobCalls[2],cpuJobEmpty[3],cpuJobCalls[3],cpuJobCalls[4]);zero_bytes(cpuJobCalls,sizeof(cpuJobCalls));zero_bytes(cpuJobEmpty,sizeof(cpuJobEmpty));
}

#include "cpu_texture_profile.inc"

#include "cpu_scene_observe.inc"
#include "cpu_streaming.inc"
