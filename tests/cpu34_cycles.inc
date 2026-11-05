/* Private sampled OS cycle accounting. Native physics policy unchanged. */
static i32 (__attribute__((ms_abi))*cpu34Query)(void*,u64*);
static u32 (__attribute__((ms_abi))*cpu34Id)(void*);
static i32 (__attribute__((ms_abi))*cpu34Count)(const void*);
static void*cpu34Handles[9];static u64 cpu34Before[9];static u32 cpu34Ids[9];
static u32 cpu14Saved;
static u32 cpu34Ready,cpu34Active,cpu34N,cpu34Sequence,cpu34Bad;
static void cpu34_begin(const void*w){
 cpu34Active=0;if(!w||!cpu_detail_begin()||cpu14Saved||((cpu34Sequence++)&31u))return;
 if(!cpu34Ready){cpu34Ready=1;void*k=ext_GetModuleHandleA("kernel32.dll"),*n=ext_GetModuleHandleA("Newton.dll");
 cpu34Query=(void*)ext_GetProcAddress(k,"QueryThreadCycleTime");cpu34Id=(void*)ext_GetProcAddress(k,"GetThreadId");
 u8*f=ext_GetProcAddress(n,"NewtonGetThreadsCount");const u8 sig[]={0x8b,0x81,0xa0,0x1a,0,0,0xc3};
 if(f!=(u8*)n+0x1340)return;for(u32 i=0;i<sizeof(sig);i++)if(f[i]!=sig[i])return;cpu34Count=(void*)f;
 }
 if(!cpu34Query||!cpu34Id||!cpu34Count)return;if(!h20_mem_readable((const u8*)w+0x2250,4))return;i32 n=*(i32*)((u8*)w+0x2250);if(n<0||n>8||cpu34Count(w)!=(n?n:1))return;
 if(!h20_mem_readable((const u8*)w+0x23c0,(u64)n*8))return;
 cpu34N=(u32)n;cpu34Bad=0;
 for(u32 i=0;i<=cpu34N;i++){
 void*h=i==cpu34N?(void*)(u64)-2:*(void**)((u8*)w+0x23c0+i*8);
 cpu34Handles[i]=h;cpu34Ids[i]=cpu34Id(h);
 if(!cpu34Ids[i]||!cpu34Query(h,&cpu34Before[i]))cpu34Bad|=1u<<i;
 }
 cpu34Active=1;
}
static void cpu34_after(u64 start,u64 end){
 if(!cpu34Active)return;cpu34Active=0;u64 after[9]={0};
 for(u32 i=0;i<=cpu34N;i++)if(!cpu34Query(cpu34Handles[i],&after[i])||after[i]<cpu34Before[i])cpu34Bad|=1u<<i;
 cpu14_event(48,cpu34N,start,end,cpu34Bad);
 for(u32 i=0;i<=cpu34N;i++){cpu14_event(49,i,end,end,cpu34Ids[i]);if(!(cpu34Bad&(1u<<i)))cpu14_event(47,i,end,end,after[i]-cpu34Before[i]);cpu34Handles[i]=0;}
}
