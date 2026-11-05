/* Isolated Steam experiment only. Invoke the native HPL setter once per live world. */
static const void*cpu33World;
static void cpu33_workers(const void*world){
 if(!world||world==cpu33World||!g_h34PhysicsWorldWrapper)return;
 u8*w=(u8*)g_h34PhysicsWorldWrapper;
 if(!h20_mem_readable(w+0x2a8,8)||*(const void**)(w+0x2a8)!=world||!h20_mem_readable(w+0x354,4))return;
 u8*n=ext_GetModuleHandleA("Newton.dll");u8*fn=n?ext_GetProcAddress(n,"NewtonSetThreadsCount"):0;
 const u8 sig[]={0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20};
 if(!fn||fn!=n+0x1300)return;for(u32 i=0;i<sizeof(sig);i++)if(fn[i]!=sig[i])return;
 i32(__attribute__((ms_abi))*get)(const void*)=(void*)ext_GetProcAddress(n,"NewtonGetThreadsCount");if(!get)return;
 void(__attribute__((ms_abi))*set)(void*,i32)=(void*)((u8*)ext_GetModuleHandleA(0)+0x558040);
 i32 before=get(world);set(w,2);i32 after=get(world);cpu33World=world;
 ext_Log(">>> CPU33 private native worker trial before %d after %d wrapper %d",before,after,*(i32*)(w+0x354));
}
