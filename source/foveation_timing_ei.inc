/* Optional, sparse GPU timestamps around the opaque pass. No glFinish, query
   result waits, or extra scene rendering. Other engine timer queries can nest. */
static u32 g_s26eiDFRTiming;
typedef struct {u32 query[2],pending,config,epoch; i32 mode,w,h;} S26EIGPUTicket;
typedef struct {u64 total,maximum;u32 count,config,epoch;i32 w,h;} S26EIGPUStats;
static S26EIGPUTicket g_s26eiTickets[8];
static S26EIGPUStats g_s26eiGPUStats[3];
static void* g_s26eiTimerContext;
static u32 g_s26eiTimerCalls,g_s26eiTimerReady;
static void (__attribute__((ms_abi)) *p_s26eiGenQueries)(i32,u32*);
static void (__attribute__((ms_abi)) *p_s26eiQueryCounter)(u32,u32);
static void (__attribute__((ms_abi)) *p_s26eiQueryAvailable)(u32,u32,u32*);
static void (__attribute__((ms_abi)) *p_s26eiQueryResult)(u32,u32,u64*);
static void (__attribute__((ms_abi)) *p_s26eiQueryBits)(u32,u32,i32*);
static void (__attribute__((ms_abi)) *p_s26eiTimerBindBuffer)(u32,u32);
static i32 s26ei_timer_init(void){
    void* ogl=ext_GetModuleHandleA("opengl32.dll");if(!ogl)return 0;
    if(!p_s26efContext)p_s26efContext=(void*)ext_GetProcAddress(ogl,"wglGetCurrentContext");
    void* ctx=p_s26efContext?p_s26efContext():0;if(!ctx)return 0;
    if(ctx==g_s26eiTimerContext)return (i32)g_s26eiTimerReady;
    g_s26eiTimerContext=ctx;g_s26eiTimerReady=0;
    for(i32 i=0;i<8;++i){g_s26eiTickets[i].query[0]=g_s26eiTickets[i].query[1]=0;g_s26eiTickets[i].pending=0;}
    for(i32 i=0;i<3;++i)g_s26eiGPUStats[i].count=0;
    PFN_H5750A_WglGetProcAddress wg=(void*)ext_GetProcAddress(ogl,"wglGetProcAddress");
#define S26EI_TIMER_PROC(dst,name) dst=(void*)s26_gl_proc(ogl,wg,name);if(!dst)return 0
    S26EI_TIMER_PROC(p_s26eiGenQueries,"glGenQueries");S26EI_TIMER_PROC(p_s26eiQueryCounter,"glQueryCounter");
    S26EI_TIMER_PROC(p_s26eiQueryAvailable,"glGetQueryObjectuiv");S26EI_TIMER_PROC(p_s26eiQueryResult,"glGetQueryObjectui64v");
    S26EI_TIMER_PROC(p_s26eiQueryBits,"glGetQueryiv");S26EI_TIMER_PROC(p_s26eiTimerBindBuffer,"glBindBuffer");
#undef S26EI_TIMER_PROC
    const u8* (__attribute__((ms_abi)) *getString)(u32)=(void*)ext_GetProcAddress(ogl,"glGetString");
    if(!getString||!s26ef_extension(getString(0x1f03u),"GL_ARB_query_buffer_object")||!s26ef_extension(getString(0x1f03u),"GL_ARB_timer_query"))return 0;
    i32 bits=0;p_s26eiQueryBits(0x8e28u,0x8864u,&bits);if(bits!=64)return 0;
    g_s26eiTimerReady=1;return 1;
}
static void s26ei_gpu_collect(void){
    i32 oldBuffer=0;ext_glGetIntegerv(0x9193u,&oldBuffer);
    if(oldBuffer)p_s26eiTimerBindBuffer(0x9192u,0);
    for(i32 i=0;i<8;++i){S26EIGPUTicket* t=&g_s26eiTickets[i];if(t->pending!=1u)continue;
        u32 available=0;p_s26eiQueryAvailable(t->query[1],0x8867u,&available);if(!available)continue;
        u64 a=0,b=0;p_s26eiQueryResult(t->query[0],0x8866u,&a);p_s26eiQueryResult(t->query[1],0x8866u,&b);t->pending=0;
        if(t->epoch!=__atomic_load_n(&g_s26eiMeasureEpoch,__ATOMIC_RELAXED)||b<a||b-a>1000000000ULL)continue;
        S26EIGPUStats* s=&g_s26eiGPUStats[t->mode];
        if(!s->count||s->epoch!=t->epoch||s->config!=t->config||s->w!=t->w||s->h!=t->h){s->total=s->maximum=0;s->count=0;s->config=t->config;s->epoch=t->epoch;s->w=t->w;s->h=t->h;}
        u64 elapsed=b-a;s->total+=elapsed;if(elapsed>s->maximum)s->maximum=elapsed;
        if(++s->count==16u){
            ext_Log(">>> S26EI DFR GPU: %s opaque-pass %dx%d config %u samples %u mean %.3f ms max %.3f ms; per-eye pass timing, not total frametime",t->mode==0?"OFF":(t->mode==1?"APPLIED":"FALLBACK"),s->w,s->h,s->config,s->count,(double)s->total/16000000.0,(double)s->maximum/1000000.0);
            s->count=0;
        }
    }
    if(oldBuffer)p_s26eiTimerBindBuffer(0x9192u,(u32)oldBuffer);
}
static i32 s26ei_gpu_begin(i32 mode,i32 w,i32 h){
    if(!__atomic_load_n(&g_s26eiDFRTiming,__ATOMIC_RELAXED)||++g_s26eiTimerCalls%31u)return -1;
    if(!s26ei_timer_init())return -1;
    s26ei_gpu_collect();
    for(i32 i=0;i<8;++i){S26EIGPUTicket* t=&g_s26eiTickets[i];if(t->pending)continue;
        if(!t->query[0])p_s26eiGenQueries(2,t->query);if(!t->query[0]||!t->query[1])return -1;
        t->pending=2;t->epoch=__atomic_load_n(&g_s26eiMeasureEpoch,__ATOMIC_RELAXED);t->mode=mode;t->w=w;t->h=h;t->config=mode?__atomic_load_n(&g_s26eiDFRConfig,__ATOMIC_ACQUIRE):0;
        p_s26eiQueryCounter(t->query[0],0x8e28u);return i;
    }
    return -1; /* GPU still busy: skip the sample instead of waiting. */
}
static void s26ei_gpu_end(i32 ticket){
    if(ticket<0)return;S26EIGPUTicket* t=&g_s26eiTickets[ticket];p_s26eiQueryCounter(t->query[1],0x8e28u);t->pending=1;
}
static void s26ei_opaque_draw(void* renderer,i32 mode){
    u8* r=(u8*)renderer;i32 ticket=-1;
    if(__atomic_load_n(&g_s26eiDFRTiming,__ATOMIC_RELAXED)&&r&&renderer==g_s26doLightRenderer&&g_s26doLightFrustum&&h20_mem_readable(r+0xbf4,16)&&*(void**)(r+0x20)==g_s26doLightFrustum)
        ticket=s26ei_gpu_begin(mode,*(i32*)(r+0x40),*(i32*)(r+0x44));
    o_s26efGbuffer(renderer);s26ei_gpu_end(ticket);
}
