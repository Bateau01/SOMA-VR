/* Preserve motion across a contact-clear, free-hand gesture-body replacement.
   The dormant collision warm-up and preserved physical root remain unchanged.
   No raw-pose teleport, extra collision query, or held-object path is added. */
typedef struct {
    const void* body;
    const void* world;
    u32 generation,step;
    u8 valid;
    float target[16],velocity[4],omega[4];
} S26AVGestureMotion;
static S26AVGestureMotion g_s26avGestureMotion[2];

static void s26av_capture_gesture_motion(i32 hand){
    if(hand<0||hand>1)return;
    S26AVGestureMotion* s=&g_s26avGestureMotion[hand];s->valid=0;s->body=0;
    if(!g_h34HandNewton[hand]||g_h14GripBody[hand]||!g_h528PrevTargetValid[hand]||
       !p_h14GetVelocity||!p_h14GetOmega||g_h545ContactThisStep[hand])return;
    for(i32 i=0;i<16;++i)if(!h9_good(g_h528PrevTarget[hand][i],1000000.0f))return;
    p_h14GetVelocity(g_h34HandNewton[hand],s->velocity);
    p_h14GetOmega(g_h34HandNewton[hand],s->omega);
    for(i32 i=0;i<3;++i)if(!h9_good(s->velocity[i],5.0f)||!h9_good(s->omega[i],12.0f))return;
    h29_clamp3(s->velocity,5.0f);h29_clamp3(s->omega,12.0f);
    h10_copy_f(s->target,g_h528PrevTarget[hand],16);
    s->world=g_h14NewtonWorld;s->step=g_h14PhysicsSteps;s->valid=1;
}

static void s26av_bind_gesture_motion(i32 hand){
    if(hand<0||hand>1)return;
    S26AVGestureMotion* s=&g_s26avGestureMotion[hand];
    if(s->valid){s->body=g_h34HandNewton[hand];s->generation=g_h526BodyCreates[hand];}
}

static void s26av_resume_gesture_motion(i32 hand,const float* rawHandM){
    if(hand<0||hand>1)return;
    S26AVGestureMotion* s=&g_s26avGestureMotion[hand];u8 valid=s->valid;s->valid=0;
    u32 age=g_h14PhysicsSteps-s->step;
    if(!valid||!rawHandM||!s->body||s->body!=g_h34HandNewton[hand]||
       s->world!=g_h14NewtonWorld||s->generation!=g_h526BodyCreates[hand]||
       age<1u||age>2u||g_h14GripBody[hand]||g_h510PoseInvalidFrames[hand]||
       g_h545ContactThisStep[hand]||!p_h14SetVelocity||!p_h14SetOmega)return;
    float target[16];h34_make_body_target(hand,rawHandM,target);
    for(i32 i=0;i<16;++i)if(!h9_good(target[i],1000000.0f))return;
    float delta[3]={target[12]-s->target[12],target[13]-s->target[13],target[14]-s->target[14]};
    if(h10_len3(delta[0],delta[1],delta[2])>=0.25f)return; // same discontinuity limit as H528
    /* Prime a one-step history from the measured interval. The normal target
       publisher computes/clamps feed-forward exactly once later this step.
       At age two, only translation is extrapolated; avoid scaling rotations. */
    h10_copy_f(g_h528PrevTarget[hand],age==1u?s->target:target,16);
    for(i32 i=0;i<3;++i)g_h528PrevTarget[hand][12+i]=target[12+i]-delta[i]/(float)age;
    g_h528PrevTargetValid[hand]=1;
    float dt=g_h14LastPhysicsDt;if(!h9_good(dt,0.1f)||dt<0.001f)dt=1.0f/60.0f;
    float targetV[3]={delta[0]/((float)age*dt),delta[1]/((float)age*dt),delta[2]/((float)age*dt)};
    /* Do not replay old momentum when the controller stopped or reversed.
       World contacts remain authoritative once the ordinary solver resumes. */
    float speed=h10_len3(targetV[0],targetV[1],targetV[2]);
    if(speed>0.02f&&h10_dot(targetV,s->velocity)>0.0f)
        p_h14SetVelocity(s->body,s->velocity);
    float turn[3];h26_rotation_delta(s->target,target,turn);
    if(h10_len3(turn[0],turn[1],turn[2])>0.001f&&h10_dot(turn,s->omega)>0.0f)
        p_h14SetOmega(s->body,s->omega);
}
