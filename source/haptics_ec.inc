/* S26EC: CREATURE HAPTICS. DistortionEffectsHandler publishes its monster
   proximity "static" amount (the value that drives the screen distortion)
   through VRHAPT; this channel turns it into a rough low-frequency buzz in
   both controllers, throbbing while the creature is being looked at.
   - Semantic one-shot pulses always win: a hand that just received one is
     left alone for 40 ms (OpenXR replaces a running vibration on apply).
   - Short pulses only, rate-limited; the effect lapses on its own when the
     script stops publishing (stale), outside VR gameplay, while paused, or
     with the option off. */
#define S26EC_STATIC_STALE_FRAMES 45u
#define S26EC_STATIC_HOLDOFF_NS 40000000LL
#define S26EC_STATIC_PULSE_NS 14000000LL
static volatile u32 g_s26ecStaticMilli,g_s26ecStaticLooked,g_s26ecStaticFrame;
static i64 g_s26ecStaticNext,g_s26ecStaticHoldUntil[2];
static u32 g_s26ecStaticRng=0x9e3779b9u,g_s26ecStaticPulses;
static float s26ec_static_rand(void){
    g_s26ecStaticRng=g_s26ecStaticRng*1664525u+1013904223u;return (float)(g_s26ecStaticRng>>8)/16777216.0f;
}
static u64 s26ec_static_token(const H5730TString* cls,const H5730TString* fn){
    i32 looked=h5748t_sso_eq(cls,"L",1u);
    if(!looked&&!h5748t_sso_eq(cls,"S",1u))return 0u;
    char text[8];float value=0.0f;
    if(!h5748n_copy_tstring((void*)fn,text,sizeof(text))||!h11_parse_float(text,&value)||!(value>=0.0f&&value<=1000.0f))return 0u;
    __atomic_store_n(&g_s26ecStaticMilli,(u32)value,__ATOMIC_RELEASE);
    __atomic_store_n(&g_s26ecStaticLooked,looked?1u:0u,__ATOMIC_RELEASE);
    __atomic_store_n(&g_s26ecStaticFrame,g_frameCounter,__ATOMIC_RELEASE);
    return 1u;
}
/* Amplitude for one pulse: amount 0..1 (script distortion), looked flag and
   time in seconds. Separated for tests. */
static float s26ec_static_amplitude(float amount,i32 looked,float seconds,float noise){
    if(!(amount>0.0f))return 0.0f;if(amount>1.0f)amount=1.0f;
    float a=(0.08f+0.42f*amount)*(0.6f+0.4f*noise);
    if(looked){float beat=0.5f+0.5f*ext_Sinf(seconds*13.823f);a*=0.55f+0.75f*beat;}
    return a>0.75f?0.75f:a;
}
static void s26ec_static_tick(Handle sess,i64 now){
    for(i32 h=0;h<2;++h)if(__atomic_exchange_n(&g_s26ecSemanticFired[h],0u,__ATOMIC_ACQ_REL))g_s26ecStaticHoldUntil[h]=now+S26EC_STATIC_HOLDOFF_NS;
    u32 milli=__atomic_load_n(&g_s26ecStaticMilli,__ATOMIC_ACQUIRE);
    u32 stamp=__atomic_load_n(&g_s26ecStaticFrame,__ATOMIC_ACQUIRE);
    if(!sess||now<=0||!milli||(u32)(g_frameCounter-stamp)>S26EC_STATIC_STALE_FRAMES||!s26ec_option(S26EC_SET_CREATURE)||
       !g_h576acHapticReady||!pApplyHaptic||!h5755dg_gameplay_vr()||h5754h_pause_active()){g_s26ecStaticNext=0;return;}
    if(g_s26ecStaticNext&&now<g_s26ecStaticNext&&g_s26ecStaticNext-now<200000000LL)return;
    /* Script value is 0.1 + 0.9 * proximity once a creature is in range. */
    float amount=((float)milli/1000.0f-0.1f)/0.9f;if(amount<0.0f)amount=0.0f;
    i32 looked=(i32)__atomic_load_n(&g_s26ecStaticLooked,__ATOMIC_ACQUIRE);
    float noise=s26ec_static_rand();
    float amp=s26ec_static_amplitude(amount,looked,(float)(now%1000000000000LL)/1.0e9f,noise);
    g_s26ecStaticNext=now+16000000LL+(i64)(s26ec_static_rand()*14000000.0f);
    if(amp<=0.0f)return;
    for(i32 h=0;h<2;++h){
        if(!g_h576acHapticAction[h]||now<g_s26ecStaticHoldUntil[h])continue;
        if(__atomic_load_n(&g_h576acHapticPending[h],__ATOMIC_ACQUIRE))continue;
        XrHapticActionInfo hi;zero_bytes(&hi,sizeof(hi));hi.type=XR_TYPE_HAPTIC_ACTION_INFO;hi.action=g_h576acHapticAction[h];
        XrHapticVibration vib;zero_bytes(&vib,sizeof(vib));vib.type=XR_TYPE_HAPTIC_VIBRATION;
        vib.duration=S26EC_STATIC_PULSE_NS;vib.frequency=60.0f+40.0f*s26ec_static_rand();vib.amplitude=amp;
        (void)pApplyHaptic(sess,&hi,(const void*)&vib);
    }
    if(g_s26ecStaticPulses++==0u)ext_Log(">>> S26EC CREATURE HAPTICS ACTIVE: static %.2f looked %d -> amplitude %.2f",amount,looked,amp);
}
