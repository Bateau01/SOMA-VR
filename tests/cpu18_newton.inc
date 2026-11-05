/* Diagnostic reads after native NewtonUpdate. No performance clock replacement. */
static u32 (__attribute__((ms_abi))*cpu18Ticks)(const void*,u32);
static i32 (__attribute__((ms_abi))*cpu18BodyCount)(const void*);
static u32 cpu18Resolved;
static void cpu18_newton(const void*world,u64 start,u64 end){
 if(!world||!start||end<start||cpu13Phase>10)return;
 if(!cpu18Resolved){cpu18Resolved=1;void*m=ext_GetModuleHandleA("Newton.dll");cpu18Ticks=(void*)ext_GetProcAddress(m,"NewtonReadPerformanceTicks");cpu18BodyCount=(void*)ext_GetProcAddress(m,"NewtonWorldGetBodyCount");ext_Log(">>> CPU18 Newton read-only counters %u %u; raw ticks, clock unchanged",cpu18Ticks!=0,cpu18BodyCount!=0);}
 if(end-start<cpuFreq/1000)return;
 if(cpu18Ticks)for(u32 i=0;i<8;i++)cpu14_event(19,i,end,end,cpu18Ticks(world,i));
 if(cpu18BodyCount)cpu14_event(20,0,end,end,(u32)cpu18BodyCount(world));
}
