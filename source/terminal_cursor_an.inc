/* SOMA 7c424e60: cImGui::SetShowMouse changes +0x751, which is ALSO
   the hit-test gate in 1402f9b70. Never hide that flag during widgets.
   End (14030e3b0) draws the automatic cursor only when +0x750 is true.
   DrawMouse (14030e620) submits an explicitly requested cursor, while
   140217000 submits the legacy cGuiSet cursor. All three routes below
   affect presentation of registered terminal GUIs only. */
typedef void (__attribute__((ms_abi)) *S26ANEnd)(void*);
typedef void (__attribute__((ms_abi)) *S26ANMouse)(void*,void*,const float*,const float*);
typedef u64 (__attribute__((ms_abi)) *S26ANLegacyMouse)(void*);
static S26ANEnd o_s26anEnd;
static S26ANMouse o_s26anMouse;
static S26ANLegacyMouse o_s26anLegacyMouse;
static const void* g_s26anTerminalSet;
static i32 g_s26anCursorTried,g_s26anCursorReady;
// Terminal presentation survives finger withdrawal and the short walk-up state.
// Registration is per exact terminal GUI, never a global GUI visibility switch.
static const void* g_s26bvGui[128];
static const void* g_s26bvSet[128];
static u32 g_s26bvGuiCount;
static void s26bv_register_terminal(void* gui){
    if(!gui || !h20_mem_readable((u8*)gui+0x18,8))return;
    for(u32 i=0;i<g_s26bvGuiCount;i++)if(g_s26bvGui[i]==gui)return;
    if(g_s26bvGuiCount>=128u)return;
    u32 i=g_s26bvGuiCount++;g_s26bvGui[i]=gui;g_s26bvSet[i]=*(const void**)((u8*)gui+0x18);
}
static i32 s26bv_cursor_owned(const void* self,i32 legacy){
    if(!g_s26anCursorReady||g_h576mScriptRuntimePublished!=1||!p2_xr_on()||!p2_xr_running()||g_h576bfMapTransitionActive)return 0;
    for(u32 i=0;i<g_s26bvGuiCount;i++)if(self==(legacy?g_s26bvSet[i]:g_s26bvGui[i]))return 1;
    return 0;
}
static void __attribute__((ms_abi)) s26an_gui_end(void* self){
    if(!o_s26anEnd)return;
    if(s26bv_cursor_owned(self,0)){
        u8* autoDraw=(u8*)self+0x750;u8 saved=*autoDraw;*autoDraw=0;
        o_s26anEnd(self);*autoDraw=saved;
    }else o_s26anEnd(self);
}
static void __attribute__((ms_abi)) s26an_gui_mouse(void* self,void* gfx,const float* offset,const float* size){
    if(s26bv_cursor_owned(self,0))return;
    if(o_s26anMouse)o_s26anMouse(self,gfx,offset,size);
}
static u64 __attribute__((ms_abi)) s26an_legacy_mouse(void* self){
    if(s26bv_cursor_owned(self,1))return 1;
    return o_s26anLegacyMouse?o_s26anLegacyMouse(self):1;
}
static void s26an_cursor_install(void){
    if(g_s26anCursorTried)return;g_s26anCursorTried=1;
    u8* base=(u8*)ext_GetModuleHandleA(0);if(!base)return;
    const u32 offsets[3]={0x30e3b0,0x30e620,0x217000};
    const u8 sig[3][12]={
        {0x48,0x8b,0xc4,0x41,0x54,0x48,0x81,0xec,0xd0,0,0,0},
        {0x48,0x8b,0xc4,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x81,0xec},
        {0x4c,0x8b,0xdc,0x41,0x55,0x48,0x81,0xec,0x30,0x01,0,0}};
    for(i32 j=0;j<3;++j){if(!h20_mem_readable(base+offsets[j],12))return;for(i32 i=0;i<12;++i)if(base[offsets[j]+i]!=sig[j][i])return;}
    /* Verify the public cImGui::GetSet getter used at a live Begin callback. */
    const u8 getter[5]={0x48,0x8b,0x41,0x18,0xc3};
    for(i32 i=0;i<5;++i)if(base[0x3b1330+i]!=getter[i])return;
    if(ext_MH_CreateHook(base+offsets[0],(void*)s26an_gui_end,(void**)&o_s26anEnd)||ext_MH_EnableHook(base+offsets[0]))return;
    if(ext_MH_CreateHook(base+offsets[1],(void*)s26an_gui_mouse,(void**)&o_s26anMouse)||ext_MH_EnableHook(base+offsets[1]))return;
    if(ext_MH_CreateHook(base+offsets[2],(void*)s26an_legacy_mouse,(void**)&o_s26anLegacyMouse)||ext_MH_EnableHook(base+offsets[2]))return;
    g_s26anCursorReady=1;
    ext_Log(">>> S26AN TERMINAL CURSOR DRAW FILTER READY: automatic, explicit and legacy drawing only; ImGui hit-test visibility preserved");
}

