/* S26ED: RENDER SCALE. VR SETTINGS > VIDEO publishes a 60..150% multiplier
   (VRCOMFORT O, slider index 0..18). It multiplies the OpenXR runtime's
   recommended eye size once, at the first LowLevelInit, so the swapchains,
   the HPL3 envelope and the private resolve all keep their existing 1:1
   contract at the new size. Swapchains cannot be resized while a session
   runs, so a change is saved to hpl3vr_render_scale.txt and applies on the
   next launch. SteamVR's own per-app resolution still multiplies on top. */
#define S26ED_SCALE_MIN     60u
#define S26ED_SCALE_MAX     150u
#define S26ED_SCALE_STEP    5u
#define S26ED_SCALE_DEFAULT 100u
#define S26ED_SCALE_INDEX_MAX ((S26ED_SCALE_MAX-S26ED_SCALE_MIN)/S26ED_SCALE_STEP)
#define S26ED_SCALE_MAX_DIM 8192
static u32 g_s26edScaleActive=S26ED_SCALE_DEFAULT,g_s26edScaleRequested=S26ED_SCALE_DEFAULT;
static u8 g_s26edScaleLoaded;
static u32 s26ed_scale_from_index(u32 index){
    if(index>S26ED_SCALE_INDEX_MAX)index=S26ED_SCALE_INDEX_MAX;
    return S26ED_SCALE_MIN+index*S26ED_SCALE_STEP;
}
static i32 s26ed_scale_valid(u32 pct){
    return pct>=S26ED_SCALE_MIN&&pct<=S26ED_SCALE_MAX&&(pct-S26ED_SCALE_MIN)%S26ED_SCALE_STEP==0u;
}
/* Leading decimal percent, optional trailing whitespace/newline. */
static i32 s26ed_parse_scale(const char* b,u32 n,u32* out){
    u32 i=0,v=0,digits=0;
    while(i<n&&(b[i]==' '||b[i]=='\t'))++i;
    while(i<n&&b[i]>='0'&&b[i]<='9'&&digits<4u){v=v*10u+(u32)(b[i]-'0');++i;++digits;}
    if(!digits)return 0;
    while(i<n&&(b[i]==' '||b[i]=='\t'||b[i]=='\r'||b[i]=='\n'))++i;
    if(i!=n||!s26ed_scale_valid(v))return 0;
    *out=v;return 1;
}
/* Runtime-recommended dimension -> scaled even dimension, 1:1 at 100%. */
static i32 s26ed_scaled_dim(i32 v,u32 pct){
    if(v<=0)return v;
    if(!s26ed_scale_valid(pct)||pct==100u)return v;
    i64 s=((i64)v*(i64)pct+99)/100;s=(s+1)&~1LL;
    if(s<16)s=16;if(s>S26ED_SCALE_MAX_DIM)s=S26ED_SCALE_MAX_DIM&~1;
    return (i32)s;
}
static i32 make_sibling_path(char* out,u32 cap,const char* leaf);
static void s26ed_load_render_scale(void){
    if(g_s26edScaleLoaded)return;g_s26edScaleLoaded=1;
    char path[520];if(!make_sibling_path(path,sizeof(path),"hpl3vr_render_scale.txt"))return;
    void* f=ext_fopen(path,"rb");if(!f)return;
    char b[16];u64 got=ext_fread(b,1,sizeof(b),f);ext_fclose(f);
    u32 pct=0;if(got&&got<sizeof(b)&&s26ed_parse_scale(b,(u32)got,&pct)){g_s26edScaleActive=pct;g_s26edScaleRequested=pct;}
    else ext_Log(">>> S26ED RENDER SCALE: ignored malformed %s; using %u%%",path,g_s26edScaleActive);
}
/* VRCOMFORT O <index>: remember the request for the next launch. */
static void s26ed_request_render_scale(u32 index){
    u32 pct=s26ed_scale_from_index(index);
    if(pct==g_s26edScaleRequested)return;
    g_s26edScaleRequested=pct;
    char path[520];if(!make_sibling_path(path,sizeof(path),"hpl3vr_render_scale.txt"))return;
    char b[8];u32 n=0;if(pct>=100u)b[n++]=(char)('0'+pct/100u);b[n++]=(char)('0'+(pct/10u)%10u);b[n++]=(char)('0'+pct%10u);b[n++]='\n';
    void* f=ext_fopen(path,"wb");if(!f)return;ext_fwrite(b,1,n,f);ext_fclose(f);
    ext_Log(">>> S26ED RENDER SCALE: %u%% saved for the next launch (this session keeps %u%%)",pct,g_s26edScaleActive);
}
