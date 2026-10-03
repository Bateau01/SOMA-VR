/* S26ED: CLIMB LADDERS WITH HANDS. While SOMA's ladder state is active
   (PlayerHandsHandler publishes VRLADDER 1/0), a hand that holds grip and
   pulls down climbs up; pushing up climbs down. Hand speed maps onto the
   native Move analog the ladder state already reads from the stick, so the
   authored climb speed, mount and dismount rules stay SOMA's. The stick keeps
   priority whenever it is pushed. A light pulse marks every ~30 cm climbed. */
#define S26ED_LADDER_FULL_SPEED 0.90f /* m/s of hand pull for full climb input */
#define S26ED_LADDER_DEADZONE   0.05f /* m/s */
#define S26ED_LADDER_SMOOTH     0.08f /* s */
#define S26ED_LADDER_RUNG       0.30f /* m between rung pulses */
#define S26ED_LADDER_GRIP_ON    0.55f
#define S26ED_LADDER_GRIP_OFF   0.35f
typedef struct { u8 holding[2]; float lastY[2]; i64 lastT; float climb,travel; } S26EDLadder;
static void s26ed_ladder_reset(S26EDLadder* L){
    L->holding[0]=L->holding[1]=0;L->lastY[0]=L->lastY[1]=0.0f;L->lastT=0;L->climb=0.0f;L->travel=0.0f;
}
/* grip: 1 while that hand holds grip on a tracked controller; y: raw tracked
   height in metres. Returns the climb input (-1..1, positive = up) and sets
   *rungHand to the hand that just completed a rung, else -1. */
static float s26ed_ladder_step(S26EDLadder* L,const i32 grip[2],const float y[2],i64 now,i32* rungHand){
    if(rungHand)*rungHand=-1;
    float dt=(L->lastT&&now>L->lastT)?(float)(now-L->lastT)*1.0e-9f:0.0f;
    i32 valid=dt>0.0005f&&dt<0.10f;
    float best=0.0f;i32 bestHand=-1;
    for(i32 h=0;h<2;++h){
        if(!grip[h]||!(y[h]>-10.0f&&y[h]<10.0f)){L->holding[h]=0;continue;}
        if(L->holding[h]&&valid){
            float pull=L->lastY[h]-y[h];
            if((pull<0.0f?-pull:pull)>(best<0.0f?-best:best)){best=pull;bestHand=h;}
        }
        L->holding[h]=1;L->lastY[h]=y[h];
    }
    if(now>0)L->lastT=now;
    if(!valid){L->climb=0.0f;return 0.0f;}
    float target=0.0f;
    if(bestHand>=0){
        float v=best/dt;
        if(v>S26ED_LADDER_DEADZONE||v<-S26ED_LADDER_DEADZONE){target=v/S26ED_LADDER_FULL_SPEED;if(target>1.0f)target=1.0f;if(target<-1.0f)target=-1.0f;}
        L->travel+=best<0.0f?-best:best;
        if(L->travel>=S26ED_LADDER_RUNG){L->travel=0.0f;if(rungHand)*rungHand=bestHand;}
    }
    float k=dt/S26ED_LADDER_SMOOTH;if(k>1.0f)k=1.0f;
    L->climb+=(target-L->climb)*k;
    if(L->climb>-0.02f&&L->climb<0.02f&&target==0.0f)L->climb=0.0f;
    return L->climb;
}
