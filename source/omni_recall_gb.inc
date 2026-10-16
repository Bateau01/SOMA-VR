/* S26GB: recall only an already-owned, loose Catherine. No creation, pickup,
   detach, use or ownership callback. Commands execute once at the normal gameplay
   pre-physics boundary. Pause can queue; map teardown invalidates its epoch. */
static u32 g_s26gbRecallEpoch=1,g_s26gbRecallPending,g_s26gbRecallResult;
static i32 g_s26gbRecallCommitting;
static i32 s26gb_recall_allowed(void){
    return g_h576mScriptRuntimePublished==1 && p2_xr_on() && p2_xr_running() &&
        g_h5753cAuthorityEnabled && !g_h576bfMapTransitionActive &&
        g_h5755bhPresentationState==H5755BH_GAMEPLAY_VR && !g_h5755asUiIslandActive &&
        !g_h5755asResumeClassifyActive && !g_h5755azExitPending && !g_h5755bbTitlePresentationLatch &&
        !g_s26CutsceneHandsHidden && !g_s26ManualHeal &&
        h5720_streq(g_h5729LastModuleName,"player/PlayerState_Normal.hps") &&
        h5720_streq(g_h5729LastClassName,"cScrPlayerState_Normal") &&
        g_h576anOmniStorageMode==H576AN_OMNI_STORAGE_RIGHT_SHOULDER &&
        g_h576bOmniState==H576B_OMNI_LOOSE && g_h576bOmniBody && g_h576bOmniWrapper &&
        g_h576bOmniOwner && g_h576cCanonicalEntityName[0] &&
        !g_h14GripBody[0] && !g_h14GripBody[1] && !g_h30NativeMouseDown &&
        !g_h576dDockReleasePending && !g_h576dDockReleaseActive &&
        !g_h576eBindPending && !g_h576bCaptureNextInteract && !g_h576aoOmniHidePending;
}
static u32 s26gb_recall_request(i32 menu){
    u32 epoch=__atomic_load_n(&g_s26gbRecallEpoch,__ATOMIC_ACQUIRE);
    u32 state=__atomic_load_n(&g_h5755bhPresentationState,__ATOMIC_ACQUIRE);
    if(g_h576mScriptRuntimePublished!=1 || !p2_xr_on() || !p2_xr_running() ||
       g_h576bfMapTransitionActive || g_s26CutsceneHandsHidden || g_s26ManualHeal || (state!=H5755BH_GAMEPLAY_VR && !(menu && state==H5755BH_PAUSE_QUAD))){__atomic_store_n(&g_s26gbRecallResult,3u,__ATOMIC_RELEASE);return 0;}
    __atomic_store_n(&g_s26gbRecallResult,1u,__ATOMIC_RELEASE);
    // Binding only queues an edge. Script/ownership checks run on the engine thread.
    __atomic_store_n(&g_s26gbRecallPending,epoch,__ATOMIC_RELEASE);
    return 1;
}
static void s26gb_recall_button_sample(i32 down,i32 active){
    static i32 armed;
    if(!active || !p2_xr_running() || g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR){armed=0;return;}
    if(!down){armed=1;return;}
    if(armed){armed=0;(void)s26gb_recall_request(0);}
}
static void s26gb_recall_reset(void){
    __atomic_add_fetch(&g_s26gbRecallEpoch,1u,__ATOMIC_ACQ_REL);
    __atomic_store_n(&g_s26gbRecallPending,0u,__ATOMIC_RELEASE);
    __atomic_store_n(&g_s26gbRecallResult,0u,__ATOMIC_RELEASE);
}
static void s26gb_recall_cancel_unavailable(void){
    if(!__atomic_load_n(&g_s26gbRecallPending,__ATOMIC_ACQUIRE))return;
    u32 state=__atomic_load_n(&g_h5755bhPresentationState,__ATOMIC_ACQUIRE);
    if(g_h576bfMapTransitionActive || g_s26CutsceneHandsHidden || g_s26ManualHeal ||
       g_h5755azExitPending || g_h5755bbTitlePresentationLatch ||
       (state!=H5755BH_GAMEPLAY_VR && state!=H5755BH_PAUSE_QUAD)){
        s26gb_recall_reset();
        __atomic_store_n(&g_s26gbRecallResult,3u,__ATOMIC_RELEASE);
    }
}
static void s26gb_recall_step(void){
    u32 epoch=__atomic_exchange_n(&g_s26gbRecallPending,0u,__ATOMIC_ACQ_REL);
    if(!epoch)return;
    if(epoch!=__atomic_load_n(&g_s26gbRecallEpoch,__ATOMIC_ACQUIRE) || !s26gb_recall_allowed()){
        __atomic_store_n(&g_s26gbRecallResult,3u,__ATOMIC_RELEASE);
        ext_Log(">>> S26GB OMNI RECALL: unavailable; tool/state unchanged");return;
    }
    u32 ack=g_h576aoOmniShoulderStoreAcks;
    g_s26gbRecallCommitting=1;
    i32 invoked=h576aa_run_global("PlayerToolHandler","","_Global_VRRecallOwnedOmni");
    g_s26gbRecallCommitting=0;
    if(!invoked || ack==g_h576aoOmniShoulderStoreAcks){
        __atomic_store_n(&g_s26gbRecallResult,3u,__ATOMIC_RELEASE);
        ext_Log(">>> S26GB OMNI RECALL: script ownership/attachment guard rejected; tool unchanged");return;
    }
    __atomic_store_n(&g_s26gbRecallResult,2u,__ATOMIC_RELEASE);
    h576b_forget_body("S26GB recalled owned loose Omni-Tool to shoulder");
    for(i32 h=0;h<2;h++){
        g_h576aoOmniStowArmedBody[h]=0;g_h576aoOmniStowLastInsideStep[h]=0;
        g_h576anOmniShoulderRetrieveArmed[h]=0;g_h576anOmniShoulderInside[h]=0;
    }
    h576ac_queue_haptic(1,H576AC_HAPTIC_CONFIRM);
    ext_Log(">>> S26GB OMNI RECALL: stored existing owned carrier; no socket/use/pickup callback");
}
