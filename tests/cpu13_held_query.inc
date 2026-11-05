/* Test-only, original narrowphase always executes exactly once. */
static PFN_H508_CheckShapeCollision cpu13PairOriginal;
static void* cpu13OwnShape;static u32 cpu13QueryScope,cpu13PairReady;
static u8 __attribute__((ms_abi)) cpu13_pair(void*w,void*a,const float*am,void*b,const float*bm,void*cd,i32 max,u8 correct,i32 thread){
 if(!cpu13QueryScope||cpu13Phase>=11||!cpuCounter||!cpuThreadId||cpuThreadId()!=cpuMainThread)return cpu13PairOriginal(w,a,am,b,bm,cd,max,correct,thread);
 u32 slot=(b==cpu13OwnShape&&cpu13OwnShape)?19:20;u64 t=0,q=0;cpuCounter(&t);u8 hit=cpu13PairOriginal(w,a,am,b,bm,cd,max,correct,thread);cpuCounter(&q);cpu13Totals[cpu13Phase][slot]+=q-t;cpu13Totals[cpu13Phase][slot+2]++;return hit;
}
static void cpu13_pair_install(void){
 if(cpu13PairReady)return;cpu13PairReady=1;u8*t=(u8*)ext_GetModuleHandleA(0)+0x558bc0;
 const u8 sig[]={0x48,0x8b,0xc4,0x4c,0x89,0x48,0x20,0x48,0x89,0x50,0x10,0x48,0x89,0x48,0x08,0x55};
 if(!h20_mem_executable(t))return;for(u32 i=0;i<sizeof(sig);i++)if(t[i]!=sig[i])return;
 i32 c=ext_MH_CreateHook(t,(void*)cpu13_pair,(void**)&cpu13PairOriginal);i32 e=c?c:ext_MH_EnableHook(t);ext_Log(">>> CPU13_PAIR_OBSERVER create %d enable %d",c,e);
}
