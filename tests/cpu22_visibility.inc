/* Private: native portal-container construction before split-loader insertion.
   No retained world pointer; exact Steam layout only. */
static void (__attribute__((ms_abi))*cpu22PrepareOriginal)(void*);
static void __attribute__((ms_abi)) cpu22_prepare(void*loader){
 if(loader&&cpu21ConvertOriginal&&cpuThreadId&&cpuThreadId()==cpuMainThread){
  u8*p=loader;
  if(*(u32*)(p+0x54)==5){
   u8*w=*(void**)(p+0x1c8);
   if(w&&!*(void**)(w+0x180)&&!*(u32*)(w+0x198)&&*(void**)(w+0xd8)){
    u64 t=0,end=0;if(cpuCounter)cpuCounter(&t);
    u64 result=cpu21ConvertOriginal((u64)w);
    if(cpuCounter)cpuCounter(&end);
    ext_Log(">>> CPU22_EARLY_CONTAINER frame %u ms %.4f ready %u old_empty %u",g_frameCounter,cpuFreq?1000.0*(end-t)/cpuFreq:0.,result&&result==*(u64*)(w+0x180),!*(void**)(w+0x170)&&!*(void**)(w+0x178));
    if(t)cpu14_event(27,3,t,end,0);
   }
  }
 }
 cpu22PrepareOriginal(loader);
}
static void cpu22_install(void){
 const u8 sig[]={0x40,0x53,0x57,0x48,0x83,0xec,0x28,0x48,0x8b,0x91,0xe0,0x02,0x00,0x00,0x48,0x89};
 if(cpu21ConvertOriginal)cpu_detail_hook(0x45eef0,sig,sizeof(sig),(void*)cpu22_prepare,(void**)&cpu22PrepareOriginal);
 ext_Log(">>> CPU22_VISIBILITY_PREINIT private %u",cpu22PrepareOriginal!=0);
}
