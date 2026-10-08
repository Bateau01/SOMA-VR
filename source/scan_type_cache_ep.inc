/* Scope: a single synchronous Newton AABB enumeration. No body/owner identity
   survives the call. Each live owner is still checked before reading its vtable.
   Cache only successful RTTI classification; invalid/unknown data is retried.
   Material discovery remains outside this cache and runs for every body. */
#define S26EP_TYPE_CAP 64u
typedef struct {
    const void* world;u32 visited,count,hits,misses;
    const void* vtable[S26EP_TYPE_CAP];u8 kind[S26EP_TYPE_CAP];
} H530SelfScan;
static i32 s26ep_type_mask(H530SelfScan* scan,const void* owner){
    if(!owner||!h20_mem_readable(owner,8))return 0;
    const void* vt=*(void* const*)owner;if(!vt)return 0;
    for(u32 i=0;i<scan->count;++i)if(scan->vtable[i]==vt){scan->hits++;return scan->kind[i];}
    char rt[96];rt[0]=0;scan->misses++;
    if(!h22_rtti_name(owner,rt,sizeof(rt)))return 0;
    i32 mask=(h25_str_contains(rt,"cLuxCameraEntity")?1:0)|(h25_str_contains(rt,"cCharacterBodyNewton")?2:0);
    if(scan->count<S26EP_TYPE_CAP){u32 i=scan->count++;scan->vtable[i]=vt;scan->kind[i]=(u8)mask;}
    return mask;
}
static i32 s26ep_self_kind(H530SelfScan* scan,const void* body){
    if(!body||!p_h14GetUserData)return 0;void* w=p_h14GetUserData(body);if(!w)return 0;
    if(h20_mem_readable((u8*)w+0x2c8,8)){
        void* q=*(void**)((u8*)w+0x2c0);if(q&&(s26ep_type_mask(scan,q)&1))return 1;
    }
    if(h20_mem_readable((u8*)w+0x168,8)){
        void* q=*(void**)((u8*)w+0x160);if(q&&(s26ep_type_mask(scan,q)&2))return 2;
    }
    return 0;
}
