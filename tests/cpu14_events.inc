/* Private CPU14 attribution. CPU QPC and GPU nanoseconds are separate domains. */
typedef struct {u32 kind,frame,step,phase,state,detail;u64 begin,end,identity;} CPU14Event;
static CPU14Event cpu14Events[200000];static u32 cpu14Count,cpu14Dropped,cpu14Saved,cpu14GpuSkipped,cpu14ShortFiltered;
static void cpu14_event(u32 kind,u32 detail,u64 a,u64 b,u64 identity){
 if(cpu14Saved||cpu13Phase>10||!a||b<a||!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 if((kind==8||kind==10||kind==11||kind==12)&&b-a<cpuFreq/20000){cpu14ShortFiltered++;return;}
 if(cpu14Count>=200000){cpu14Dropped++;return;}
 CPU14Event*r=cpu14Events+cpu14Count++;r->kind=kind;r->frame=g_frameCounter;r->step=g_h14PhysicsSteps;r->phase=cpu13Phase;r->state=g_h5755bhPresentationState;r->detail=detail;r->begin=a;r->end=b;r->identity=identity;
}
typedef struct {u32 q[2],busy,frame,phase;void*ctx;} CPU14GPU;
static CPU14GPU cpu14Gpu[32];
static void cpu14_collect(void*ctx){
 i32 old=0;ext_glGetIntegerv(0x9193u,&old);if(old)p_s26eiTimerBindBuffer(0x9192u,0);
 for(u32 i=0;i<32;i++){CPU14GPU*q=cpu14Gpu+i;if(q->ctx!=ctx){q->q[0]=q->q[1]=q->busy=0;q->ctx=ctx;}if(q->busy!=1)continue;
 u32 ready=0;p_s26eiQueryAvailable(q->q[1],0x8867u,&ready);if(!ready)continue;
 u64 a=0,b=0;p_s26eiQueryResult(q->q[0],0x8866u,&a);p_s26eiQueryResult(q->q[1],0x8866u,&b);q->busy=0;
 u32 n=cpu14Count;cpu14_event(7,0,a,b,0);if(cpu14Count>n){cpu14Events[n].frame=q->frame;cpu14Events[n].phase=q->phase;}
 }if(old)p_s26eiTimerBindBuffer(0x9192u,(u32)old);
}
static i32 cpu14_gpu_begin(void){
 if(cpu14Saved||cpu13Phase>10||g_h5750vPrimeWrapperActive||!s26ei_timer_init())return -1;
 void*ctx=p_s26efContext?p_s26efContext():0;if(!ctx)return -1;cpu14_collect(ctx);
 for(u32 i=0;i<32;i++){CPU14GPU*q=cpu14Gpu+i;if(q->busy)continue;if(!q->q[0])p_s26eiGenQueries(2,q->q);if(!q->q[0]||!q->q[1])return -1;q->busy=2;q->frame=g_frameCounter;q->phase=cpu13Phase;p_s26eiQueryCounter(q->q[0],0x8e28u);return (i32)i;}cpu14GpuSkipped++;return -1;
}
static void cpu14_gpu_end(i32 i){if(i<0)return;CPU14GPU*q=cpu14Gpu+i;if(!p_s26efContext||p_s26efContext()!=q->ctx){q->busy=0;return;}p_s26eiQueryCounter(q->q[1],0x8e28u);q->busy=1;}
static void cpu14_save(void){
 if(cpu14Saved)return;cpu14Saved=1;u32 pending=0;for(u32 i=0;i<32;i++)pending+=cpu14Gpu[i].busy!=0;
 void*f=ext_fopen("cpu14_events.bin","wb");if(!f){ext_Log(">>> CPU14_SAVE_FAILED");return;}u64 header[6]={0x4350553134455654ULL,cpuFreq,cpu14Count,cpu14Dropped,cpu14GpuSkipped,cpu14ShortFiltered};u64 a=ext_fwrite(header,sizeof(header),1,f),b=ext_fwrite(cpu14Events,sizeof(CPU14Event),cpu14Count,f);ext_fclose(f);ext_Log(">>> CPU14_SAVED ok %u rows %u dropped %u gpu_skipped %u gpu_pending %u",a==1&&b==cpu14Count,cpu14Count,cpu14Dropped,cpu14GpuSkipped,pending);
}
