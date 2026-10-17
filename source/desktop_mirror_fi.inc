#include "desktop_combine_hq.inc"
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
/* S26HP: the gameplay drawable can exceed the desktop. Fit the complete eye
   to its visible monitor intersection, not the off-screen rendering envelope.
   All rectangles below are client top-left coordinates until the final GL flip. */
static i32 s26hp_visible_fit(i32 sw,i32 sh,i32 dw,i32 dh,i32 cw,i32 ch,
                           i32 left,i32 top,i32 right,i32 bottom,i32 rect[4]){
    if(cw<1||ch<1||cw>32768||ch>32768||dw<1||dh<1||dw>32768||dh>32768)return 0;
    if(left<0)left=0;if(top<0)top=0;if(right>cw)right=cw;if(bottom>ch)bottom=ch;
    if(right<=left||bottom<=top)return 0;
    i32 x0=(i32)((i64)left*dw/cw),x1=(i32)((i64)right*dw/cw);
    i32 y0=dh-(i32)((i64)bottom*dh/ch),y1=dh-(i32)((i64)top*dh/ch);
    if(sw==0&&sh==0){rect[0]=0;rect[1]=0;rect[2]=x1-x0;rect[3]=y1-y0;}
    else if(!s26fi_fit(sw,sh,x1-x0,y1-y0,rect))return 0;
    rect[0]+=x0;rect[2]+=x0;rect[1]+=y0;rect[3]+=y0;return 1;
}
static i32 s26hp_mirror_rect(i32 sw,i32 sh,i32 dw,i32 dh,i32 rect[4]){
    typedef struct {u32 size;H5754DRect monitor,work;u32 flags;} Info;
    typedef void* (__attribute__((ms_abi)) *FromPoint)(H5754DPoint,u32);
    typedef i32 (__attribute__((ms_abi)) *GetInfo)(void*,Info*);
    static FromPoint fromPoint;static GetInfo getInfo;
    h5754d_resolve_platform();
    if(!fromPoint||!getInfo){void* u=ext_GetModuleHandleA("USER32.dll");if(u){
        fromPoint=(FromPoint)ext_GetProcAddress(u,"MonitorFromPoint");
        getInfo=(GetInfo)ext_GetProcAddress(u,"GetMonitorInfoA");}}
    void* wnd=s26cb_menu_render_window();H5754DRect client;H5754DPoint origin={0,0};
    if(!wnd||!fromPoint||!getInfo||!p_h5754dGetClientRect||!p_h5754dClientToScreen||
       !p_h5754dGetClientRect(wnd,&client)||!p_h5754dClientToScreen(wnd,&origin))
        return s26fi_fit(sw?sw:dw,sh?sh:dh,dw,dh,rect);
    i32 cw=client.right-client.left,ch=client.bottom-client.top;
    /* Use the pre-envelope footprint to choose the intended monitor. */
    i32 aw=cw,ah=ch;
    if(g_h5755akPopupActive&&g_h5755akSavedClientW>0&&g_h5755akSavedClientH>0){
        aw=g_h5755akSavedClientW;ah=g_h5755akSavedClientH;}
    H5754DPoint anchor={origin.x+aw/2,origin.y+ah/2};Info info;info.size=sizeof(info);
    if(!getInfo(fromPoint(anchor,2),&info))return s26fi_fit(sw?sw:dw,sh?sh:dh,dw,dh,rect);
    return s26hp_visible_fit(sw,sh,dw,dh,cw,ch,info.monitor.left-origin.x,
        info.monitor.top-origin.y,info.monitor.right-origin.x,info.monitor.bottom-origin.y,rect);
}
static void s26fi_desktop_mirror(void){
    if(!g_s26fiMirrorEnabled||!g_s26fiMirrorReady||!p2_xr_on()||!p2_xr_running()||
       g_h5755asUiIslandActive||g_h576bfMapTransitionActive||
       __atomic_load_n(&g_h5755bhPresentationState,__ATOMIC_ACQUIRE)!=H5755BH_GAMEPLAY_VR||
       !h5750y_resolve_ready_for_eye(0))return;
    i32 w=0,h=0,rect[4];
    if(!s26cb_flat_drawable_extent(&w,&h)||
       !s26hp_mirror_rect(g_h5750yResolveW,g_h5750yResolveH,w,h,rect))return;
    float bounds[2][4],box[4];i32 combined=0,full[4];
    if(h5750y_resolve_ready_for_eye(1)&&s26hp_mirror_rect(0,0,w,h,full)){
        i32 valid=1;
        for(i32 e=0;e<2;e++){float f[4],t[4];i32 ew,eh;
            if(!h5750x_eye_contract(e,f,&ew,&eh)){valid=0;break;}
            for(i32 k=0;k<4;k++)if(!h5750x_tan_checked(f[k],&t[k]))valid=0;
            bounds[e][0]=t[0];bounds[e][1]=t[3];bounds[e][2]=t[1];bounds[e][3]=t[2];}
        if(valid&&s26hq_box(bounds[0],bounds[1],full[2]-full[0],full[3]-full[1],box)&&s26hq_init())combined=1;
    }
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
    if(!push||!pop||!mask||!clearColor||!clear||!bind||!blit||(!combined&&!s26ec_ready(w,h)))return;
    h5750v_resolve_read_buffer();
    if(!s26ec_draw)s26ec_draw=(PFN_H5754AQ_DrawBuffer)ext_GetProcAddress(ext_GetModuleHandleA("opengl32.dll"),"glDrawBuffer");
    if(!p_h5750vReadBuffer||!s26ec_draw)return;
    i32 rd=0,dr=0,back=0,src=0;
    ext_glGetIntegerv(0x8CAAu,&rd);ext_glGetIntegerv(0x8CA6u,&dr);
    /* Save enables, colour mask/clear value and original draw selection. */
    push(0x000fffffu);
    ext_glDisable(0x0C11u);ext_glDisable(0x8DB9u);mask(1,1,1,1);
    if(combined){
        bind(0x8CA9u,0);ext_glGetIntegerv(0x0C01u,&back);s26ec_draw(0x0405u);
        clearColor(0,0,0,1);clear(0x4000u);
        s26hq_draw(bounds[0],bounds[1],box,full,1);
        s26ec_draw((u32)back);bind(0x8CA8u,(u32)rd);bind(0x8CA9u,(u32)dr);pop();
        static u32 logged;if(!logged++){ext_Log(">>> S26HQ COMBINED MIRROR ACTIVE: visible %dx%d, drawable %dx%d; one desktop draw, no eye writes",full[2]-full[0],full[3]-full[1],w,h);}return;
    }
    bind(0x8CA9u,s26ec_fbo);s26ec_draw(0x8CE0u);clearColor(0,0,0,1);clear(0x4000u);
    bind(0x8CA8u,g_h5750yResolveFbo[0]);ext_glGetIntegerv(0x0C02u,&src);p_h5750vReadBuffer(0x8CE0u);
    blit(0,0,g_h5750yResolveW,g_h5750yResolveH,rect[0],rect[1],rect[2],rect[3],0x4000u,0x2601u);
    p_h5750vReadBuffer((u32)src);
    bind(0x8CA8u,s26ec_fbo);p_h5750vReadBuffer(0x8CE0u);
    bind(0x8CA9u,0);ext_glGetIntegerv(0x0C01u,&back);s26ec_draw(0x0405u);
    blit(0,0,w,h,0,0,w,h,0x4000u,0x2600u);
    s26ec_draw((u32)back);bind(0x8CA8u,(u32)rd);bind(0x8CA9u,(u32)dr);pop();
    static i32 last[6];if(last[0]!=w||last[1]!=h||last[2]!=rect[0]||last[3]!=rect[1]||last[4]!=rect[2]||last[5]!=rect[3]){
        last[0]=w;last[1]=h;for(i32 k=0;k<4;k++)last[k+2]=rect[k];
        ext_Log(">>> S26HP DESKTOP MIRROR: left eye %dx%d -> drawable %dx%d visible fit [%d,%d,%d,%d]; full eye, MSAA-safe",g_h5750yResolveW,g_h5750yResolveH,w,h,rect[0],rect[1],rect[2],rect[3]);}
}
