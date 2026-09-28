/* Audio options must not invoke ApplyUserConfig's graphics/GUI rebuild.
   Verified on Soma.exe SHA256 7c424e60...; validate each called entry first. */
static u64 s26u_apply_audio_config(void){
    if(g_h576mScriptGateAck!=1)return 0;
    u8* base=(u8*)ext_GetModuleHandleA(0);if(!base)return 0;
    const u32 rva[3]={0x5ee90,0x39b30,0x39e10};
    const u8 sig[3][12]={{0x48,0x8b,0xc4,0x55,0x41,0x56,0x41,0x57,0x48,0x8d,0xa8,0xe8},{0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x48,0x8b},{0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x48,0x89}};
    for(i32 i=0;i<3;++i){if(!h20_mem_readable(base+rva[i],12))return 0;for(i32 k=0;k<12;++k)if(base[rva[i]+k]!=sig[i][k])return 0;}
    if(!h20_mem_readable(base+0x8147c0,8))return 0;
    void* lux=*(void**)(base+0x8147c0);if(!lux||!h20_mem_readable(lux,0x858))return 0;
    void* cfg=*(void**)((u8*)lux+0xa8);void* engine=*(void**)lux;
    if(!cfg||!engine||!h20_mem_readable(cfg,0xd0)||!h20_mem_readable(engine,0xd8))return 0;
    void* sound=*(void**)((u8*)engine+0xd0);if(!sound||!h20_mem_readable(sound,0x40)||!*(void**)((u8*)sound+0x38))return 0;
    typedef void (__attribute__((ms_abi)) *Read)(void*);
    typedef void (__attribute__((ms_abi)) *Notify)(void*,i32,void*);
    ((Read)(void*)(base+rva[0]))(cfg);
    ((Read)(void*)(base+rva[1]))(lux);
    ((Notify)(void*)(base+rva[2]))(lux,2,0);
    static u32 logs;if(logs++<8u)ext_Log(">>> S26U AUDIO MENU APPLY: native config/audio/module refresh; graphics and GUI rebuild bypassed");
    return 1;
}
