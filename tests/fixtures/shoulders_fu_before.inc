/* S26R: independent shoulder heading, in raw application tracking space.
   No camera, character, physics, recenter, or inventory writes. */
typedef struct {
    float yaw;
    i64 time;
    u32 epoch;
    u8 valid, following, reach, trackerSeen;
} S26RShoulders;
static S26RShoulders g_s26rShoulders;
static u32 g_s26rShoulderLogs;

static float s26r_angle(float x) {
    return h5755eb_wrap_pi(x);
}
/* Pure state update. Nanosecond XR time, never render/physics frame counts. */
static void s26r_shoulder_step(S26RShoulders* st,i64 now,u32 epoch,i32 valid,
                               float headYaw,i32 reach,float handYaw,i32 hands) {
    if(!valid||now<=0){st->valid=0;st->reach=0;st->following=0;return;}
    if(!st->valid||st->epoch!=epoch||now<st->time||now-st->time>250000000LL){
        st->yaw=headYaw;st->valid=1;st->epoch=epoch;st->time=now;
        st->following=0;st->reach=0;return;
    }
    if(now==st->time)return;
    float dt=(float)(now-st->time)*0.000000001f;st->time=now;
    st->reach=reach?1:0;
    if(reach){st->following=0;return;}
    /* Controller evidence only corroborates head direction, at most 9 degrees.
       The caller excludes raised, crossed, missing and behind-head hands. */
    float target=headYaw;
    float hd=s26r_angle(handYaw-headYaw);
    if(hands&&h9_abs(hd)<0.785398164f)target=s26r_angle(target+0.20f*hd);
    float delta=s26r_angle(target-st->yaw),a=h9_abs(delta);
    if(a>0.349065850f)st->following=1; /* 20-degree turn threshold */
    if(a<=0.087266463f)st->following=0; /* settle within 5 degrees */
    if(st->following){
        float step=2.094395102f*dt; /* 120 degrees/second at every refresh rate */
        float remaining=a-0.087266463f;if(step>remaining)step=remaining;
        st->yaw=s26r_angle(st->yaw+(delta<0?-step:step));
    }
}

/* S26FG: tracker heading is a torso reference, independent of locomotion mode.
   Preserve the existing reach latch; movement in Waist mode stays tracker-directed.
   Rate limiting bridges tracker acquisition/loss without snapping slot targets. */
static void s26fg_shoulder_step(S26RShoulders* st,i64 now,u32 epoch,i32 valid,
                                float head,i32 reach,float hand,i32 hands,
                                i32 tracked,float waist) {
    if(!tracked){
        if(st->trackerSeen&&st->valid&&st->epoch==epoch&&now-st->time>250000000LL)
            st->time=now-50000000LL;
        s26r_shoulder_step(st,now,epoch,valid,head,reach,hand,hands);return;
    }
    st->trackerSeen=1;
    if(!valid||now<=0){s26r_shoulder_step(st,now,epoch,0,0,0,0,0);return;}
    if(!st->valid||st->epoch!=epoch||now<st->time){
        st->yaw=waist;st->valid=1;st->epoch=epoch;st->time=now;
        st->following=0;st->reach=reach?1:0;return;
    }
    if(now==st->time)return;
    float dt=(float)(now-st->time)*0.000000001f;st->time=now;
    if(dt>0.05f)dt=0.05f;
    st->reach=reach?1:0;st->following=0;
    if(reach)return;
    float delta=s26r_angle(waist-st->yaw),limit=2.094395102f*dt;
    if(delta>limit)delta=limit;if(delta<-limit)delta=-limit;
    st->yaw=s26r_angle(st->yaw+delta);
}

