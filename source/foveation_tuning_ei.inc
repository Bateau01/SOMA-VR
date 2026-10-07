/* DFR tuning is published as one atomic word, never partially updated per eye. */
static u32 g_s26eiDFRConfig=25u|(45u<<8);
static float g_s26eiGazeGuard;
static i32 s26ei_dfr_config(const u8* text,u32 length){
    if(!text||length!=6)return 0;
    for(u32 i=0;i<6;++i)if(text[i]<'0'||text[i]>'9')return 0;
    u32 inner=(text[0]-'0')*10u+text[1]-'0',outer=(text[2]-'0')*10u+text[3]-'0';
    if(inner<10||inner>35||outer<25||outer>60||outer<inner+5||text[4]>'1'||text[5]>'1')return 0;
    u32 value=inner|(outer<<8)|((u32)(text[4]-'0')<<16)|((u32)(text[5]-'0')<<17);
    u32 old=__atomic_exchange_n(&g_s26eiDFRConfig,value,__ATOMIC_ACQ_REL);
    if(old!=value)__atomic_fetch_add(&g_s26eiMeasureEpoch,1u,__ATOMIC_RELAXED);return 1;
}
static float s26ei_tangent(u32 degrees){
    float a=(float)degrees*.01745329252f;return ext_Sinf(a)/ext_Cosf(a);
}
/* Use a circular cone about the gaze, rather than a circle offset on the
   projection plane. This preserves the angular radius at the edge of the view. */
static i32 s26ef_rate_mask(u8* pixels,i32 tw,i32 th,i32 w,i32 h,i32 tilew,i32 tileh,const float* p,const float* gaze){
    if(!pixels||tw<1||th<1||tw>512||th>512||w<1||h<1||tilew<1||tileh<1)return 0;
    if(!(p[0]>.01f&&p[0]<100&&p[5]>.01f&&p[5]<100&&p[8]>-2&&p[8]<2&&p[9]>-2&&p[9]<2))return 0;
    if(!(gaze[2]<-.2f&&gaze[2]>=-1.01f&&gaze[0]>=-1.01f&&gaze[0]<=1.01f&&gaze[1]>=-1.01f&&gaze[1]<=1.01f))return 0;
    u32 config=__atomic_load_n(&g_s26eiDFRConfig,__ATOMIC_ACQUIRE);
    float dx=2.0f*(float)tilew/((float)w*p[0]),dy=2.0f*(float)tileh/((float)h*p[5]);
    float tileGuard=ext_Sqrtf(dx*dx+dy*dy),guard=(config&(1u<<17))?g_s26eiGazeGuard:0;
    float radius=s26ei_tangent(config&255u)+tileGuard+guard;
    float outer=s26ei_tangent((config>>8)&255u)+tileGuard+guard;
    float norm=gaze[0]*gaze[0]+gaze[1]*gaze[1]+gaze[2]*gaze[2];
    float innerTest=norm/(1+radius*radius),outerTest=norm/(1+outer*outer);
    i32 coarse=(config&(1u<<16))!=0;
    for(i32 y=0;y<th;++y){float ry=(2.0f*((float)y+.5f)*(float)tileh/(float)h-1+p[9])/p[5];
        for(i32 x=0;x<tw;++x){float rx=(2.0f*((float)x+.5f)*(float)tilew/(float)w-1+p[8])/p[0];
            float dot=rx*gaze[0]+ry*gaze[1]-gaze[2],len=rx*rx+ry*ry+1;
            pixels[y*tw+x]=(dot>0&&dot*dot>=len*innerTest)?0u:((coarse&&!(dot>0&&dot*dot>=len*outerTest))?2u:1u);
        }}
    return 1;
}
/* Render-thread-only history. Repeated eyes at the same display time share the
   same guard. Reset after loss of tracking, pause or a time discontinuity. */
static void s26ei_gaze_guard(i64 now,i64 sampleTime,const float* gaze,i32 valid){
    static i64 previousTime;static float previous[3],motion;
    if(!valid||now<=0){previousTime=0;motion=0;g_s26eiGazeGuard=0;return;}
    i64 elapsed=now-previousTime;
    if(elapsed!=0){
        float next=0;
        if(previousTime>0&&elapsed>0&&elapsed<100000000LL){
            float x=gaze[0]-previous[0],y=gaze[1]-previous[1],z=gaze[2]-previous[2];
            /* Anticipate 25 ms of observed angular movement, capped near 10 deg. */
            next=ext_Sqrtf(x*x+y*y+z*z)*25000000.0f/(float)elapsed;
            float decay=motion*.75f;if(next<decay)next=decay;
        }
        if(next>.1763f)next=.1763f;motion=next;
        previousTime=now;for(i32 i=0;i<3;++i)previous[i]=gaze[i];
    }
    i64 age=now-sampleTime;float latency=age>20000000LL?(float)(age-20000000LL)*.0000000022f:0;
    if(latency>.1763f)latency=.1763f;
    g_s26eiGazeGuard=motion>latency?motion:latency;
}
