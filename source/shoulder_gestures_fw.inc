/* FW: bounded gesture tolerance, no deferred world-body ownership or callbacks.
   All times are the runtime's predicted-display timestamps, in nanoseconds. */
typedef struct {i64 start;u32 step,epoch,grabs;u8 active;} S26FWEntry;
typedef struct {const void* body;i64 readyAt;u32 step,epoch; i32 slot;} S26FWStow;
static S26FWEntry g_s26fwEntry[2];
static S26FWStow g_s26fwStow[2];
static i64 g_s26fwNow;
static u32 g_s26fwSeenCancelGeneration;
typedef struct {u32 step,epoch;u8 sampled,valid;float wrist[3],matrix[16],anchor[2][3],yaw,metric;} S26FWFrame;
static S26FWFrame g_s26fwFrame[2];

static i32 s26fw_entry_update(S26FWEntry* e,i64 now,u32 step,u32 epoch,
                             i32 valid,i32 held,i32 edge,i32 busy,u32 grabs){
    if(!valid||!held||busy||now<=0){e->active=0;return 0;}
    if(edge){e->start=now;e->step=step;e->epoch=epoch;e->grabs=grabs;e->active=1;}
    if(!e->active)return 0;
    if(e->epoch!=epoch||e->grabs!=grabs||(u32)(step-e->step)>1u||now<e->start||now-e->start>250000000LL){e->active=0;return 0;}
    e->step=step;return 1;
}
static i32 s26fw_stow_update(S26FWStow* s,const void* body,i32 slot,
                            i64 now,u32 step,u32 epoch,i32 valid,
                            i32 inside,i32 exitMargin,i32 graceMargin){
    if(!valid||!body||now<=0){if(s->slot==slot)s->body=0;return 0;}
    if(s->body&&(s->body!=body||s->epoch!=epoch||(u32)(step-s->step)>1u||now<s->readyAt))s->body=0;
    if(s->body&&s->slot!=slot)return 0; // a gesture cannot switch shoulders
    i32 same=s->body==body;
    i32 ready=inside||(same&&exitMargin)||(same&&graceMargin&&now-s->readyAt<=120000000LL);
    if(!ready){if(s->slot==slot)s->body=0;return 0;}
    s->body=body;s->slot=slot;s->epoch=epoch;s->step=step;
    if(inside||exitMargin)s->readyAt=now; // never extend the outer grace by hovering
    return 1;
}
static void s26fw_cancel_retrieve(i32 hand){if(hand>=0&&hand<2)g_s26fwEntry[hand].active=0;}
static void s26fw_clear_hand(i32 hand){
    s26fw_cancel_retrieve(hand);g_s26fwStow[hand].body=0;g_s26fwFrame[hand].sampled=0;
}
static void s26fw_reset(void){s26fw_clear_hand(0);s26fw_clear_hand(1);g_s26fwNow=0;}
static i32 s26fw_live(i32 hand){
    return hand>=0&&hand<2&&g_lastActive[hand]&&(g_lastFlags[hand]&3u)==3u&&g_lastLocateResult[hand]>=0&&
        g_lastSqueezeActive[hand]&&g_h5753cAuthorityEnabled&&
        !g_s26ManualHeal&&!g_s26CutsceneHandsHidden&&
        !g_h576bfMapTransitionActive&&!g_h5755asUiIslandActive&&!g_h5755asResumeClassifyActive&&
        !g_h5755azExitPending&&!g_h5755bbTitlePresentationLatch&&
        g_h5755bhPresentationState==H5755BH_GAMEPLAY_VR&&
        g_h14VisualSeen&&(u32)(g_frameCounter-g_h14LastVisualFrame)<=4u;
}
static void s26fw_begin_step(void){
    u32 cancel=__atomic_load_n(&g_s26fwCancelGeneration,__ATOMIC_ACQUIRE);
    if(cancel!=g_s26fwSeenCancelGeneration){s26fw_reset();g_s26fwSeenCancelGeneration=cancel;}
    u8* xr=(u8*)p2_xr_obj();
    g_s26fwNow=xr&&h20_mem_readable(xr+0xE8,8)?*(i64*)(xr+0xE8):0;
    for(i32 h=0;h<2;++h){g_s26fwFrame[h].sampled=0;if(!s26fw_live(h))s26fw_clear_hand(h);}
}
static S26FWFrame* s26fw_frame(i32 hand){
    if(__atomic_load_n(&g_s26fwCancelGeneration,__ATOMIC_ACQUIRE)!=g_s26fwSeenCancelGeneration||!s26fw_live(hand)||g_s26fwNow<=0){if(hand>=0&&hand<2)s26fw_clear_hand(hand);return 0;}
    S26FWFrame* f=&g_s26fwFrame[hand];
    if(!f->sampled||f->step!=g_h14PhysicsSteps||f->epoch!=g_h5745YawCaptures){
        f->sampled=1;f->valid=0;f->step=g_h14PhysicsSteps;f->epoch=g_h5745YawCaptures;
        /* This is the calibrated tracked grip origin. Keep it independent of
           model skin, curled fingertips and collision-displaced render hands. */
        if(!h14_hand_pose_raw(hand,f->wrist,f->matrix)||!h576aa_shoulder_anchor(f->anchor[0])||!h576an_omni_shoulder_anchor(f->anchor[1]))return 0;
        f->yaw=s26r_shoulder_yaw();f->metric=h5755ea_world_units_per_meter();
        if(!(f->metric>=0.01f&&f->metric<=100.0f))return 0;
        f->valid=1;
    }
    return f->valid?f:0;
}
static i32 s26fz_frame_region(const S26FWFrame* f,i32 slot,float radius,i32 deposit,float* distance){
    if(!f||!f->valid||slot<0||slot>1||radius<=0.01f)return 0;
    float dx=f->wrist[0]-f->anchor[slot][0],dy=f->wrist[1]-f->anchor[slot][1],dz=f->wrist[2]-f->anchor[slot][2];
    if(distance)*distance=h10_len3(dx,dy,dz);
    float c=ext_Cosf(f->yaw),s=ext_Sinf(f->yaw);
    float x=(c*dx-s*dz)/f->metric,y=dy/f->metric,z=(s*dx+c*dz)/f->metric;
    return (deposit?s26fz_deposit_score(x,y,z,radius):s26fy_slot_score(x,y,z,radius))<=1.0f;
}
static i32 s26fw_frame_inside(const S26FWFrame* f,i32 slot,float radius,float* distance){
    return s26fz_frame_region(f,slot,radius,0,distance);
}
static i32 s26fz_frame_deposit(const S26FWFrame* f,i32 slot,float radius){
    return s26fz_frame_region(f,slot,radius,1,0);
}
static i32 s26fw_near(i32 hand,i32 slot,float* gc,float* matrix,float* distance){
    if(distance)*distance=999.0f;S26FWFrame* f=s26fw_frame(hand);if(!f)return 0;
    if(matrix)h10_copy_f(matrix,f->matrix,16);
    if(gc&&!h15_grip_center_world(hand,f->matrix,gc))h10_copy_f(gc,f->wrist,3);
    return s26fw_frame_inside(f,slot,slot?g_h576anOmniShoulderRadius:g_h576aaShoulderRadius,distance);
}
static void s26fw_update_entry(i32 hand,i32 held,i32 edge){
    i32 busy=g_h14GripBody[hand]!=0||(g_h30NativeMouseDown&&g_h30NativeUseHand==hand)||
        g_h576agPendingHand==hand||(hand==1&&g_s26xPhonePending);
    s26fw_entry_update(&g_s26fwEntry[hand],g_s26fwNow,g_h14PhysicsSteps,g_h5745YawCaptures,
        s26fw_frame(hand)!=0,held,edge,busy,g_h14GrabCount[hand]);
}
static i32 s26fw_take_entry(i32 hand,i32 inside,i32 eligible){
    if(!inside||!eligible||!g_s26fwEntry[hand].active)return 0;
    /* Consume before a script call: no repeating failed materialization/callbacks.
       Existing selected-key-item body maturation remains its own transaction. */
    g_s26fwEntry[hand].active=0;return 1;
}
