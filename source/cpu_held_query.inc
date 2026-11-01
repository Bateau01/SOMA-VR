/* Same-query compound bounds rejection for held-item clearance only.
   Native outer filtering, candidate order, collector/pushback and every
   surviving primitive collision stay authoritative. See docs/CPU70_PLAN.md.
   No Newton solver hook, altered contacts, cadence or cross-query results. */
#ifndef CPU_HELD_QUERY
#define CPU_HELD_QUERY 0
#endif
#if CPU_HELD_QUERY
static PFN_H508_CheckShapeCollision c70HeldPairOriginal;
static u32 (*c70HeldThreadId)(void);
static u32 c70HeldOwner,c70HeldDepth,c70HeldReady,c70HeldAttempted;
static u8 __attribute__((ms_abi)) c70_held_pair(void*w,void*a,const float*am,void*b,const float*bm,void*data,i32 limit,u8 correct,i32 thread){
 u32 owner=__atomic_load_n(&c70HeldOwner,__ATOMIC_ACQUIRE);
 if(!owner||!c70HeldThreadId||owner!=c70HeldThreadId())return c70HeldPairOriginal(w,a,am,b,bm,data,limit,correct,thread);
 return ct_check_shape_collision(w,a,am,b,bm,data,limit,correct,thread);
}
static void c70_held_install(void){
 if(c70HeldAttempted)return;c70HeldAttempted=1;
 void*k=ext_GetModuleHandleA("kernel32.dll");c70HeldThreadId=(void*)ext_GetProcAddress(k,"GetCurrentThreadId");
 if(!c70HeldThreadId||!p_h508CheckShapeCollision)return;
 const u8 sig[]={0x48,0x8b,0xc4,0x4c,0x89,0x48,0x20,0x48,0x89,0x50,0x10,0x48,0x89,0x48,0x08,0x55};u8*t=(u8*)p_h508CheckShapeCollision;
 if(!h20_mem_executable(t))return;for(u32 i=0;i<sizeof(sig);i++)if(t[i]!=sig[i])return;
 if(ext_MH_CreateHook(t,c70_held_pair,(void**)&c70HeldPairOriginal))return;
 /* The helper calls the trampoline directly; it must not reenter this hook. */
 p_h508CheckShapeCollision=c70HeldPairOriginal;
 if(ext_MH_EnableHook(t)){p_h508CheckShapeCollision=(PFN_H508_CheckShapeCollision)t;return;}
 c70HeldReady=1;
}
static u32 c70_held_begin(void){
 if(!c70HeldReady)return 0;
 u32 id=c70HeldThreadId(),owner=__atomic_load_n(&c70HeldOwner,__ATOMIC_ACQUIRE);
 if(owner&&owner!=id)return 0;
 if(!c70HeldDepth){g_ctQueryCache.shape=0;__atomic_store_n(&c70HeldOwner,id,__ATOMIC_RELEASE);}
 ++c70HeldDepth;return 1;
}
static void c70_held_end(u32 entered){
 if(!entered)return;if(--c70HeldDepth==0){__atomic_store_n(&c70HeldOwner,0u,__ATOMIC_RELEASE);g_ctQueryCache.shape=0;}
}
#else
#define c70_held_install() ((void)0)
#define c70_held_begin() 0u
#define c70_held_end(x) ((void)(x))
#endif
