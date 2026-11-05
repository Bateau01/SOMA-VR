/* Private scoped Newton timing, not solver policy. No world pointer is retained. */
static void (__attribute__((ms_abi))*cpu25SetClock)(const void*,u32(__attribute__((ms_abi))*)(void));
static u32 cpu25Ready,cpu25Valid;static u32 cpu14Saved;
static u32 __attribute__((ms_abi)) cpu25_clock(void){u64 t=0;cpuCounter(&t);return (u32)((t/cpuFreq)*1000000ULL+((t%cpuFreq)*1000000ULL)/cpuFreq);}
static void cpu25_init(void){
 if(cpu25Ready)return;cpu25Ready=1;u8*m=ext_GetModuleHandleA("Newton.dll");if(!m)return;
 u8*set=ext_GetProcAddress(m,"NewtonSetPerformanceClock"),*read=ext_GetProcAddress(m,"NewtonReadPerformanceTicks");
 const u8 a[]={0x48,0x89,0x91,0x60,0x24,0,0,0x48,0x8d,0x05,0x62,0xca,0x06,0};
 const u8 b[]={0xb8,0x07,0,0,0,0x3b,0xd0};
 if(set!=m+0x13a0||read!=m+0x13e0)return;
 for(u32 i=0;i<sizeof(a);i++)if(set[i]!=a[i])return;
 for(u32 i=0;i<sizeof(b);i++)if(read[i]!=b[i])return;
 cpu25SetClock=(void*)set;cpu25Valid=1;ext_Log(">>> CPU25 native scoped microsecond clock ready");
}
static u32 cpu25_begin(const void*w){
 if(!w||!cpu_detail_begin()||!cpuCounter||!cpuFreq||cpu14Saved)return 0;
 cpu25_init();if(!cpu25Valid||*(void**)((const u8*)w+0x2460))return 0;
 cpu25SetClock(w,cpu25_clock);return 1;
}
static void cpu25_end(const void*w,u32 active){if(active)cpu25SetClock(w,0);}
