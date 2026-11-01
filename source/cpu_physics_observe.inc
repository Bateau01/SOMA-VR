static void (__attribute__((ms_abi))*cpu12PreOriginal)(void*,float);
static void (__attribute__((ms_abi))*cpu12PostOriginal)(void*,float);
static u8 (__attribute__((ms_abi))*cpu12ActiveOriginal)(void*);
static void (__attribute__((ms_abi))*cpu12QueriesOriginal)(void*);
static u64 cpu12Ticks[4];static u32 cpu12Calls[4],cpu12Samples[4];
static u64 cpu12_begin(u32 s){
 if(!CPU_WORK_PROFILE||!cpuThreadId||cpuThreadId()!=cpuMainThread||cpuRenderRows>=10||g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!cpuCounter)return 0;
 u32 n=cpu12Calls[s]++;if(s<3&&(n&31))return 0;u64 t=0;cpuCounter(&t);return t;
}
static void cpu12_end(u32 s,u64 t){if(t){u64 q=0;cpuCounter(&q);cpu12Ticks[s]+=q-t;cpu12Samples[s]++;}}
static void __attribute__((ms_abi)) cpu12_pre(void*p,float dt){u64 t=cpu12_begin(0);cpu12PreOriginal(p,dt);cpu12_end(0,t);}
static void __attribute__((ms_abi)) cpu12_post(void*p,float dt){u64 t=cpu12_begin(1);cpu12PostOriginal(p,dt);cpu12_end(1,t);}
static u8 __attribute__((ms_abi)) cpu12_active(void*p){u64 t=cpu12_begin(2);u8 v=cpu12ActiveOriginal(p);cpu12_end(2,t);return v;}
static void __attribute__((ms_abi)) cpu12_queries(void*p){u64 t=cpu12_begin(3);cpu12QueriesOriginal(p);cpu12_end(3,t);}
static void cpu12_report(void){if(!CPU_WORK_PROFILE)return;for(u32 s=0;s<4;s++)ext_Log(">>> CPU12_PHYS stage %u calls %u samples %u sample_mean_ms %.9f",s,cpu12Calls[s],cpu12Samples[s],cpu12Samples[s]?1000.0*cpu12Ticks[s]/cpuFreq/cpu12Samples[s]:0.0);}
static void cpu12_install(void){
 if(!CPU_WORK_PROFILE)return;
 const u32 rvas[]={0x27a180,0x27a3a0,0x2797d0,0x262060};
 const u8 sigs[4][15]={{0x48,0x8b,0xc4,0x53,0x48,0x81,0xec,0x20,0x01,0,0,0x80,0xb9,0x25,0x02},{0x40,0x53,0x48,0x83,0xec,0x50,0x80,0xb9,0x9c,0x02,0,0,0,0x0f,0x29},{0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x40,0x32,0xff,0x48,0x8b},{0x48,0x89,0x4c,0x24,0x08,0x55,0x41,0x57,0x48,0x8d,0x6c,0x24,0xe8,0x48,0x81}};
 void*hooks[]={(void*)cpu12_pre,(void*)cpu12_post,(void*)cpu12_active,(void*)cpu12_queries};
 void**orig[]={(void**)&cpu12PreOriginal,(void**)&cpu12PostOriginal,(void**)&cpu12ActiveOriginal,(void**)&cpu12QueriesOriginal};u8*b=(u8*)ext_GetModuleHandleA(0);
 for(u32 i=0;i<4;i++){u8*t=b+rvas[i];if(!h20_mem_executable(t))return;for(u32 j=0;j<15;j++)if(t[j]!=sigs[i][j])return;}
 for(u32 i=0;i<4;i++){i32 c=ext_MH_CreateHook(b+rvas[i],hooks[i],orig[i]);i32 e=c?c:ext_MH_EnableHook(b+rvas[i]);ext_Log(">>> CPU12_OBSERVE stage %u create %d enable %d",i,c,e);}
}
