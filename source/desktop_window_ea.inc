/* VR desktop presentation uses an undecorated WINDOWED SDL carrier. Windows
   clamps a full-monitor bordered outer rect, reducing the requested client.
   Keep SDL's style bookkeeping in sync; never change the display mode. */
typedef void (*S26EABordered)(void*,i32);
typedef u32 (*S26EAFlags)(void*);
static i32 s26ea_desktop_window(void){
    if(g_s26dzDesktopW<320||g_s26dzDesktopH<200)return 0;
    h5755ak_resolve_window_api();h5755as_resolve_sdl_window_api();
    void* m=ext_GetModuleHandleA("SDL2.dll");
    S26EABordered bordered=m?(S26EABordered)ext_GetProcAddress(m,"SDL_SetWindowBordered"):0;
    S26EAFlags flags=m?(S26EAFlags)ext_GetProcAddress(m,"SDL_GetWindowFlags"):0;
    if(!bordered||!flags||!p_h5755asSDLGLGetCurrentWindow||!p_h5755asSDLSetWindowSize)return 0;
    void* sw=p_h5755asSDLGLGetCurrentWindow();if(!sw)return 0;
    /* Native fullscreen is outside this correction's contract. */
    if(flags(sw)&1u)return 0;
    h5755ag_resolve_query_apis();void* dc=p_h5755agWglGetCurrentDC?p_h5755agWglGetCurrentDC():0;
    void* wnd=dc&&p_h5755sWindowFromDC?p_h5755sWindowFromDC(dc):0;
    if(!wnd||!p_h5754dGetClientRect||!p_h5755akGetWindowRect||!p_h5755akGetWindowLongPtrA)return 0;
    H5754DRect cr,wr; i32 bw=0,bh=0;
    if(p_h5754dGetClientRect(wnd,&cr)){bw=cr.right-cr.left;bh=cr.bottom-cr.top;}
    if(!(flags(sw)&0x10u))bordered(sw,0);
    p_h5755asSDLSetWindowSize(sw,g_s26dzDesktopW,g_s26dzDesktopH);
    if(!p_h5754dGetClientRect(wnd,&cr)||!p_h5755akGetWindowRect(wnd,&wr)||
       cr.right-cr.left!=g_s26dzDesktopW||cr.bottom-cr.top!=g_s26dzDesktopH){
        ext_Log(">>> S26EA DESKTOP SIZE REJECT: requested %dx%d; retain actual drawable reconciliation",g_s26dzDesktopW,g_s26dzDesktopH);return 0;
    }
    g_h5755akWindow=wnd;g_h5755asSDLWindow=sw;
    g_h5755akSavedStyle=p_h5755akGetWindowLongPtrA(wnd,-16);g_h5755akSavedWindowRect=wr;
    g_h5755akSavedClientW=g_s26dzDesktopW;g_h5755akSavedClientH=g_s26dzDesktopH;
    g_s26dySavedSDLW=g_s26dzDesktopW;g_s26dySavedSDLH=g_s26dzDesktopH;
    __atomic_store_n(&g_h5755akSnapshotValid,1u,__ATOMIC_RELEASE);
    static u32 logs;if(logs++<24u)ext_Log(">>> S26EA EXACT DESKTOP CLIENT: %dx%d -> %dx%d; SDL borderless windowed, saved desktop resolution retained",bw,bh,g_s26dzDesktopW,g_s26dzDesktopH);
    return 1;
}
