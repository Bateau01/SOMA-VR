/* S26ED: DEPTH FOR REPROJECTION. With XR_KHR_composition_layer_depth enabled
   by the runtime and VR SETTINGS > VIDEO > DEPTH FOR REPROJECTION on, each
   gameplay eye also submits the scene depth that HPL3 rendered for it, so the
   compositor can reproject by distance instead of treating the frame as a flat
   picture. The engine's own depth attachment is observed while the main eye's
   lights are set up, copied with the exact color FOV crop into a per-eye depth
   swapchain right after that eye's scene render, and chained to the matching
   projection view at xrEndFrame. Anything unexpected (format, size, missing
   attachment, GL or XR error) leaves the frame exactly as before. */
#define S26ED_XR_TYPE_DEPTH_INFO     1000010000
#define S26ED_XR_TYPE_PROJECTION_VIEW 48
#define S26ED_GL_DEPTH_COMPONENT16   0x81A5u
#define S26ED_GL_DEPTH_COMPONENT24   0x81A6u
#define S26ED_GL_DEPTH_COMPONENT32   0x81A7u
#define S26ED_GL_DEPTH_COMPONENT32F  0x8CACu
#define S26ED_GL_DEPTH24_STENCIL8    0x88F0u
#define S26ED_GL_DEPTH32F_STENCIL8   0x8CADu
#define S26ED_DEPTH_MAX_LAYERS 16u
#define S26ED_DEPTH_MAX_IMAGES 8u
typedef struct { i32 type; u32 pad0; const void* next; XrSwapchainSubImage subImage; float minDepth,maxDepth,nearZ,farZ; } S26EDDepthInfo;
_Static_assert(sizeof(S26EDDepthInfo)==64,"XrCompositionLayerDepthInfoKHR ABI");
typedef struct {
    const void* layers[S26ED_DEPTH_MAX_LAYERS];
    XrCompositionLayerProjection proj;
    XrCompositionLayerProjectionView views[2];
    S26EDDepthInfo depth[2];
} S26EDDepthFrame;

/* Exact GL internal format of a depth attachment from its reported sizes.
   A depth blit only works between identical formats, so anything else is 0. */
static u32 s26ed_depth_format(i32 depthBits,i32 stencilBits,u32 componentType){
    i32 isFloat=componentType==0x1406u,isUnorm=componentType==0x8C17u;
    if(!isFloat&&!isUnorm)return 0;
    if(stencilBits==8){
        if(isUnorm&&depthBits==24)return S26ED_GL_DEPTH24_STENCIL8;
        if(isFloat&&depthBits==32)return S26ED_GL_DEPTH32F_STENCIL8;
        return 0;
    }
    if(stencilBits!=0)return 0;
    if(isFloat)return depthBits==32?S26ED_GL_DEPTH_COMPONENT32F:0;
    if(depthBits==16)return S26ED_GL_DEPTH_COMPONENT16;
    if(depthBits==24)return S26ED_GL_DEPTH_COMPONENT24;
    if(depthBits==32)return S26ED_GL_DEPTH_COMPONENT32;
    return 0;
}
/* Near/far in physical metres from a column-major GL perspective matrix.
   Only a standard finite projection (window depth 0 = near, 1 = far) passes. */
static i32 s26ed_depth_planes(const float* p,float unitsPerMeter,float* nearM,float* farM){
    if(!(unitsPerMeter>=0.1f&&unitsPerMeter<=10.0f))return 0;
    if(p[3]!=0.0f||p[7]!=0.0f||p[11]!=-1.0f||p[15]!=0.0f)return 0;
    float a=p[10],b=p[14];
    if(!(a>-1000.0f&&a<-1.0f&&b<0.0f&&b>-1000000.0f))return 0;
    float n=b/(a-1.0f),f=b/(a+1.0f);
    n/=unitsPerMeter;f/=unitsPerMeter;
    if(!(n>=0.001f&&n<=10.0f&&f>n*1.01f&&f<=100000.0f))return 0;
    *nearM=n;*farM=f;return 1;
}
/* Copy the frame's single stereo projection layer and chain one depth info to
   each view. The color layer is untouched apart from that chain; any layer
   shape the runtime would not expect returns 0 and the original frame is used. */
static i32 s26ed_depth_chain(const XrFrameEndInfo* in,XrFrameEndInfo* out,S26EDDepthFrame* fr,const Handle swap[2],i32 swapW,i32 swapH,const float nearM[2],const float farM[2]){
    if(!in||!out||!fr||!in->layers||in->layerCount==0||in->layerCount>S26ED_DEPTH_MAX_LAYERS)return 0;
    i32 at=-1;
    for(u32 i=0;i<in->layerCount;++i){
        const XrCompositionLayerProjection* l=(const XrCompositionLayerProjection*)in->layers[i];
        if(!l)return 0;
        if(l->type==XR_TYPE_COMPOSITION_LAYER_PROJECTION){if(at>=0)return 0;at=(i32)i;}
    }
    if(at<0)return 0;
    const XrCompositionLayerProjection* src=(const XrCompositionLayerProjection*)in->layers[at];
    if(src->viewCount!=2u||!src->views)return 0;
    for(i32 e=0;e<2;++e){
        const XrCompositionLayerProjectionView* v=&src->views[e];
        const XrRect2Di* r=&v->subImage.imageRect;
        if(v->type!=S26ED_XR_TYPE_PROJECTION_VIEW||v->next)return 0;
        if(!swap[e]||r->offset.x<0||r->offset.y<0||r->extent.width<=0||r->extent.height<=0||
           r->extent.width>swapW-r->offset.x||r->extent.height>swapH-r->offset.y)return 0;
        if(!(nearM[e]>0.0f&&farM[e]>nearM[e]))return 0;
    }
    fr->proj=*src;
    for(i32 e=0;e<2;++e){
        S26EDDepthInfo* d=&fr->depth[e];zero_bytes(d,sizeof(*d));
        d->type=S26ED_XR_TYPE_DEPTH_INFO;d->subImage.swapchain=swap[e];
        d->subImage.imageRect=src->views[e].subImage.imageRect;d->subImage.imageArrayIndex=0;
        d->minDepth=0.0f;d->maxDepth=1.0f;d->nearZ=nearM[e];d->farZ=farM[e];
        fr->views[e]=src->views[e];fr->views[e].next=d;
    }
    fr->proj.views=fr->views;
    for(u32 i=0;i<in->layerCount;++i)fr->layers[i]=i==(u32)at?(const void*)&fr->proj:in->layers[i];
    *out=*in;out->layers=fr->layers;return 1;
}

/* ---- live state ---- */
typedef void (__attribute__((ms_abi)) *S26EDGlAttachParam)(u32,u32,u32,i32*);
typedef void (__attribute__((ms_abi)) *S26EDGlAttachRenderbuffer)(u32,u32,u32,u32);
typedef void (__attribute__((ms_abi)) *S26EDGlAttachTexture)(u32,u32,u32,i32);
typedef void (__attribute__((ms_abi)) *S26EDGlU32)(u32);
typedef void (__attribute__((ms_abi)) *S26EDGlBindRenderbuffer)(u32,u32);
typedef void (__attribute__((ms_abi)) *S26EDGlRenderbufferParam)(u32,u32,i32*);
typedef void (__attribute__((ms_abi)) *S26EDGlTextureLevelParam)(u32,i32,u32,i32*);
typedef u32 (__attribute__((ms_abi)) *S26EDGlGetError)(void);
typedef void (__attribute__((ms_abi)) *S26EDGlGetBooleanv)(u32,u8*);
typedef void (__attribute__((ms_abi)) *S26EDGlDepthMask)(u8);
typedef i32 (__attribute__((ms_abi)) *S26EDXrDestroySwapchain)(Handle);
static S26EDGlAttachParam p_s26edAttachParam;
static S26EDGlAttachRenderbuffer p_s26edAttachRb;
static S26EDGlAttachTexture p_s26edAttachTex;
static S26EDGlU32 p_s26edDrawBuffer;
static S26EDGlBindRenderbuffer p_s26edBindRb;
static S26EDGlRenderbufferParam p_s26edRbParam;
static S26EDGlTextureLevelParam p_s26edTexLevelParam;
static S26EDGlGetError p_s26edGetError;
static S26EDGlGetBooleanv p_s26edGetBooleanv;
static S26EDGlDepthMask p_s26edDepthMask;
static u8 g_s26edDepthGlTried,g_s26edDepthGlReady;
static PFN_H5754H_XrEnumerateSwapchainFormats p_s26edXrFormats;
static PFN_H5754H_XrCreateSwapchain p_s26edXrCreate;
static S26EDXrDestroySwapchain p_s26edXrDestroy;
static PFN_H5754H_XrEnumerateSwapchainImages p_s26edXrImages;
static PFN_H5754H_XrAcquireSwapchainImage p_s26edXrAcquire;
static PFN_H5754H_XrWaitSwapchainImage p_s26edXrWait;
static PFN_H5754H_XrReleaseSwapchainImage p_s26edXrRelease;
static Handle g_s26edDepthXrInstance,g_s26edDepthSession,g_s26edDepthSwap[2];
static H5754HSwapchainImageGL g_s26edDepthImages[2][S26ED_DEPTH_MAX_IMAGES];
static u32 g_s26edDepthImageCount[2],g_s26edDepthSwapFormat,g_s26edDepthFbo[2];
static i32 g_s26edDepthSwapW,g_s26edDepthSwapH;
static u8 g_s26edDepthSessionFailed;
/* Per-eye observation of the engine attachment taken during this eye's render. */
static u8 g_s26edDepthSeen[2];
static u32 g_s26edDepthObjType[2],g_s26edDepthObjName[2],g_s26edDepthObjFormat[2];
static i32 g_s26edDepthRenderW[2],g_s26edDepthRenderH[2];
static float g_s26edDepthNear[2],g_s26edDepthFar[2],g_s26edDepthLiveNear[2],g_s26edDepthLiveFar[2];
static volatile u32 g_s26edDepthReady;
static u32 g_s26edDepthCopies,g_s26edDepthFrames,g_s26edDepthRejects,g_s26edDepthLogs;

static void s26ed_depth_log_reject(const char* why,i32 a,i32 b){
    ++g_s26edDepthRejects;
    if(g_s26edDepthLogs<12u){++g_s26edDepthLogs;ext_Log(">>> S26ED DEPTH LAYER skipped: %s (%d/%d); frames stay color-only",why,a,b);}
}
static i32 s26ed_depth_wanted(void){
    return g_s26edDepthExtension&&s26ec_option(S26EC_SET_DEPTH);
}
/* A new OpenXR session gets a fresh attempt; its child swapchains replace the
   ones that ended with the previous session. */
static i32 s26ed_depth_active(void){
    if(!s26ed_depth_wanted())return 0;
    u8* xr=(u8*)p2_xr_obj();Handle session=xr?*(Handle*)(xr+0x20):0;
    if(session!=g_s26edDepthSession){
        g_s26edDepthSession=session;g_s26edDepthSwap[0]=g_s26edDepthSwap[1]=0;g_s26edDepthSwapFormat=0;g_s26edDepthSessionFailed=0;
    }
    return session&&!g_s26edDepthSessionFailed;
}
static i32 s26ed_depth_gl_ready(void){
    if(g_s26edDepthGlReady)return 1;if(g_s26edDepthGlTried)return 0;g_s26edDepthGlTried=1;
    h5750a_resolve_swap_interval();h5750v_resolve_read_buffer();
    void* ogl=ext_GetModuleHandleA("opengl32.dll");if(!ogl)ogl=ext_GetModuleHandleA("OPENGL32.dll");
    if(!ogl||!p_h5750aWglGetProcAddress||!p_h5750vReadBuffer||!s26_resolve_validation_ready()||!h5750y_gen_fbo()||!h5750y_fbo_tex2d()||!h5750v_bind_fbo()||!h5750v_blit()){
        ext_Log(">>> S26ED DEPTH LAYER unavailable: OpenGL framebuffer entry points missing");return 0;}
    p_s26edAttachParam=(S26EDGlAttachParam)p_h5750aWglGetProcAddress("glGetFramebufferAttachmentParameteriv");
    p_s26edAttachRb=(S26EDGlAttachRenderbuffer)p_h5750aWglGetProcAddress("glFramebufferRenderbuffer");
    p_s26edAttachTex=(S26EDGlAttachTexture)p_h5750aWglGetProcAddress("glFramebufferTexture");
    p_s26edBindRb=(S26EDGlBindRenderbuffer)p_h5750aWglGetProcAddress("glBindRenderbuffer");
    p_s26edRbParam=(S26EDGlRenderbufferParam)p_h5750aWglGetProcAddress("glGetRenderbufferParameteriv");
    p_s26edTexLevelParam=(S26EDGlTextureLevelParam)p_h5750aWglGetProcAddress("glGetTextureLevelParameteriv");
    p_s26edDrawBuffer=(S26EDGlU32)ext_GetProcAddress(ogl,"glDrawBuffer");
    p_s26edGetError=(S26EDGlGetError)ext_GetProcAddress(ogl,"glGetError");
    p_s26edGetBooleanv=(S26EDGlGetBooleanv)ext_GetProcAddress(ogl,"glGetBooleanv");
    p_s26edDepthMask=(S26EDGlDepthMask)ext_GetProcAddress(ogl,"glDepthMask");
    if(!h20_mem_executable((void*)p_s26edAttachParam)||!h20_mem_executable((void*)p_s26edAttachRb)||!h20_mem_executable((void*)p_s26edBindRb)||
       !h20_mem_executable((void*)p_s26edRbParam)||!p_s26edDrawBuffer||!p_s26edGetError||!p_s26edGetBooleanv||!p_s26edDepthMask){
        ext_Log(">>> S26ED DEPTH LAYER unavailable: required OpenGL 3.x framebuffer queries missing");return 0;}
    if(!h20_mem_executable((void*)p_s26edAttachTex))p_s26edAttachTex=0;
    if(!h20_mem_executable((void*)p_s26edTexLevelParam))p_s26edTexLevelParam=0;
    g_s26edDepthGlReady=1;return 1;
}
/* Called from the light-setup hook while this eye's deferred lights are being
   prepared: the bound draw framebuffer carries the scene depth at that point.
   Read-only GL queries; the renderbuffer binding is restored. */
static void s26ed_depth_observe(const u8* r,i32 eye){
    if(eye<0||eye>1||!s26ed_depth_active()||!s26ed_depth_gl_ready())return;
    g_s26edDepthSeen[eye]=0;
    i32 rw=*(const i32*)(r+0x40u),rh=*(const i32*)(r+0x44u);
    float n=0.0f,f=0.0f;
    if(!s26ed_depth_planes((const float*)(r+0xaa4u),h5755ea_world_units_per_meter(),&n,&f)){s26ed_depth_log_reject("projection is not a finite standard perspective",rw,rh);return;}
    if(rw<16||rh<16||rw>16384||rh>16384){s26ed_depth_log_reject("renderer size",rw,rh);return;}
    i32 drawFbo=0;ext_glGetIntegerv(0x8CA6u,&drawFbo);if(drawFbo<=0){s26ed_depth_log_reject("scene renders to the default framebuffer",drawFbo,0);return;}
    i32 type=0,name=0,dBits=0,sBits=0,comp=0,level=-1,layered=0,stencilType=0,stencilName=0;
    p_s26edAttachParam(0x8CA9u,0x8D00u,0x8CD0u,&type);
    if(type!=0x8D41&&type!=0x1702){s26ed_depth_log_reject("no depth attachment on the scene framebuffer",drawFbo,type);return;}
    p_s26edAttachParam(0x8CA9u,0x8D00u,0x8CD1u,&name);
    p_s26edAttachParam(0x8CA9u,0x8D00u,0x8216u,&dBits);
    p_s26edAttachParam(0x8CA9u,0x8D00u,0x8217u,&sBits);
    p_s26edAttachParam(0x8CA9u,0x8D00u,0x8211u,&comp);
    p_s26edAttachParam(0x8CA9u,0x8D20u,0x8CD0u,&stencilType);
    if(stencilType)p_s26edAttachParam(0x8CA9u,0x8D20u,0x8CD1u,&stencilName);
    u32 fmt=s26ed_depth_format(dBits,sBits,(u32)comp);
    if(name<=0||!fmt){s26ed_depth_log_reject("unsupported depth format bits",dBits,sBits);return;}
    if(sBits&&(stencilType!=type||stencilName!=name)){s26ed_depth_log_reject("stencil is not packed with depth",stencilType,stencilName);return;}
    i32 ow=0,oh=0;
    if(type==0x8D41){
        i32 prev=0;ext_glGetIntegerv(0x8CA7u,&prev);
        p_s26edBindRb(0x8D41u,(u32)name);p_s26edRbParam(0x8D41u,0x8D42u,&ow);p_s26edRbParam(0x8D41u,0x8D43u,&oh);
        p_s26edBindRb(0x8D41u,(u32)prev);
    }else{
        if(!p_s26edAttachTex||!p_s26edTexLevelParam){s26ed_depth_log_reject("texture depth needs OpenGL 4.5 size queries",type,0);return;}
        p_s26edAttachParam(0x8CA9u,0x8D00u,0x8CD2u,&level);p_s26edAttachParam(0x8CA9u,0x8D00u,0x8DA7u,&layered);
        if(level!=0||layered){s26ed_depth_log_reject("depth texture level/layer",level,layered);return;}
        p_s26edTexLevelParam((u32)name,0,0x1000u,&ow);p_s26edTexLevelParam((u32)name,0,0x1001u,&oh);
    }
    /* A shadow map or other offscreen target never matches the eye render size. */
    if(ow!=rw||oh!=rh){s26ed_depth_log_reject("depth attachment size differs from the eye render",ow,oh);return;}
    g_s26edDepthObjType[eye]=(u32)type;g_s26edDepthObjName[eye]=(u32)name;g_s26edDepthObjFormat[eye]=fmt;
    g_s26edDepthRenderW[eye]=rw;g_s26edDepthRenderH[eye]=rh;g_s26edDepthNear[eye]=n;g_s26edDepthFar[eye]=f;
    g_s26edDepthSeen[eye]=1;
}
static i32 s26ed_depth_xr_procs(u8* xr){
    Handle inst=*(Handle*)(xr+0x10);if(!inst)return 0;
    if(inst==g_s26edDepthXrInstance&&p_s26edXrRelease)return 1;
    PFN_GIPA get=*(PFN_GIPA*)(xr+0x1C8);if(!get)return 0;
    p_s26edXrFormats=0;p_s26edXrCreate=0;p_s26edXrDestroy=0;p_s26edXrImages=0;p_s26edXrAcquire=0;p_s26edXrWait=0;p_s26edXrRelease=0;
    if(get(inst,"xrEnumerateSwapchainFormats",(void**)&p_s26edXrFormats)<0||get(inst,"xrCreateSwapchain",(void**)&p_s26edXrCreate)<0||
       get(inst,"xrDestroySwapchain",(void**)&p_s26edXrDestroy)<0||get(inst,"xrEnumerateSwapchainImages",(void**)&p_s26edXrImages)<0||
       get(inst,"xrAcquireSwapchainImage",(void**)&p_s26edXrAcquire)<0||get(inst,"xrWaitSwapchainImage",(void**)&p_s26edXrWait)<0||
       get(inst,"xrReleaseSwapchainImage",(void**)&p_s26edXrRelease)<0||!p_s26edXrFormats||!p_s26edXrCreate||!p_s26edXrDestroy||
       !p_s26edXrImages||!p_s26edXrAcquire||!p_s26edXrWait||!p_s26edXrRelease){p_s26edXrRelease=0;return 0;}
    g_s26edDepthXrInstance=inst;return 1;
}
static void s26ed_depth_disable_session(const char* why,i32 code,i32 detail){
    g_s26edDepthSessionFailed=1;
    ext_Log(">>> S26ED DEPTH LAYER off for this session: %s (%d/%d); color submission unchanged",why,code,detail);
}
/* One depth swapchain per eye, same size as the color eye and the engine's
   exact depth format. Recreated if the session, size or format changes. */
static i32 s26ed_depth_swapchains(u8* xr,u32 fmt){
    Handle session=*(Handle*)(xr+0x20);i32 w=*(volatile i32*)(xr+0x40),h=*(volatile i32*)(xr+0x44);
    if(!session||session!=g_s26edDepthSession||w<=0||h<=0)return 0;
    if(w!=*(volatile i32*)(xr+0x60)||h!=*(volatile i32*)(xr+0x64)){s26ed_depth_disable_session("eye swapchain sizes differ",w,*(volatile i32*)(xr+0x60));return 0;}
    if(g_s26edDepthSwap[0]&&g_s26edDepthSwap[1]&&g_s26edDepthSwapFormat==fmt&&g_s26edDepthSwapW==w&&g_s26edDepthSwapH==h)return 1;
    if(!s26ed_depth_xr_procs(xr))return 0;
    for(i32 e=0;e<2;++e)if(g_s26edDepthSwap[e]){p_s26edXrDestroy(g_s26edDepthSwap[e]);g_s26edDepthSwap[e]=0;}
    u32 count=0;i64 fmts[64];
    if(p_s26edXrFormats(session,0,&count,0)<0||count==0||count>64u||p_s26edXrFormats(session,count,&count,fmts)<0){s26ed_depth_disable_session("swapchain formats unavailable",(i32)count,0);return 0;}
    i32 offered=0;for(u32 i=0;i<count;++i)if(fmts[i]==(i64)fmt)offered=1;
    if(!offered){s26ed_depth_disable_session("runtime does not offer the engine depth format",(i32)fmt,0);return 0;}
    for(i32 e=0;e<2;++e){
        H5754HSwapchainCreateInfo ci;zero_bytes(&ci,sizeof(ci));ci.type=H5754H_XR_TYPE_SWAPCHAIN_CREATE_INFO;
        ci.usageFlags=0x02u;ci.format=(i64)fmt;ci.sampleCount=1;ci.width=(u32)w;ci.height=(u32)h;ci.faceCount=1;ci.arraySize=1;ci.mipCount=1;
        i32 cr=p_s26edXrCreate(session,&ci,&g_s26edDepthSwap[e]);
        if(cr<0||!g_s26edDepthSwap[e]){g_s26edDepthSwap[e]=0;s26ed_depth_disable_session("depth swapchain creation failed",cr,0);return 0;}
        u32 n=0;if(p_s26edXrImages(g_s26edDepthSwap[e],0,&n,0)<0||n==0||n>S26ED_DEPTH_MAX_IMAGES){s26ed_depth_disable_session("depth swapchain image count",(i32)n,0);return 0;}
        for(u32 i=0;i<n;++i){zero_bytes(&g_s26edDepthImages[e][i],sizeof(g_s26edDepthImages[e][i]));g_s26edDepthImages[e][i].type=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_KHR;}
        u32 got=n;if(p_s26edXrImages(g_s26edDepthSwap[e],n,&got,g_s26edDepthImages[e])<0||got==0||got>n){s26ed_depth_disable_session("depth swapchain images",(i32)got,0);return 0;}
        g_s26edDepthImageCount[e]=got;
    }
    g_s26edDepthSwapFormat=fmt;g_s26edDepthSwapW=w;g_s26edDepthSwapH=h;
    ext_Log(">>> S26ED DEPTH LAYER swapchains ready: 2 x %dx%d format 0x%x (%u/%u images)",w,h,fmt,g_s26edDepthImageCount[0],g_s26edDepthImageCount[1]);
    return 1;
}
/* Copy this eye's scene depth (same crop as the color resolve) into the
   acquired depth image. Every GL binding/state touched is restored. */
static i32 s26ed_depth_blit(i32 eye,u32 image,const i32 crop[4]){
    PFN_H5750V_BindFramebuffer bind=h5750v_bind_fbo();PFN_H5750V_BlitFramebuffer blit=h5750v_blit();
    if(!g_s26edDepthFbo[0]||!g_s26edDepthFbo[1]){h5750y_gen_fbo()(2,g_s26edDepthFbo);if(!g_s26edDepthFbo[0]||!g_s26edDepthFbo[1])return 0;}
    u32 point=(g_s26edDepthObjFormat[eye]==S26ED_GL_DEPTH24_STENCIL8||g_s26edDepthObjFormat[eye]==S26ED_GL_DEPTH32F_STENCIL8)?0x821Au:0x8D00u;
    i32 prevRead=0,prevDraw=0;u8 mask=1;ext_glGetIntegerv(0x8CAAu,&prevRead);ext_glGetIntegerv(0x8CA6u,&prevDraw);
    u8 scissor=ext_glIsEnabled(0x0C11u);p_s26edGetBooleanv(0x0B72u,&mask);
    while(p_s26edGetError()!=0){}
    bind(0x8CA8u,g_s26edDepthFbo[0]);
    if(g_s26edDepthObjType[eye]==0x8D41u)p_s26edAttachRb(0x8CA8u,point,0x8D41u,g_s26edDepthObjName[eye]);
    else p_s26edAttachTex(0x8CA8u,point,g_s26edDepthObjName[eye],0);
    p_h5750vReadBuffer(0);
    bind(0x8CA9u,g_s26edDepthFbo[1]);h5750y_fbo_tex2d()(0x8CA9u,point,0x0DE1u,image,0);p_s26edDrawBuffer(0);
    i32 ok=p_s26CheckResolveFbo(0x8CA8u)==0x8CD5u&&p_s26CheckResolveFbo(0x8CA9u)==0x8CD5u;
    if(ok){
        if(scissor)ext_glDisable(0x0C11u);if(!mask)p_s26edDepthMask(1);
        blit(crop[0],crop[1],crop[2],crop[3],0,0,g_s26edDepthSwapW,g_s26edDepthSwapH,0x0100u,0x2600u);
        if(!mask)p_s26edDepthMask(0);if(scissor)ext_glEnable(0x0C11u);
    }
    /* Detach so the private FBOs never keep engine or runtime images alive. */
    if(g_s26edDepthObjType[eye]==0x8D41u)p_s26edAttachRb(0x8CA8u,point,0x8D41u,0);else p_s26edAttachTex(0x8CA8u,point,0,0);
    h5750y_fbo_tex2d()(0x8CA9u,point,0x0DE1u,0,0);
    bind(0x8CA8u,(u32)prevRead);bind(0x8CA9u,(u32)prevDraw);
    u32 err=p_s26edGetError();while(p_s26edGetError()!=0){}
    if(!ok){s26ed_depth_log_reject("depth framebuffer incomplete",eye,0);return 0;}
    if(err){s26ed_depth_log_reject("OpenGL error during depth copy",eye,(i32)err);return 0;}
    return 1;
}
/* After the main eye's scene render, still inside that eye's GL scope. */
static void s26ed_depth_capture(i32 eye){
    if(eye<0||eye>1)return;
    i32 seen=g_s26edDepthSeen[eye];g_s26edDepthSeen[eye]=0;
    __atomic_and_fetch(&g_s26edDepthReady,~(1u<<eye),__ATOMIC_ACQ_REL);
    if(!seen||!s26ed_depth_active())return;
    u8* xr=(u8*)p2_xr_obj();if(!xr||!s26ed_depth_swapchains(xr,g_s26edDepthObjFormat[eye]))return;
    i32 crop[4];if(!h5750x_eye_geometry(eye,g_s26edDepthRenderW[eye],g_s26edDepthRenderH[eye],crop,0,0)){s26ed_depth_log_reject("eye crop",eye,0);return;}
    Handle swap=g_s26edDepthSwap[eye];u32 index=0;
    H5754HAcquireInfo ai;zero_bytes(&ai,sizeof(ai));ai.type=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_ACQUIRE_INFO;
    i32 xr0=p_s26edXrAcquire(swap,&ai,&index);
    if(xr0<0){s26ed_depth_disable_session("depth image acquire failed",xr0,0);return;}
    H5754HReleaseInfo ri;zero_bytes(&ri,sizeof(ri));ri.type=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO;
    if(index>=g_s26edDepthImageCount[eye]){p_s26edXrRelease(swap,&ri);s26ed_depth_disable_session("depth image index",(i32)index,0);return;}
    H5754HWaitInfo wi;zero_bytes(&wi,sizeof(wi));wi.type=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_WAIT_INFO;wi.timeout=0x7fffffffffffffffLL;
    i32 wr=p_s26edXrWait(swap,&wi);
    i32 copied=wr==0&&s26ed_depth_blit(eye,g_s26edDepthImages[eye][index].image,crop);
    i32 rr=p_s26edXrRelease(swap,&ri);
    if(wr!=0||rr<0){s26ed_depth_disable_session("depth image wait/release failed",wr!=0?wr:rr,0);return;}
    if(!copied)return;
    g_s26edDepthLiveNear[eye]=g_s26edDepthNear[eye];g_s26edDepthLiveFar[eye]=g_s26edDepthFar[eye];
    __atomic_or_fetch(&g_s26edDepthReady,1u<<eye,__ATOMIC_ACQ_REL);
    if(++g_s26edDepthCopies<=2u)ext_Log(">>> S26ED DEPTH LAYER eye %d copied: crop %d,%d-%d,%d of %dx%d -> %dx%d | near %.3f m far %.1f m",eye,crop[0],crop[1],crop[2],crop[3],g_s26edDepthRenderW[eye],g_s26edDepthRenderH[eye],g_s26edDepthSwapW,g_s26edDepthSwapH,(double)g_s26edDepthNear[eye],(double)g_s26edDepthFar[eye]);
}
/* xrEndFrame: consume this frame's depth readiness; returns the frame to submit. */
static S26EDDepthFrame g_s26edDepthFrame;
static XrFrameEndInfo g_s26edDepthEnd;
static const XrFrameEndInfo* s26ed_depth_end_frame(const XrFrameEndInfo* in,i32 gameplay){
    u32 ready=__atomic_exchange_n(&g_s26edDepthReady,0u,__ATOMIC_ACQ_REL);
    if(!gameplay||ready!=3u||!s26ed_depth_wanted()||g_s26edDepthSessionFailed)return in;
    if(!s26ed_depth_chain(in,&g_s26edDepthEnd,&g_s26edDepthFrame,g_s26edDepthSwap,g_s26edDepthSwapW,g_s26edDepthSwapH,g_s26edDepthLiveNear,g_s26edDepthLiveFar)){
        s26ed_depth_log_reject("projection layer shape",in?(i32)in->layerCount:-1,0);return in;}
    if(++g_s26edDepthFrames==1u)ext_Log(">>> S26ED DEPTH LAYER submitting: both eyes carry XrCompositionLayerDepthInfoKHR");
    return &g_s26edDepthEnd;
}
static void s26ed_depth_end_result(const XrFrameEndInfo* submitted,i32 r){
    if(submitted==&g_s26edDepthEnd&&r<0)s26ed_depth_disable_session("runtime rejected the frame with depth",r,0);
}
