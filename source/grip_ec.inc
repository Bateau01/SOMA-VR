/* S26EC: SMART GRIP for capacitive skeletal controllers. Runs on the XR input
   thread after the grip/trigger remap and rewrites only that frame's grab
   analog (g_lastSqueeze), so every grab start/keep/release site downstream
   applies the same rules without per-site changes:
   - Pinch: thumb and index closed with middle/ring/little open counts as a
     full grab (small items are then seated between the fingertips).
   - Closure only: middle/ring/little closed while thumb and index are open
     and off their controls cannot START a grab (capped below 0.55); an
     existing hold is kept (cap stays above the 0.28 release threshold).
   - Opening release: a fast opening of the gripping fingers releases at
     once, through the normal "squeeze released" path with its throw velocity.
     The grab analog then stays below the press threshold until the hand is
     really open or deliberately closes again, so it cannot instantly regrab.
   Unavailable/invalid fingers, an analog swap to the trigger, or the setting
   off leave the controller value untouched. */
#define S26EC_PINCH_ENTER_THUMB 0.55f
#define S26EC_PINCH_ENTER_INDEX 0.50f
#define S26EC_PINCH_ENTER_LOWER_MAX 0.35f
#define S26EC_PINCH_EXIT_THUMB 0.40f
#define S26EC_PINCH_EXIT_INDEX 0.35f
#define S26EC_PINCH_GRIP 0.80f
#define S26EC_OPEN_FINGER_MAX 0.30f
#define S26EC_CLOSURE_LOWER_MIN 0.50f
#define S26EC_CLOSURE_CAP 0.50f
#define S26EC_OPEN_WINDOW_NS 90000000LL
#define S26EC_OPEN_DROP 0.22f
#define S26EC_OPEN_MAX_AFTER 0.60f
#define S26EC_OPEN_RECLOSE 0.15f
#define S26EC_OPEN_TIMEOUT_NS 1500000000LL
#define S26EC_OPEN_HOLD_CAP 0.0f
#define S26EC_REGRAB_CAP 0.27f
static u32 g_s26ecPinchGrabs[2],g_s26ecClosureCaps[2],g_s26ecOpenReleases[2];
static i64 g_s26ecOpenStart[2];
static u8 g_s26ecOpenReleased[2];
static void s26ec_grip_reset(i32 h){
    if(h<0||h>1)return;zero_bytes(&g_s26ecGrip[h],sizeof(g_s26ecGrip[h]));g_s26ecOpenReleased[h]=0;g_s26ecOpenStart[h]=0;
    __atomic_store_n(&g_s26ecPinch[h],0u,__ATOMIC_RELEASE);
}
static i32 s26ec_hand_holding(i32 h){
    return g_h14GripBody[h]!=0||(g_h30NativeMouseDown&&g_h30NativeUseHand==h);
}
/* Pure decision step, separated for tests. Returns the effective grab analog. */
static float s26ec_grip_decide(S26ECGrip* G,const S26ECFingers* f,float v,i64 now,i32 held,u32 touchKnown,u32 touched,u8* released,i64* openStart){
    float lower=s26ec_lower_three(f);
    if(!G->pinch){if(f->thumb>=S26EC_PINCH_ENTER_THUMB&&f->index>=S26EC_PINCH_ENTER_INDEX&&lower<=S26EC_PINCH_ENTER_LOWER_MAX)G->pinch=1;}
    else if(f->thumb<S26EC_PINCH_EXIT_THUMB||f->index<S26EC_PINCH_EXIT_INDEX)G->pinch=0;
    /* Thumb and index count as open only when curled little AND not resting
       on a sensed control; a known contact means the finger is in use. */
    i32 thumbOpen=f->thumb<=S26EC_OPEN_FINGER_MAX&&!((touchKnown&1u)&&(touched&1u));
    i32 indexOpen=f->index<=S26EC_OPEN_FINGER_MAX&&!((touchKnown&2u)&&(touched&2u));
    float e=v;
    if(G->pinch){if(e<S26EC_PINCH_GRIP)e=S26EC_PINCH_GRIP;}
    else if(thumbOpen&&indexOpen&&lower>=S26EC_CLOSURE_LOWER_MIN&&e>S26EC_CLOSURE_CAP)e=S26EC_CLOSURE_CAP;
    /* Opening measure: the fingers that actually carry the grip. */
    float g=G->pinch?(f->thumb<f->index?f->thumb:f->index):lower;
    float peak=g;
    for(u32 k=0;k<G->count;++k){u32 at=(G->head+S26EC_GRIP_HISTORY-1u-k)%S26EC_GRIP_HISTORY;if(now-G->t[at]>S26EC_OPEN_WINDOW_NS||now<G->t[at])break;if(G->g[at]>peak)peak=G->g[at];}
    G->t[G->head]=now;G->g[G->head]=g;G->head=(G->head+1u)%S26EC_GRIP_HISTORY;if(G->count<S26EC_GRIP_HISTORY)G->count++;
    if(!G->openLatch&&held&&peak-g>=S26EC_OPEN_DROP&&g<=S26EC_OPEN_MAX_AFTER){G->openLatch=1;G->openMin=g;*openStart=now;*released=0;}
    if(G->openLatch){
        if(g<G->openMin)G->openMin=g;
        if(v<0.28f&&!G->pinch){G->openLatch=0;}
        else if(g>=G->openMin+S26EC_OPEN_RECLOSE||now-*openStart>S26EC_OPEN_TIMEOUT_NS){G->openLatch=0;}
        else {if(!held)*released=1;e=*released?S26EC_REGRAB_CAP:S26EC_OPEN_HOLD_CAP;if(G->pinch)G->pinch=0;}
    }
    return e;
}
static void s26ec_grip_tick(i32 h,i64 now){
    if(h<0||h>1)return;
    S26ECFingers f;
    if(!s26ec_option(S26EC_SET_SMART_GRIP)||g_s26qAnalogApplied[h]||!g_lastSqueezeActive[h]||g_lastSqueezeResult[h]<0||now<=0||!s26ec_fingers(h,&f)){s26ec_grip_reset(h);return;}
    S26ECGrip* G=&g_s26ecGrip[h];u8 wasPinch=G->pinch,wasLatch=G->openLatch;
    float v=clamp01(g_lastSqueeze[h]);
    float e=s26ec_grip_decide(G,&f,v,now,s26ec_hand_holding(h),g_s26dlTouchKnown[h],g_s26dlTouched[h],&g_s26ecOpenReleased[h],&g_s26ecOpenStart[h]);
    if(G->pinch&&!wasPinch&&g_s26ecPinchGrabs[h]++<16u)ext_Log(">>> S26EC PINCH %s: thumb %.2f index %.2f others %.2f -> grab analog %.2f",h?"R":"L",f.thumb,f.index,s26ec_lower_three(&f),e);
    if(G->openLatch&&!wasLatch&&g_s26ecOpenReleases[h]++<24u)ext_Log(">>> S26EC FINGER-OPEN RELEASE %s: grip fingers opened %.2f within 90 ms; release now with tracked throw velocity",h?"R":"L",G->openMin);
    if(e<v&&!G->openLatch&&g_s26ecClosureCaps[h]++<8u)ext_Log(">>> S26EC CLOSURE-ONLY GRIP %s: middle/ring/little closed with thumb and index open; grab start suppressed",h?"R":"L");
    __atomic_store_n(&g_s26ecPinch[h],(u32)G->pinch,__ATOMIC_RELEASE);
    g_lastSqueeze[h]=e;
}

/* Called from h14_latch for a loose body: a pinched light item is moved so
   its contact point sits between the thumb and index fingertips. */
#define S26EC_PINCH_MAX_MASS 1.0f
#define S26EC_PINCH_MAX_SHIFT_M 0.06f
static void s26ec_pinch_seat(i32 hand,const float* handM,const float* gripHand,const float* bm,const float* contact,float mass){
    if(hand<0||hand>1||!__atomic_load_n(&g_s26ecPinch[hand],__ATOMIC_ACQUIRE)||!(mass>0.0f&&mass<=S26EC_PINCH_MAX_MASS))return;
    float t0[3],t1[3];
    if(!h14_finger_tip_world(hand,0,h10_raw_finger_input(hand,0),gripHand,t0)||!h14_finger_tip_world(hand,1,h10_raw_finger_input(hand,1),gripHand,t1))return;
    float p[3]={(t0[0]+t1[0])*0.5f,(t0[1]+t1[1])*0.5f,(t0[2]+t1[2])*0.5f},d[3]={p[0]-contact[0],p[1]-contact[1],p[2]-contact[2]};
    float shift=h10_len3(d[0],d[1],d[2]);
    if(!(shift<=S26EC_PINCH_MAX_SHIFT_M*h5755ea_world_units_per_meter()))return;
    float seated[16],invGrip[16],invH[16];h10_copy_f(seated,bm,16);seated[12]+=d[0];seated[13]+=d[1];seated[14]+=d[2];
    h14_rigid_inverse(gripHand,invGrip);h10_matmul(invGrip,seated,g_h14GripRel[hand]);
    h14_rigid_inverse(handM,invH);h14_transform_point(invH,p,g_h15GripHandAnchor[hand]);
    for(i32 k=0;k<3;++k)g_h32DriveHandAnchor[hand][k]=g_h15GripHandAnchor[hand][k];
    ext_Log(">>> S26EC PINCH SEAT %s: %.3f kg item moved %.4f m to the thumb/index tips",hand?"R":"L",mass,shift);
}

/* GRIP PRESSURE for heavy loose bodies: with grip force sensing, a heavy
   item needs a real squeeze; a weak grip lets it slip after a short warning.
   Bodies held without force data keep the existing behaviour. */
#define S26EC_HEAVY_MASS 3.0f
#define S26EC_HEAVY_GRACE_STEPS 45u
#define S26EC_HEAVY_WARN_STEPS 8u
#define S26EC_HEAVY_SLIP_STEPS 24u
static const void* g_s26ecHoldBody[2];
static u32 g_s26ecHoldStep[2],g_s26ecLowSteps[2],g_s26ecSlips[2];
static float s26ec_heavy_force_needed(float mass){
    float need=0.06f+0.02f*(mass-S26EC_HEAVY_MASS);return need<0.06f?0.06f:(need>0.35f?0.35f:need);
}
static i32 s26ec_heavy_slip_step(i32 h){
    if(h<0||h>1)return 0;
    const void* b=g_h14GripBody[h];
    if(b!=g_s26ecHoldBody[h]){g_s26ecHoldBody[h]=b;g_s26ecHoldStep[h]=g_h14PhysicsSteps;g_s26ecLowSteps[h]=0;}
    if(!b||g_h15GripJointed[h]||!s26ec_option(S26EC_SET_PRESSURE)||!(g_h14GrabMass[h]>=S26EC_HEAVY_MASS)){g_s26ecLowSteps[h]=0;return 0;}
    float best=-1.0f;
    for(i32 k=0;k<2;++k)if(g_h14GripBody[k]==b&&g_s26ecForceValid[k]&&g_s26ecForce[k]>best)best=g_s26ecForce[k];
    if(best<0.0f||g_h14PhysicsSteps-g_s26ecHoldStep[h]<S26EC_HEAVY_GRACE_STEPS||best>=s26ec_heavy_force_needed(g_h14GrabMass[h])){g_s26ecLowSteps[h]=0;return 0;}
    if(++g_s26ecLowSteps[h]==S26EC_HEAVY_WARN_STEPS)h576ac_queue_haptic(h,H576AC_HAPTIC_READY);
    if(g_s26ecLowSteps[h]<S26EC_HEAVY_SLIP_STEPS)return 0;
    g_s26ecLowSteps[h]=0;
    if(g_s26ecSlips[h]++<16u)ext_Log(">>> S26EC HEAVY SLIP %s: %.2f kg needs grip force %.2f, had %.2f",h?"R":"L",g_h14GrabMass[h],s26ec_heavy_force_needed(g_h14GrabMass[h]),best);
    return 1;
}
