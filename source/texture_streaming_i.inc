/* Optional S26I experiment for the verified Steam Soma.exe.
   FUN_1402de9c0 gates ready texture uploads at DAT_14080cca8 (1 GiB).
   Keep the 60 MiB/s rate and map-preload priority untouched. */
static i32 g_s26TextureSetting=0,g_s26TextureVerified,g_s26TextureOwned;
static u64* g_s26TextureBudget;
static void s26ef_set_texture_budget(i32 enabled){
    __atomic_store_n(&g_s26TextureSetting,enabled?1:0,__ATOMIC_RELEASE);
}

static void s26_texture_budget_policy(i32 active,u64* budget,i32* owned){
    if(!budget||!owned)return;
    if(active){
        if(*budget==0x40000000ull){*budget=0x60000000ull;*owned=1;}
    }else if(*owned){
        if(*budget==0x60000000ull)*budget=0x40000000ull;
        *owned=0;
    }
}
static void s26_texture_streaming_step(void){
    /* The profile menu owns this setting. No hidden flag-file override. */
    i32 enabled=__atomic_load_n(&g_s26TextureSetting,__ATOMIC_ACQUIRE)>0;
    if(!enabled){
        s26_texture_budget_policy(0,g_s26TextureBudget,&g_s26TextureOwned);
        return;
    }
    if(!g_s26TextureVerified){
        g_s26TextureVerified=1;
        u8* base=(u8*)ext_GetModuleHandleA(0);
        const u8 sig[29]={0x48,0x89,0x74,0x24,0x20,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x83,0xec,0x60,0x48,0x8b,0x05,0xda,0xe2,0x52,0x00,0x0f,0x29,0x74,0x24,0x50,0x66,0x0f};
        if(!base||!h20_mem_readable(base+0x2de9c0,29)||!h20_mem_readable(base+0x80cca8,16))return;
        for(u32 i=0;i<29u;++i)if(base[0x2de9c0+i]!=sig[i])return;
        if(*(u64*)(base+0x80cca8)!=0x40000000ull)return;
        g_s26TextureBudget=(u64*)(base+0x80cca8);
        ext_Log(">>> S26I OPTIONAL TEXTURE BUDGET: verified engine threshold 1024 -> 1536 MiB while VR runs; upload rate and map priority unchanged; not total VRAM limit");
    }
    s26_texture_budget_policy(g_h576mScriptRuntimePublished==1&&p2_xr_on()&&p2_xr_running(),g_s26TextureBudget,&g_s26TextureOwned);
}
