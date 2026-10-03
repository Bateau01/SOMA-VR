/* Experimental Frame-only released-pose reference. A button's touch state is
   not an independent finger sensor: it only permits observing a stable,
   partly open pose. Never infer a rest pose from a closed finger or unknown
   touch input. Once learned, the reference may decrease but never increase.
   No temporal smoothing is applied to finger motion. */
typedef struct {float reference,candidate; i64 since,last; u32 learned,manual;} S26DZRest;
static S26DZRest g_s26dzRest[2][5];
static void s26dz_rest_reset(i32 hand){
    for(i32 f=0;f<5;++f)zero_bytes(&g_s26dzRest[hand][f],sizeof(S26DZRest));
}
static float s26dz_rest_value(S26DZRest* r,float value,float maximum,i64 time,i32 released){
    float v=value/maximum;
    if(!(v>=0.0f&&v<=1.0f)||time<=0)return value;
    if(r->manual)return maximum*clamp01((v-r->reference)/(1.0f-r->reference));
    if(!released||v>0.45f){r->since=0;}
    else {
        float delta=v-r->candidate;if(delta<0)delta=-delta;
        if(!r->since||time<=r->last||time-r->last>100000000LL||delta>0.015f){
            r->candidate=v;r->since=time;
        }else if(time-r->since>=400000000LL){
            if(!r->learned||r->candidate<r->reference){r->reference=r->candidate;r->learned=1;}
        }
    }
    r->last=time;
    return maximum*clamp01((v-r->reference)/(1.0f-r->reference));
}
static void s26dz_rest_correct(i32 hand,i32 finger,i64 time,float cv[4]){
    S26DZRest* r=&g_s26dzRest[hand][finger];u32 before=r->learned;float old=r->reference;
    i32 released=g_s26diFrameHand[hand]&&g_s26dlTouchKnown[hand]==31u&&g_s26dlTouched[hand]==0u&&g_s26dmReleasedMask[hand]==31u;
    float result=s26dz_rest_value(r,cv[0],finger==0?0.55f:1.0f,time,released);
    for(i32 d=0;d<4;++d)cv[d]=result;
    static u32 logs[2];
    if((r->learned!=before||r->reference!=old)&&logs[hand]<20u){
        ++logs[hand];ext_Log(">>> S26DZ FRAME REST h%d f%d reference %.4f raw %.4f; stable released pose, full curl preserved",hand,finger,r->reference,r->candidate);
    }
}
