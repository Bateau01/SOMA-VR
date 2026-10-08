/* Experimental main-view opaque-material foveation. Shadow/depth/UI stages
   never enter this scope. Unsupported contexts and invalid gaze stay full rate. */
static volatile i32 g_s26efFoveation;
static u32 g_s26efFoveationCalls;
static u32 g_s26efFoveationErrors;
/* Cumulative pass counts, not FPS estimates. Read atomically from menu updates. */
static u32 g_s26egDFRStats[9];
static u32 g_s26eiMeasureEpoch;
/* lock, invalid, old, future, nonfinite, accepted extended-age, accepted predicted */
static u32 g_s26ehGazeStats[7];
static void s26eg_dfr_report(i32 enabled){
    u32 g[7];for(i32 i=0;i<7;++i)g[i]=__atomic_load_n(&g_s26ehGazeStats[i],__ATOMIC_RELAXED);
    ext_Log(">>> S26EH DFR GAZE: lock %u invalid %u old %u future %u nonfinite %u accepted-age-50-to-100ms %u accepted-prediction-10-to-100ms %u",g[0],g[1],g[2],g[3],g[4],g[5],g[6]);
    u32 s[9];for(i32 i=0;i<9;++i)s[i]=__atomic_load_n(&g_s26egDFRStats[i],__ATOMIC_RELAXED);
    ext_Log(">>> S26EG DFR STATUS: requested %s | passes %u applied %u gaze-skip %u scope-skip %u unsupported %u target-skip %u foreign-VRS %u setup-errors %u prior-GL-errors %u | counts are not performance measurements",enabled?"ON":"OFF",s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8]);
}
static void s26eg_set_foveation(i32 enabled){
    i32 old=__atomic_exchange_n(&g_s26efFoveation,enabled,__ATOMIC_RELAXED);
    if(old!=enabled){__atomic_fetch_add(&g_s26eiMeasureEpoch,1u,__ATOMIC_RELAXED);s26eg_dfr_report(enabled);}
}
static void s26eg_dfr_count(i32 index){__atomic_fetch_add(&g_s26egDFRStats[index],1u,__ATOMIC_RELAXED);}
typedef void (__attribute__((ms_abi)) *S26EFPass)(void*);
static S26EFPass o_s26efGbuffer;
static void* g_s26efGLContext;
static i32 g_s26efGLReady,g_s26efTileW,g_s26efTileH;
static u32 g_s26efRateTexture;
static i32 g_s26efRateW,g_s26efRateH;
static u8 g_s26efRatePixels[512u*512u];
static void* (__attribute__((ms_abi)) *p_s26efContext)(void);
static const u8* (__attribute__((ms_abi)) *p_s26efString)(u32);
static void (__attribute__((ms_abi)) *p_s26efGen)(i32,u32*);
static void (__attribute__((ms_abi)) *p_s26efDelete)(i32,const u32*);
static void (__attribute__((ms_abi)) *p_s26efStorage)(u32,i32,u32,i32,i32);
static void (__attribute__((ms_abi)) *p_s26efUpload)(u32,i32,i32,i32,i32,i32,u32,u32,const void*);
static void (__attribute__((ms_abi)) *p_s26efPixelStore)(u32,i32);
static void (__attribute__((ms_abi)) *p_s26efBindBuffer)(u32,u32);
static void (__attribute__((ms_abi)) *p_s26efRateBind)(u32);
static void (__attribute__((ms_abi)) *p_s26efPalette)(u32,u32,i32,const u32*);
static void (__attribute__((ms_abi)) *p_s26efGetPalette)(u32,u32,u32*);
static u32 (__attribute__((ms_abi)) *p_s26efError)(void);
static u32 s26eg_drain_gl_errors(void){
    u32 first=0;for(i32 i=0;i<16;++i){u32 e=p_s26efError();if(!e)break;if(!first)first=e;}return first;
}
static i32 s26ef_extension(const u8* names,const char* name){
    if(!names)return 0;
    for(u32 i=0;names[i];){u32 j=0;while(names[i+j]&&names[i+j]!=' '&&name[j]&&names[i+j]==(u8)name[j])++j;
        if(!name[j]&&(!names[i+j]||names[i+j]==' '))return 1;
        while(names[i]&&names[i]!=' ')++i;if(names[i])++i;}
    return 0;
}
static i32 s26ef_foveation_gl(void){
    void* ogl=ext_GetModuleHandleA("opengl32.dll");if(!ogl)return 0;
    if(!p_s26efContext)p_s26efContext=(void*)ext_GetProcAddress(ogl,"wglGetCurrentContext");
    void* ctx=p_s26efContext?p_s26efContext():0;if(!ctx)return 0;
    if(ctx==g_s26efGLContext)return g_s26efGLReady;
    g_s26efGLContext=ctx;g_s26efGLReady=0;g_s26efRateTexture=0;g_s26efRateW=g_s26efRateH=0;
    PFN_H5750A_WglGetProcAddress wg=(void*)ext_GetProcAddress(ogl,"wglGetProcAddress");
#define S26EF_PROC(dst,name) dst=(void*)s26_gl_proc(ogl,wg,name);if(!dst)return 0
    S26EF_PROC(p_s26efString,"glGetString");
    if(!s26ef_extension(p_s26efString(0x1f03u),"GL_NV_shading_rate_image")){ext_Log(">>> S26EF DFR unavailable: GL_NV_shading_rate_image not supported; full quality retained");return 0;}
    S26EF_PROC(p_s26efGen,"glGenTextures");S26EF_PROC(p_s26efDelete,"glDeleteTextures");
    S26EF_PROC(p_s26efStorage,"glTexStorage2D");S26EF_PROC(p_s26efUpload,"glTexSubImage2D");
    S26EF_PROC(p_s26efPixelStore,"glPixelStorei");S26EF_PROC(p_s26efBindBuffer,"glBindBuffer");
    S26EF_PROC(p_s26efRateBind,"glBindShadingRateImageNV");S26EF_PROC(p_s26efPalette,"glShadingRateImagePaletteNV");
    S26EF_PROC(p_s26efGetPalette,"glGetShadingRateImagePaletteNV");S26EF_PROC(p_s26efError,"glGetError");
#undef S26EF_PROC
    ext_glGetIntegerv(0x955cu,&g_s26efTileW);ext_glGetIntegerv(0x955du,&g_s26efTileH);
    if(g_s26efTileW<1||g_s26efTileH<1||g_s26efTileW>256||g_s26efTileH>256)return 0;
    g_s26efGLReady=1;ext_Log(">>> S26EF DFR supported: %dx%d shading-rate tiles; main opaque-material pass only",g_s26efTileW,g_s26efTileH);return 1;
}
#include "foveation_tuning_ei.inc"
#include "foveation_timing_ei.inc"
static i32 s26ei_read_foveation_gaze(float* gaze){
    if(!s26s_eye_lock()){__atomic_fetch_add(&g_s26ehGazeStats[0],1u,__ATOMIC_RELAXED);return 0;}S26SEyeSample sample=g_s26sEyeSample;s26s_eye_unlock();
    u8* xr=(u8*)p2_xr_obj();i64 now=xr?*(i64*)(xr+0xe8):0;
    if(!sample.valid||!sample.headValid||now<=0){__atomic_fetch_add(&g_s26ehGazeStats[1],1u,__ATOMIC_RELAXED);return 0;}
    /* Same bounded timestamp policy as the producer and gameplay gaze bridge.
       Runtime gaze can be delayed or predicted. Never reuse an invalid sample. */
    if(sample.time<now-100000000LL){__atomic_fetch_add(&g_s26ehGazeStats[2],1u,__ATOMIC_RELAXED);return 0;}
    if(sample.time>now+100000000LL){__atomic_fetch_add(&g_s26ehGazeStats[3],1u,__ATOMIC_RELAXED);return 0;}
    if(!s26s_pose_finite(&sample.eye)||!s26s_pose_finite(&sample.head)){__atomic_fetch_add(&g_s26ehGazeStats[4],1u,__ATOMIC_RELAXED);return 0;}
    if(sample.time<now-50000000LL)__atomic_fetch_add(&g_s26ehGazeStats[5],1u,__ATOMIC_RELAXED);
    if(sample.time>now+10000000LL)__atomic_fetch_add(&g_s26ehGazeStats[6],1u,__ATOMIC_RELAXED);
    XrQuaternionf inv={-sample.head.orientation.x,-sample.head.orientation.y,-sample.head.orientation.z,sample.head.orientation.w};
    float forward[3]={0,0,-1},raw[3];s26s_quat_rotate(&sample.eye.orientation,forward,raw);s26s_quat_rotate(&inv,raw,gaze);s26ei_gaze_guard(now,sample.time,gaze,1);return 1;
}
static i32 s26ef_foveation_gaze(float* gaze){
    i32 valid=s26ei_read_foveation_gaze(gaze);if(!valid)s26ei_gaze_guard(0,0,gaze,0);return valid;
}
/* The light fix has already replaced bf4 with asymmetric-eye coefficients.
   Validate the projection itself; do not mistake those corrected coefficients
   for the native symmetric viewport values expected by its conversion helper. */
static i32 s26ef_projection_valid(const u8* r){
    i32 w=*(const i32*)(r+0x40),h=*(const i32*)(r+0x44);float out[4];
    float reference[4]={1,1,-.5f*(float)w,-.5f*(float)h};
    return s26do_light_coefficients((const float*)(r+0xaa4),*(const float*)(r+0xbe4),w,h,reference,out);
}
static void __attribute__((ms_abi)) s26ef_gbuffer_impl(void* renderer){
    if(!o_s26efGbuffer)return;
    u8* r=(u8*)renderer;float gaze[3];i32 vp[4]={0},fb=0;
    if(!__atomic_load_n(&g_s26efFoveation,__ATOMIC_RELAXED)){s26ei_opaque_draw(renderer,0);return;}
    u32 calls=__atomic_add_fetch(&g_s26egDFRStats[0],1u,__ATOMIC_RELAXED);if(calls%1200u==0)s26eg_dfr_report(1);
    if(!r||renderer!=g_s26doLightRenderer||!g_s26doLightFrustum||!h20_mem_readable(r+0xbf4,16)||*(void**)(r+0x20)!=g_s26doLightFrustum){s26eg_dfr_count(3);s26ei_opaque_draw(renderer,2);return;}
    if(!s26ef_foveation_gaze(gaze)){s26eg_dfr_count(2);s26ei_opaque_draw(renderer,2);return;}
    if(!s26ef_projection_valid(r)){s26eg_dfr_count(5);s26ei_opaque_draw(renderer,2);return;}
    if(!s26ef_foveation_gl()){s26eg_dfr_count(4);s26ei_opaque_draw(renderer,2);return;}
    if(ext_glIsEnabled(0x9563u)){s26eg_dfr_count(6);s26ei_opaque_draw(renderer,2);return;}
    ext_glGetIntegerv(0x8ca6u,&fb);ext_glGetIntegerv(0x0ba2u,vp);
    i32 w=vp[2],h=vp[3],tw=(w+g_s26efTileW-1)/g_s26efTileW,th=(h+g_s26efTileH-1)/g_s26efTileH;
    if(!fb||vp[0]||vp[1]||w!=*(i32*)(r+0x40)||h!=*(i32*)(r+0x44)||!s26ef_rate_mask(g_s26efRatePixels,tw,th,w,h,g_s26efTileW,g_s26efTileH,(float*)(r+0xaa4),gaze)){s26eg_dfr_count(5);s26ei_opaque_draw(renderer,2);return;}
    /* GL errors are sticky across callers. Do not blame a prior engine/hand
       error on DFR or discard a healthy rate texture because of that error. */
    u32 priorError=s26eg_drain_gl_errors();if(priorError){s26eg_dfr_count(8);if(__atomic_load_n(&g_s26egDFRStats[8],__ATOMIC_RELAXED)<=4u)ext_Log(">>> S26EG DFR prior GL error 0x%x existed before setup; origin unassigned",priorError);}
    i32 oldTex=0,oldBuffer=0,unpack[4],oldRate=0;u32 oldPalette[3];
    ext_glGetIntegerv(0x8069u,&oldTex);ext_glGetIntegerv(0x88efu,&oldBuffer);ext_glGetIntegerv(0x955bu,&oldRate);
    const u32 keys[4]={0x0cf5u,0x0cf2u,0x0cf3u,0x0cf4u};
    for(i32 i=0;i<4;++i){ext_glGetIntegerv(keys[i],&unpack[i]);p_s26efPixelStore(keys[i],i==0?1:0);}
    p_s26efBindBuffer(0x88ecu,0);
    if(!g_s26efRateTexture||tw!=g_s26efRateW||th!=g_s26efRateH){
        if(g_s26efRateTexture)p_s26efDelete(1,&g_s26efRateTexture);
        p_s26efGen(1,&g_s26efRateTexture);ext_glBindTexture(0x0de1u,g_s26efRateTexture);p_s26efStorage(0x0de1u,1,0x8232u,tw,th);g_s26efRateW=tw;g_s26efRateH=th;
    }else ext_glBindTexture(0x0de1u,g_s26efRateTexture);
    p_s26efUpload(0x0de1u,0,0,0,tw,th,0x8d94u,0x1401u,g_s26efRatePixels);
    ext_glBindTexture(0x0de1u,(u32)oldTex);p_s26efBindBuffer(0x88ecu,(u32)oldBuffer);
    for(i32 i=0;i<4;++i)p_s26efPixelStore(keys[i],unpack[i]);
    for(u32 i=0;i<3;++i)p_s26efGetPalette(0,i,&oldPalette[i]);
    const u32 rates[3]={0x9565u,0x9568u,0x956bu};p_s26efPalette(0,0,3,rates);p_s26efRateBind(g_s26efRateTexture);
    u32 err=s26eg_drain_gl_errors();if(!err){ext_glEnable(0x9563u);err=s26eg_drain_gl_errors();}
    if(err)ext_glDisable(0x9563u);else s26eg_dfr_count(1);
    s26ei_opaque_draw(renderer,err?2:1);
    ext_glDisable(0x9563u);p_s26efRateBind((u32)oldRate);p_s26efPalette(0,0,3,oldPalette);
    /* A failed allocation/upload must not poison subsequent frames with a
       cached texture size. Delete only after restoring all caller bindings. */
    if(err){
        s26eg_dfr_count(7);
        if(g_s26efRateTexture)p_s26efDelete(1,&g_s26efRateTexture);
        g_s26efRateTexture=0;g_s26efRateW=g_s26efRateH=0;
        if(g_s26efFoveationErrors++<4u)ext_Log(">>> S26EF DFR setup failed: GL error 0x%x; full-rate frame retained",err);
    }
    if(!err&&g_s26efFoveationCalls++<4u)ext_Log(">>> S26EF DFR applied: main GBuffer %dx%d gaze %.3f/%.3f/%.3f; shadow, lighting and UI passes remain full rate",w,h,gaze[0],gaze[1],gaze[2]);
}
static void __attribute__((ms_abi)) s26ef_gbuffer(void* renderer){
 s26ef_gbuffer_impl(renderer);
}
static void s26ef_install_foveation(void){
    static u8 tried;if(tried||(!g_s26efFoveation&&!g_s26eiDFRTiming))return;tried=1;
    u8* base=(u8*)ext_GetModuleHandleA(0);u8* target=base?base+0x285070u:0;
    const u8 sig[13]={0x48,0x8b,0xc4,0x48,0x89,0x48,0x08,0x48,0x81,0xec,0x98,0,0};
    if(!target||!h20_mem_readable(target,sizeof(sig)))return;
    for(u32 i=0;i<sizeof(sig);++i)if(target[i]!=sig[i]){ext_Log(">>> S26EF DFR unavailable: GBuffer signature mismatch");return;}
    i32 cr=ext_MH_CreateHook(target,(void*)s26ef_gbuffer,(void**)&o_s26efGbuffer);i32 er=cr==0?ext_MH_EnableHook(target):-999;
    ext_Log(">>> S26EF DFR GBuffer hook %d/%d; default OFF, fresh tracked gaze required",cr,er);
}
