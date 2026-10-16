/* S26R: independent shoulder heading, in raw application tracking space.
   No camera, character, physics, recenter, or inventory writes. */
typedef struct {
    float yaw, inputYaw, turnRate, headReference;
    i64 time;
    u32 epoch;
    u8 valid, following, reach, trackerSeen, headSeen, headVertical;
} S26RShoulders;
static S26RShoulders g_s26rShoulders;
static u32 g_s26rShoulderLogs;

static float s26r_angle(float x) {
    return h5755eb_wrap_pi(x);
}
/* FV: guard the projected heading near the vertical singularity. Pitch and
   roll never tilt shoulder volumes. This reference is local to shoulders/Body
   movement; it does not change the submitted camera pose or recenter basis. */
static float s26fv_head_reference(S26RShoulders* st,float yaw,float horizontal){
    if(!(horizontal>=0.0f&&horizontal<=1.1f))horizontal=0.0f;
    if(horizontal<0.25f)st->headVertical=1;
    else if(horizontal>0.35f)st->headVertical=0;
    if(!st->headVertical){st->headReference=yaw;st->headSeen=1;}
    return st->headSeen?st->headReference:0.0f;
}
/* Continuous time-based heading. OpenXR poses are already predicted; only
   follow gain uses measured turn speed, never an extrapolated future position.
   A reach marks intent but cannot freeze heading or locomotion. */
static void s26fv_follow(S26RShoulders* st,i64 now,u32 epoch,i32 valid,
                         float target,i32 reach,i32 tracked){
    if(!valid||now<=0||!(target>=-3.142f&&target<=3.142f)){
        st->valid=0;st->reach=0;st->following=0;st->turnRate=0;
        st->headSeen=0;st->headVertical=0;st->trackerSeen=0;return;
    }
    if(!st->valid||st->epoch!=epoch||now<st->time||now-st->time>250000000LL){
        st->yaw=target;st->inputYaw=target;st->turnRate=0;st->valid=1;
        st->epoch=epoch;st->time=now;st->following=0;st->reach=reach?1:0;
        st->trackerSeen=tracked?1:0;return;
    }
    if(now==st->time)return;
    float dt=(float)(now-st->time)*0.000000001f;st->time=now;
    if(dt>0.05f)dt=0.05f;
    if(st->trackerSeen!=(tracked?1:0)){st->inputYaw=target;st->turnRate=0;}
    st->trackerSeen=tracked?1:0;st->reach=reach?1:0;
    float speed=h9_abs(s26r_angle(target-st->inputYaw))/dt;st->inputYaw=target;
    if(speed>6.283185307f)speed=6.283185307f;
    float rateAlpha=(12.0f*dt)/(1.0f+6.0f*dt);
    st->turnRate+=(speed-st->turnRate)*rateAlpha;
    float gain=tracked?14.0f:6.0f+st->turnRate*2.0f;
    if(gain>14.0f)gain=14.0f;
    float alpha=(gain*dt)/(1.0f+0.5f*gain*dt);
    float delta=s26r_angle(target-st->yaw),step=delta*alpha;
    float limit=6.283185307f*dt; /* bounded 360 degrees/sec, never a hard snap */
    if(step>limit)step=limit;if(step<-limit)step=-limit;
    st->yaw=s26r_angle(st->yaw+step);
    st->following=h9_abs(delta)>0.001745329f;
}
static void s26r_shoulder_step(S26RShoulders* st,i64 now,u32 epoch,i32 valid,
                               float headYaw,i32 reach,float handYaw,i32 hands){
    float target=headYaw;
    /* Hands corroborate, never override, heading. Raised/crossed/behind-head
       hands are excluded by the caller, so a reach cannot steer the shoulders. */
    float hd=s26r_angle(handYaw-headYaw);
    if(hands&&h9_abs(hd)<0.785398164f)target=s26r_angle(target+0.20f*hd);
    s26fv_follow(st,now,epoch,valid,target,reach,0);
}
static void s26fg_shoulder_step(S26RShoulders* st,i64 now,u32 epoch,i32 valid,
                                float head,i32 reach,float hand,i32 hands,
                                i32 tracked,float waist){
    if(tracked)s26fv_follow(st,now,epoch,valid,waist,reach,1);
    else s26r_shoulder_step(st,now,epoch,valid,head,reach,hand,hands);
}

static void s26r_update_shoulders(void) {
    u8* xr=(u8*)p2_xr_obj();
    i64 now=xr&&h20_mem_readable(xr+0xE8,8)?*(i64*)(xr+0xE8):0;
    i32 valid=p2_xr_origin_set()&&g_s26nHeadHeightFresh&&
        (u32)(g_frameCounter-g_s26nHeadValidFrame)<=2u&&
        !__atomic_load_n(&g_h576bfMapTransitionActive,__ATOMIC_ACQUIRE)&&
        h5755bl_resolve_atan2f();
    float hc=g_s26HeadMoveC,hs=g_s26HeadMoveS;
    if(!(hc>=-1.01f&&hc<=1.01f&&hs>=-1.01f&&hs<=1.01f))valid=0;
    if(!valid){s26r_shoulder_step(&g_s26rShoulders,now,g_h5745YawCaptures,0,0,0,0,0);return;}
    if(g_s26rShoulders.valid&&g_s26rShoulders.time==now&&g_s26rShoulders.epoch==g_h5745YawCaptures)return;
    if(!g_s26rShoulders.valid||g_s26rShoulders.epoch!=g_h5745YawCaptures){
        g_s26rShoulders.headSeen=0;g_s26rShoulders.headVertical=0;
    }
    float head=s26fv_head_reference(&g_s26rShoulders,p_h5755blAtan2f(hs,hc),g_s26fvHeadHorizontal);
    float yaw=g_s26rShoulders.valid?g_s26rShoulders.yaw:head;
    float c=ext_Cosf(yaw),s=ext_Sinf(yaw);
    volatile float* hp=p2_eye_mid();
    float local[2][3];i32 good[2]={0,0},reach=0;
    for(i32 h=0;h<2;++h){
        if(!g_lastActive[h]||(g_lastFlags[h]&3u)!=3u||g_lastLocateResult[h]<0)continue;
        float dx=g_lastPose[h].position.x-hp[0],dy=g_lastPose[h].position.y-hp[1],dz=g_lastPose[h].position.z-hp[2];
        if(!(dx>-3&&dx<3&&dy>-3&&dy<3&&dz>-3&&dz<3))continue;
        local[h][0]=c*dx-s*dz;local[h][1]=dy;local[h][2]=s*dx+c*dz;good[h]=1;
        /* Approach classification only; NEVER freezes heading and NEVER grants inventory admission. Both
           hands can approach either configured shoulder. Exit hysteresis keeps
           controller corroboration disabled throughout an active reach. */
        float pad=g_s26rShoulders.reach?0.18f:0.12f;
        for(i32 slot=0;slot<2;++slot){
            float x=slot?g_h576anOmniShoulderX:g_h576aaShoulderX;
            float y=slot?g_h576anOmniShoulderY:g_h576aaShoulderY;
            float z=slot?g_h576anOmniShoulderZ:g_h576aaShoulderZ;
            float r=(slot?g_h576anOmniShoulderRadius:g_h576aaShoulderRadius)+pad;
            float ex=(local[h][0]-x)/1.5f,ey=dy-y,ez=local[h][2]-z; // FN: approach guard covers wider lateral slot
            if(ex*ex+ey*ey+ez*ez<r*r)reach=1;
        }
    }
    i32 hands=good[0]&&good[1]&&!reach;float handYaw=head;
    if(hands){
        /* Both wrists forward/below head, sufficiently separated, uncrossed. */
        for(i32 h=0;h<2;++h)if(local[h][2]>-0.10f||local[h][1]>-0.15f)hands=0;
        float dx=g_lastPose[1].position.x-g_lastPose[0].position.x;
        float dz=g_lastPose[1].position.z-g_lastPose[0].position.z;
        if(local[1][0]-local[0][0]<0.15f||dx*dx+dz*dz>1.44f)hands=0;
        if(hands)handYaw=p_h5755blAtan2f(-dz,dx);
    }
    u8 previous=g_s26rShoulders.reach;
    i32 tracked=g_s26qWaistValid;
    float waist=tracked?p_h5755blAtan2f(g_s26qWaistS,g_s26qWaistC):head;
    s26fg_shoulder_step(&g_s26rShoulders,now,g_h5745YawCaptures,1,head,reach,handYaw,hands,tracked,waist);
    if((g_s26rShoulderLogs==0||previous!=g_s26rShoulders.reach)&&g_s26rShoulderLogs<24u){
        ++g_s26rShoulderLogs;
        ext_Log(">>> S26FV SHOULDER FRAME #%u: raw head %.1f torso %.1f reach %u hands %d epoch %u | continuous heading; shared Body movement/slots; no camera writes",g_s26rShoulderLogs,head*57.2957795f,g_s26rShoulders.yaw*57.2957795f,(u32)g_s26rShoulders.reach,hands,g_h5745YawCaptures);
    }
}
static float s26r_shoulder_yaw(void) {
    s26r_update_shoulders();
    if(!g_s26rShoulders.valid)return p2_player_yaw();
    float x,y,z;
    tracking_vector_to_game_unscaled(ext_Sinf(g_s26rShoulders.yaw),0,ext_Cosf(g_s26rShoulders.yaw),&x,&y,&z);
    return p_h5755blAtan2f(x,z);
}
static i32 h576an_body_slot_base(float out[3]) {
    /* The legacy cached late-view fallback already includes HMD translation;
       do not mix it with the gameplay-camera tracking-delta construction. */
    void* camera=p2_camera_obj();
    if(!camera||!h20_mem_readable((u8*)camera+0x10,12))return 0;
    if(!h576an_legacy_slot_base(out))return 0;
    s26r_update_shoulders();
    if(!g_s26rShoulders.valid)return 0;
    /* Hand targets use gameplay-camera + (tracking-position - XR origin).
       Use that identical translation for shoulders, including physical crouch.
       Retain the user's local shoulder calibration offsets without rescaling. */
    volatile float* hp=p2_eye_mid();volatile float* origin=p2_xr_origin();
    float dx=hp[0]-origin[0],dy=hp[1]-origin[1],dz=hp[2]-origin[2],x,y,z;
    if(!(dx>-100&&dx<100&&dy>-100&&dy<100&&dz>-100&&dz<100))return 0;
    tracking_delta_to_game(dx,dy,dz,&x,&y,&z);
    out[0]+=x;out[1]+=y;out[2]+=z;return 1;
}
