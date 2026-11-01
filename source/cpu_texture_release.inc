#ifndef CPU_TEXTURE_RELEASE
#define CPU_TEXTURE_RELEASE 0
#endif
#if CPU_TEXTURE_RELEASE && !CPU_WORK_PROFILE
/* Bounded streaming cleanup: transfer only an owned contiguous pixel allocation.
   Engine bitmap/list/string destruction stays synchronous. No GL/engine access on workers. */
#define CPU15_SLOTS 4u
#define CPU15_MAX_BYTES (128ull*1024*1024)
typedef struct {u32 state;void*work;void*pixels;u64 bytes;} CPU15FreeSlot;
static CPU15FreeSlot cpu15FreeSlots[CPU15_SLOTS];
static void (__attribute__((ms_abi))*cpu15DeleteArray)(void*);
static void (__attribute__((ms_abi))*cpu15Submit)(void*);
static u64 cpu15PendingBytes;static u32 cpu15FreeReady;
static void __attribute__((ms_abi)) cpu15_free_worker(void*instance,void*context,void*work){
 (void)instance;(void)work;CPU15FreeSlot*s=context;
 if(__atomic_load_n(&s->state,__ATOMIC_ACQUIRE)!=1)return;
 cpu15DeleteArray(s->pixels);
 __atomic_fetch_sub(&cpu15PendingBytes,s->bytes,__ATOMIC_RELAXED);
 __atomic_store_n(&s->state,0u,__ATOMIC_RELEASE);
}
static i32 cpu15_defer_pixels(void*bitmap){
 if(!cpu15FreeReady||!bitmap)return 0;
 u8*b=bitmap;if(!b[0x21])return 0;
 u64 begin=*(u64*)b,end=*(u64*)(b+8);
 if(!begin||end<=begin||(end-begin)%16||(end-begin)/16>16)return 0;
 u64 base=*(u64*)begin,total=0;if(!base)return 0;
 for(u64 p=begin;p<end;p+=16){i32 bytes=*(i32*)(p+8);if(bytes<=0||*(u64*)p!=base+total||base+total<base)return 0;total+=(u32)bytes;if(total>CPU15_MAX_BYTES)return 0;}
 if(total<2u*1024u*1024u||__atomic_load_n(&cpu15PendingBytes,__ATOMIC_RELAXED)>CPU15_MAX_BYTES-total)return 0;
 for(u32 i=0;i<CPU15_SLOTS;i++){CPU15FreeSlot*s=cpu15FreeSlots+i;u32 empty=0;
  if(!__atomic_compare_exchange_n(&s->state,&empty,2u,0,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED))continue;
  s->pixels=(void*)base;s->bytes=total;__atomic_fetch_add(&cpu15PendingBytes,total,__ATOMIC_RELAXED);
  /* Native destructor normally frees first buffer and clears all these pointers. */
  for(u64 p=begin;p<end;p+=16)*(u64*)p=0;
  __atomic_store_n(&s->state,1u,__ATOMIC_RELEASE);cpu15Submit(s->work);return 1;
 }return 0;
}
#ifndef CPU15_TEST
static void cpu15_free_init(void){
 void*k=ext_GetModuleHandleA("kernel32.dll");void*crt=ext_GetModuleHandleA("MSVCR100.dll");if(!k||!crt)return;
 cpu15DeleteArray=(void*)ext_GetProcAddress(crt,"??_V@YAXPEAX@Z");
 u8*thunk=(u8*)ext_GetModuleHandleA(0)+0x64b248;const u8 sig[]={0xff,0x25,0x82,0xa2,0x03,0x00};
 for(u32 i=0;i<6;i++)if(thunk[i]!=sig[i])return;
 if(!cpu15DeleteArray||*(void**)(thunk+6+*(i32*)(thunk+2))!=(void*)cpu15DeleteArray)return;
 void*(__attribute__((ms_abi))*create)(void*,void*,void*)=(void*)ext_GetProcAddress(k,"CreateThreadpoolWork");
 void(__attribute__((ms_abi))*close)(void*)=(void*)ext_GetProcAddress(k,"CloseThreadpoolWork");cpu15Submit=(void*)ext_GetProcAddress(k,"SubmitThreadpoolWork");
 if(!create||!close||!cpu15Submit)return;
 for(u32 i=0;i<CPU15_SLOTS;i++){cpu15FreeSlots[i].work=create((void*)cpu15_free_worker,cpu15FreeSlots+i,0);if(!cpu15FreeSlots[i].work){for(u32 j=0;j<i;j++){close(cpu15FreeSlots[j].work);cpu15FreeSlots[j].work=0;}return;}}
 cpu15FreeReady=1;ext_Log("TEXTURE BUFFER RELEASE: bounded worker cleanup enabled; native fallback retained");
}
#endif

static CPUObjectCall cpuPixelDestroyOriginal;
static void __attribute__((ms_abi)) cpu_pixel_destroy(void*p){
 if(cpuStorageStreamingDepth&&cpuThreadId&&cpuThreadId()==cpuMainThread)cpu15_defer_pixels(p);
 cpuPixelDestroyOriginal(p);
}
static void cpu_texture_release_install(void){
 static u32 attempted;if(attempted)return;attempted=1;
 u8*t=(u8*)ext_GetModuleHandleA(0)+0x334e20;
 const u8 sig[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x33,0xed};
 for(u32 i=0;i<sizeof(sig);i++)if(t[i]!=sig[i])return;
 if(ext_MH_CreateHook(t,(void*)cpu_pixel_destroy,(void**)&cpuPixelDestroyOriginal))return;
 cpu15_free_init();if(!cpu15FreeReady)return;
 if(ext_MH_EnableHook(t)){
  cpu15FreeReady=0;void(__attribute__((ms_abi))*close)(void*)=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"CloseThreadpoolWork");
  if(close)for(u32 i=0;i<CPU15_SLOTS;i++){close(cpu15FreeSlots[i].work);cpu15FreeSlots[i].work=0;}
 }
}

#else
static void cpu_texture_release_install(void){}
#endif
