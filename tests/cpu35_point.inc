/* Sampled main-thread native clock caller/cycles, not a physics policy. */
static void cpu35_point(void*caller,u64 tick){
 if(!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 static i32(__attribute__((ms_abi))*query)(void*,u64*);static u8*module;
 if(!query){query=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"QueryThreadCycleTime");module=ext_GetModuleHandleA("Newton.dll");}
 u64 cycles=0;if(!query||!module||!query((void*)(u64)-2,&cycles)){cpu14_event(51,0,tick,tick,1);return;}
 u64 offset=(u8*)caller-module;if(offset>=0xd0000){cpu14_event(51,1,tick,tick,offset);return;}
 cpu14_event(50,(u32)offset,tick,tick,cycles);
}
