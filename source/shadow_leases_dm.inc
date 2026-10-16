/* The native shadow pool's +0x18 stamp means "leased by this render frame",
   not "shadow content last refreshed" (+0x1c). Native 1401f1b10 refuses a
   second lease in the same frame, even for the same light. The two completed
   stereo scenes can reuse resources sequentially; their GL reads/writes are
   ordered. Never change the global frame counter, light owner, content age,
   textures, caster list or a lease while the first scene is still executing. */
typedef struct {void* renderer;void* world;void* frustum;u32 xrFrame,nativeFrame;i32 eye;u8 valid; i32 role; u32 depth;} S26DMShadowBoundary;
static S26DMShadowBoundary g_s26dmShadowBoundary;
static u32* s26dm_native_render_stamp(void){
    static u32* stamp;static u8 tried;
    if(!tried){
        tried=1;u8* base=(u8*)ext_GetModuleHandleA(0);
        const u8 sig[28]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x50,0xff,0x05,0x96,0x5e,0x57,0x00,0x33,0xc0};
        if(base&&h20_mem_readable(base+0x29ea40u,28u)&&h20_mem_readable(base+0x8148f0u,4u)){
            i32 ok=1;for(u32 i=0;i<28u;++i)if(base[0x29ea40u+i]!=sig[i])ok=0;
            if(ok)stamp=(u32*)(base+0x8148f0u);
        }
    }
    return stamp;
}
static u32 s26dm_release_shadow_leases(void* renderer,u32 frame){
    if(!renderer||!h20_mem_readable((u8*)renderer+0x850u,0x80u))return 0;
    u32 released=0;
    for(u32 tier=0;tier<4u;++tier){
        u8* vec=(u8*)renderer+0x850u+tier*0x20u;
        u64 begin=*(u64*)vec,end=*(u64*)(vec+8u);
        if(end<begin||(end-begin)%8u||(end-begin)/8u>256u||!h20_mem_readable((void*)begin,(u32)(end-begin)))continue;
        for(u64 at=begin;at<end;at+=8u){
            u8* rec=*(u8**)at;if(!rec||!h20_mem_readable(rec,0x38u)||!h20_mem_writable(rec+0x18u,4u))continue;
            if(*(u32*)(rec+0x18u)==frame){*(u32*)(rec+0x18u)=frame-1u;++released;}
        }
    }
    return released;
}
/* Roles: 0 unclassified/inactive, 1 exact player camera, 2 auxiliary.
   Native cCamera3D::GetFrustum (Steam 140277d80) returns camera+0x3f8.
   Do not use P2's last-published frustum: the render callback also publishes
   monitor cameras, so it can lag the current scene by one render. */
static i32 s26gq_scene_role(i32 live,void* camera,void* frustum){
    if(!live||!camera||!frustum||!h20_mem_readable((u8*)camera+0x3f8u,0x198u))return 0;
    return frustum==(void*)((u8*)camera+0x3f8u)?1:2;
}
static u32 s26dm_shadow_begin(i32 role,void* renderer,void* world,void* frustum,u32 xrFrame,u32 nativeFrame,i32 eye){
    S26DMShadowBoundary* s=&g_s26dmShadowBoundary;u32 n=0;
    ++s->depth;
    /* Nested scenes may still have a parent consuming its leased textures. */
    if(s->depth==1u && role && s->valid && s->renderer==renderer && s->world==world &&
       s->xrFrame==xrFrame && s->nativeFrame==nativeFrame &&
       (role==1 || s->role==1) && (s->frustum!=frustum || s->eye!=eye))
        n=s26dm_release_shadow_leases(renderer,nativeFrame);
    s->valid=0;return n;
}
static void s26dm_shadow_end(i32 role,void* renderer,void* world,void* frustum,u32 xrFrame,u32 nativeFrame,i32 eye){
    S26DMShadowBoundary* s=&g_s26dmShadowBoundary;
    if(!s->depth){s->valid=0;return;}
    --s->depth;
    if(s->depth){s->valid=0;return;}
    s->renderer=renderer;s->world=world;s->frustum=frustum;s->xrFrame=xrFrame;s->nativeFrame=nativeFrame;s->eye=eye;s->role=role;s->valid=role?1:0;
}
