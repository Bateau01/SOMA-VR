/* Timestamp pairs coexist with engine queries; never wait or change draw state. */
typedef struct {u32 q[2],pending,frame;void*context;} S26IHGPU;
static S26IHGPU g_s26ihGPU[8];static u32 g_s26ihGPUCalls;
static i32 s26ih_gpu_begin(void){
    if(!g_s26ihEnabled||g_s26ihSaved||g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||g_h5750vPrimeWrapperActive)return -1;
    if(++g_s26ihGPUCalls%8u||!s26ei_timer_init())return -1;
    void*ctx=p_s26efContext?p_s26efContext():0;if(!ctx)return -1;
    i32 old=0;ext_glGetIntegerv(0x9193u,&old);if(old)p_s26eiTimerBindBuffer(0x9192u,0);
    for(i32 i=0;i<8;++i){S26IHGPU*t=&g_s26ihGPU[i];
        if(t->context!=ctx){t->q[0]=t->q[1]=t->pending=0;t->context=ctx;}
        if(t->pending!=1)continue;u32 ready=0;p_s26eiQueryAvailable(t->q[1],0x8867u,&ready);if(!ready)continue;
        u64 a=0,b=0;p_s26eiQueryResult(t->q[0],0x8866u,&a);p_s26eiQueryResult(t->q[1],0x8866u,&b);t->pending=0;
        if(b>=a&&b-a<1000000000ULL)s26ih_event(7,t->frame,a,b,0,0);
    }
    if(old)p_s26eiTimerBindBuffer(0x9192u,(u32)old);
    for(i32 i=0;i<8;++i){S26IHGPU*t=&g_s26ihGPU[i];if(t->pending)continue;
        if(!t->q[0])p_s26eiGenQueries(2,t->q);if(!t->q[0]||!t->q[1])return -1;
        t->frame=g_frameCounter;t->pending=2;p_s26eiQueryCounter(t->q[0],0x8e28u);return i;
    }return -1;
}
static void s26ih_gpu_end(i32 i){
    if(i<0)return;S26IHGPU*t=&g_s26ihGPU[i];
    if(!p_s26efContext||p_s26efContext()!=t->context){t->pending=0;return;}
    p_s26eiQueryCounter(t->q[1],0x8e28u);t->pending=1;
}
