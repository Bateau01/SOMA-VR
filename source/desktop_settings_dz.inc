/* Ghidra: startup 0x46200 copies LowLevel::GetScreenSize into options+64/+68.
   0x5d1f0 serializes those fields to Screen Width/Height. Keep requested desktop
   dimensions separate from actual/clamped UI and oversized VR drawables. */
static i32 g_s26dzDesktopW,g_s26dzDesktopH;
static u32 g_s26dzInternalMenuRebuild;
static void s26dz_desktop_request(u32 w,u32 h){
    if(w>=320u&&h>=200u&&w<=8192u&&h<=8192u){g_s26dzDesktopW=(i32)w;g_s26dzDesktopH=(i32)h;}
}
typedef void (__attribute__((ms_abi)) *S26DZSaveOptions)(void*);
static S26DZSaveOptions o_s26dzSaveOptions;
static void __attribute__((ms_abi)) s26dz_save_options(void* self){
    if(!o_s26dzSaveOptions)return;
    if(!self||g_s26dzDesktopW<320||g_s26dzDesktopH<200||!h20_mem_readable(self,0x70u)){
        o_s26dzSaveOptions(self);return;
    }
    i32* size=(i32*)((u8*)self+0x64u);i32 oldW=size[0],oldH=size[1];
    size[0]=g_s26dzDesktopW;size[1]=g_s26dzDesktopH;
    o_s26dzSaveOptions(self);
    size[0]=oldW;size[1]=oldH;
    ext_Log(">>> S26DZ CONFIG DESKTOP SAVE: requested %dx%d retained; transient options size %dx%d not persisted",
        g_s26dzDesktopW,g_s26dzDesktopH,oldW,oldH);
}
static void s26dz_install_save_options(void){
    static u32 tried;if(tried)return;tried=1;
    u8* base=(u8*)ext_GetModuleHandleA(0);if(!base)return;
    u8* target=base+0x5d1f0u;
    const u8 sig[16]={0x48,0x8b,0xc4,0x55,0x41,0x54,0x41,0x55,0x48,0x8d,0x68,0xa1,0x48,0x81,0xec,0xb0};
    if(!h20_mem_readable(target,sizeof(sig)))return;
    for(u32 i=0;i<sizeof(sig);++i)if(target[i]!=sig[i]){ext_Log(">>> S26DZ CONFIG SAVE GUARD unavailable: native signature mismatch");return;}
    i32 c=ext_MH_CreateHook(target,(void*)s26dz_save_options,(void**)&o_s26dzSaveOptions);
    i32 e=c==0?ext_MH_EnableHook(target):-1;
    ext_Log(">>> S26DZ CONFIG SAVE GUARD: hook %d enable %d; desktop request separated from window/render dimensions",c,e);
}
