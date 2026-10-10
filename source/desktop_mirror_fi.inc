/* Left eye only, after both eye submissions and before the desktop swap.
   Scale into the existing single-sample window stage, then copy 1:1 to
   GL_BACK: scaled single->multisample blits are not legal. No XR writes. */
static i32 s26fi_fit(i32 sw,i32 sh,i32 dw,i32 dh,i32 rect[4]){
    if(sw<1||sh<1||dw<1||dh<1||sw>32768||sh>32768||dw>32768||dh>32768)return 0;
    i32 w=dw,h=(i32)((i64)dw*sh/sw);
    if(h>dh){h=dh;w=(i32)((i64)dh*sw/sh);}
    if(w<1||h<1)return 0;
    rect[0]=(dw-w)/2;rect[1]=(dh-h)/2;rect[2]=rect[0]+w;rect[3]=rect[1]+h;return 1;
}
static void s26fi_desktop_mirror(void){
    if(!g_s26fiMirrorEnabled||!g_s26fiMirrorReady||!p2_xr_on()||!p2_xr_running()||
       g_h5755asUiIslandActive||g_h576bfMapTransitionActive||
       __atomic_load_n(&g_h5755bhPresentationState,__ATOMIC_ACQUIRE)!=H5755BH_GAMEPLAY_VR||
       !h5750y_resolve_ready_for_eye(0))return;
    i32 w=0,h=0,rect[4];
    if(!s26cb_flat_drawable_extent(&w,&h)||
       !s26fi_fit(g_h5750yResolveW,g_h5750yResolveH,w,h,rect))return;
    typedef void (__attribute__((ms_abi)) *Push)(u32);
    typedef void (__attribute__((ms_abi)) *Pop)(void);
    typedef void (__attribute__((ms_abi)) *Mask)(u8,u8,u8,u8);
    static Push push;static Pop pop;static Mask mask;
    static PFN_H5754T_GlClearColor clearColor;static PFN_H5754T_GlClear clear;
    if(!push){void* gl=ext_GetModuleHandleA("opengl32.dll");if(!gl)return;
        push=(Push)ext_GetProcAddress(gl,"glPushAttrib");pop=(Pop)ext_GetProcAddress(gl,"glPopAttrib");
        mask=(Mask)ext_GetProcAddress(gl,"glColorMask");
        clearColor=(PFN_H5754T_GlClearColor)ext_GetProcAddress(gl,"glClearColor");
        clear=(PFN_H5754T_GlClear)ext_GetProcAddress(gl,"glClear");}
    PFN_H5750V_BindFramebuffer bind=h5750v_bind_fbo();
    PFN_H5750V_BlitFramebuffer blit=h5750v_blit();
    if(!push||!pop||!mask||!clearColor||!clear||!bind||!blit||!s26ec_ready(w,h))return;
    h5750v_resolve_read_buffer();if(!p_h5750vReadBuffer||!s26ec_draw)return;
    i32 rd=0,dr=0,back=0,src=0;
    ext_glGetIntegerv(0x8CAAu,&rd);ext_glGetIntegerv(0x8CA6u,&dr);
    /* Save enables, colour mask/clear value and original draw selection. */
    push(0x00006000u);
    ext_glDisable(0x0C11u);ext_glDisable(0x8DB9u);mask(1,1,1,1);
    bind(0x8CA9u,s26ec_fbo);s26ec_draw(0x8CE0u);clearColor(0,0,0,1);clear(0x4000u);
    bind(0x8CA8u,g_h5750yResolveFbo[0]);ext_glGetIntegerv(0x0C02u,&src);p_h5750vReadBuffer(0x8CE0u);
    blit(0,0,g_h5750yResolveW,g_h5750yResolveH,rect[0],rect[1],rect[2],rect[3],0x4000u,0x2601u);
    p_h5750vReadBuffer((u32)src);
    bind(0x8CA8u,s26ec_fbo);p_h5750vReadBuffer(0x8CE0u);
    bind(0x8CA9u,0);ext_glGetIntegerv(0x0C01u,&back);s26ec_draw(0x0405u);
    blit(0,0,w,h,0,0,w,h,0x4000u,0x2600u);
    s26ec_draw((u32)back);bind(0x8CA8u,(u32)rd);bind(0x8CA9u,(u32)dr);pop();
    static u32 logged;if(!logged++){ext_Log(">>> S26FI DESKTOP MIRROR: left eye %dx%d -> window %dx%d; aspect preserved, MSAA-safe staged copy",g_h5750yResolveW,g_h5750yResolveH,w,h);}
}
