/* Bounded observation. Rows contain copies only; no retained engine pointers.
   First Begin caller owns the stream; other-thread samples are counted/dropped.
   No per-frame IO. QPC and GPU timestamp domains are explicitly distinct. */
typedef struct {u32 type,frame,step,detail,state,thread;u64 begin,end,predicted;float model[16],view[16];} S26IHRow;
#define S26IH_CAP 32768u
static S26IHRow g_s26ihRows[S26IH_CAP];
static u32 g_s26ihInit,g_s26ihEnabled,g_s26ihSaved,g_s26ihCount,g_s26ihOwner,g_s26ihOtherThread;
static u64 g_s26ihFrequency,g_s26ihStart;
typedef i32 (__attribute__((ms_abi))*S26IHCounter)(i64*);
typedef u32 (__attribute__((ms_abi))*S26IHThread)(void);
static S26IHCounter p_s26ihCounter;
static S26IHThread p_s26ihThread;
static u64 s26ih_now(void){i64 t=0;if(g_s26ihEnabled&&p_s26ihCounter)p_s26ihCounter(&t);return (u64)t;}
static void s26ih_begin_capture(void){
    if(g_s26ihInit)return;g_s26ihInit=1;
    char path[520];void*f=make_sibling_path(path,sizeof(path),"hpl3vr_frame_timing.flag")?ext_fopen(path,"rb"):0;
    if(!f)return;ext_fclose(f);void*k=ext_GetModuleHandleA("kernel32.dll");if(!k)return;
    p_s26ihCounter=(S26IHCounter)ext_GetProcAddress(k,"QueryPerformanceCounter");
    p_s26ihThread=(S26IHThread)ext_GetProcAddress(k,"GetCurrentThreadId");
    S26IHCounter freq=(S26IHCounter)ext_GetProcAddress(k,"QueryPerformanceFrequency");
    if(!p_s26ihCounter||!p_s26ihThread||!freq||!freq((i64*)&g_s26ihFrequency)||!g_s26ihFrequency)return;
    g_s26ihOwner=p_s26ihThread();g_s26ihEnabled=1;ext_Log("S26IH frame recorder armed: 30 seconds, CPU/GPU domains separate, observation only");
}
static void s26ih_event(u32 type,u32 detail,u64 begin,u64 end,const float* model,const float* view){
    if(!g_s26ihEnabled||g_s26ihSaved||g_s26ihCount>=S26IH_CAP||!begin||end<begin)return;
    if(p_s26ihThread()!=g_s26ihOwner){__atomic_fetch_add(&g_s26ihOtherThread,1u,__ATOMIC_RELAXED);return;}
    if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||g_h576bfMapTransitionActive||g_h5755asUiIslandActive||g_h5755asResumeClassifyActive||g_h5755azExitPending)return;
    if(!g_s26ihStart)g_s26ihStart=s26ih_now();
    S26IHRow*r=&g_s26ihRows[g_s26ihCount++];zero_bytes(r,sizeof(*r));
    r->type=type;r->frame=g_frameCounter;r->step=g_h14PhysicsSteps;r->detail=detail;r->state=g_h5755bhPresentationState;r->thread=g_s26ihOwner;r->begin=begin;r->end=end;
    void*xr=p2_xr_obj();r->predicted=xr?*(u64*)((u8*)xr+0xe8):0;
    for(i32 i=0;i<16;++i){if(model)r->model[i]=model[i];if(view)r->view[i]=view[i];}
}
static void s26ih_hand(u32 hand,const float* model){
    if(!g_s26ihEnabled)return;
    if(p_s26ihThread()!=g_s26ihOwner){__atomic_fetch_add(&g_s26ihOtherThread,1u,__ATOMIC_RELAXED);return;}
    if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||g_h576bfMapTransitionActive||g_h5755asUiIslandActive||g_h5755asResumeClassifyActive||g_h5755azExitPending)return;
    void*camera=p2_camera_obj();u64 t=s26ih_now();
    s26ih_event(6u,hand,t,t,model,camera?(float*)((u8*)camera+0x74):0);
}
static void s26ih_flush(void){
    if(!g_s26ihEnabled||g_s26ihSaved||p_s26ihThread()!=g_s26ihOwner||!g_s26ihCount)return;
    if(g_s26ihCount<S26IH_CAP&&s26ih_now()-g_s26ihStart<30u*g_s26ihFrequency)return;
    g_s26ihSaved=1;g_s26ihEnabled=0;char path[520];if(!make_sibling_path(path,sizeof(path),"hpl3vr_frame_timing_IH.bin"))return;
    void*f=ext_fopen(path,"wb");if(!f){ext_Log("S26IH frame save failed");return;}
    u32 h[4]={0x48494653u,1u,(u32)sizeof(S26IHRow),g_s26ihCount};
    u64 a=ext_fwrite(h,16,1,f),b=ext_fwrite(&g_s26ihFrequency,8,1,f),c=ext_fwrite(g_s26ihRows,sizeof(S26IHRow),g_s26ihCount,f);ext_fclose(f);
    ext_Log("S26IH frame saved=%u rows=%u rowBytes=%u otherThreadDropped=%u",(u32)(a==1&&b==1&&c==g_s26ihCount),g_s26ihCount,(u32)sizeof(S26IHRow),g_s26ihOtherThread);
}
