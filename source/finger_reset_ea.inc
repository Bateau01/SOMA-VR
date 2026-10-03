/* Explicit, delayed controller rest capture. All ten fingers commit together.
   A failed/aborted capture leaves existing references untouched. */
static volatile u32 g_s26eaResetRequest,g_s26eaResetState,g_s26eaResetCountdown;
static i64 g_s26eaResetStart,g_s26eaStableStart,g_s26eaResetLast;
static float g_s26eaRestMin[2][5],g_s26eaRestMax[2][5],g_s26eaRestSum[2][5];
static u32 g_s26eaRestCount;
static void s26ea_finger_reset_tick(i64 time,i32 focused,const float raw[2][5],const u8 valid[2]){
    u32 request=__atomic_exchange_n(&g_s26eaResetRequest,0u,__ATOMIC_ACQ_REL);
    if(request==2u){g_s26eaResetState=0;return;}
    if(request==1u){g_s26eaResetStart=time;g_s26eaStableStart=0;g_s26eaRestCount=0;g_s26eaResetLast=0;g_s26eaResetState=1;}
    u32 state=g_s26eaResetState;if(state!=1&&state!=2)return;
    if(time<=0||time<g_s26eaResetStart||!focused){g_s26eaResetState=4;return;}
    i64 elapsed=time-g_s26eaResetStart;
    if(elapsed<5000000000LL){g_s26eaResetCountdown=(u32)((5000000000LL-elapsed+999999999LL)/1000000000LL);return;}
    g_s26eaResetState=2;
    if(elapsed>15000000000LL){g_s26eaResetState=4;ext_Log(">>> S26EA FINGER RESET FAILED: no valid stable released pose; previous reference retained");return;}
    i32 ok=valid[0]&&valid[1];
    for(i32 h=0;h<2;++h){
        /* Some controllers expose joints without per-finger touch actions.
           Known contact rejects capture; unknown touch is not fake release.
           Explicit countdown + stable skeletal pose is the reference. */
        if(g_s26dlTouchKnown[h]&g_s26dlTouched[h])ok=0;
        if(!(g_lastSqueeze[h]>=0&&g_lastSqueeze[h]<=0.05f&&g_lastTrigger[h]>=0&&g_lastTrigger[h]<=0.05f))ok=0;
        for(i32 f=0;f<5;++f)if(!(raw[h][f]>=0&&raw[h][f]<0.92f))ok=0;
    }
    if(!ok){g_s26eaStableStart=0;g_s26eaRestCount=0;return;}
    i32 restart=!g_s26eaStableStart||time<=g_s26eaResetLast||time-g_s26eaResetLast>100000000LL;
    for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f)
        if(raw[h][f]<g_s26eaRestMin[h][f]-0.02f||raw[h][f]>g_s26eaRestMax[h][f]+0.02f||
           g_s26eaRestMax[h][f]-g_s26eaRestMin[h][f]>0.04f)restart=1;
    if(restart){
        g_s26eaStableStart=time;g_s26eaRestCount=0;
        for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f){g_s26eaRestMin[h][f]=g_s26eaRestMax[h][f]=raw[h][f];g_s26eaRestSum[h][f]=0;}
    }
    ++g_s26eaRestCount;g_s26eaResetLast=time;
    for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f){
        float v=raw[h][f];if(v<g_s26eaRestMin[h][f])g_s26eaRestMin[h][f]=v;if(v>g_s26eaRestMax[h][f])g_s26eaRestMax[h][f]=v;g_s26eaRestSum[h][f]+=v;
    }
    if(time-g_s26eaStableStart<750000000LL||g_s26eaRestCount<8)return;
    for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f){
        S26DZRest* r=&g_s26dzRest[h][f];r->reference=g_s26eaRestSum[h][f]/(float)g_s26eaRestCount;r->learned=1;r->manual=1;
        ext_Log(">>> S26EA FINGER RESET h%d f%d reference %.4f; explicit stable release, session-only",h,f,r->reference);
    }
    __atomic_store_n(&g_s26eaResetState,3u,__ATOMIC_RELEASE);
}
