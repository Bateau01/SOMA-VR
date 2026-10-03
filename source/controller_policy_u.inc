/* Preference is published by the native-style VR menu and consumed at the next
   XR input update. Invalid packets then follow the existing grip/trigger path. */
static u32 g_s26djFingerTracking=1u;
static void s26dj_set_finger_tracking(u32 enabled){__atomic_store_n(&g_s26djFingerTracking,enabled?1u:0u,__ATOMIC_RELEASE);}
static u8 g_s26diFrameHand[2],g_s26ebProfileChanged[2];
static XrPath g_s26ebRestProfile[2];
/* XR_EXT_hand_tracking alone does not prove independent controller fingers.
   Quest/Touch runtimes can supply inferred controller-holding skeletons. */
static i32 s26u_controller_fingers_allowed(Handle session,i32 hand){
    if(hand>=0&&hand<2)g_s26diFrameHand[hand]=0;
    if(!__atomic_load_n(&g_s26djFingerTracking,__ATOMIC_ACQUIRE))return 0;
    if(hand<0||hand>1||!session||!pGetCurrentInteractionProfile||!g_handPath[hand])return 0;
    XrInteractionProfileState state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_INTERACTION_PROFILE_STATE;
    if(pGetCurrentInteractionProfile(session,g_handPath[hand],&state)<0)return 0;
    /* Runtime skeletal capability, not a vendor allowlist. An interaction
       profile alone never validates fingers: the caller requires active,
       finite joint chains. Users can disable runtime-estimated poses. */
    i32 allowed=state.interactionProfile!=0;
    if(allowed&&g_s26ebRestProfile[hand]!=state.interactionProfile){
        g_s26ebRestProfile[hand]=state.interactionProfile;g_s26ebProfileChanged[hand]=1;
    }
    /* S26EC: Valve Index and Steam Frame both sense each finger group and bind
       the shared contact actions, so both use the unobstructed motion range and
       contact-gated rest learning. Other profiles keep the generic path. */
    g_s26diFrameHand[hand]=(u8)(allowed && (state.interactionProfile==g_s26nProfiles[5]||state.interactionProfile==g_s26nProfiles[1]));
    static XrPath previous[2];static Handle previousSession;static u32 logs;
    if(previousSession!=session){previousSession=session;previous[0]=previous[1]=0;logs=0;}
    if(previous[hand]!=state.interactionProfile && logs<16u){
        previous[hand]=state.interactionProfile;++logs;
        ext_Log(">>> S26DG controller fingers hand %d: %s; runtime skeletal input %s",hand,
            state.interactionProfile==g_s26nProfiles[5]?"Steam Frame":
            state.interactionProfile==g_s26nProfiles[1]?"Valve Index":"other controller",
            allowed?"eligible; awaiting valid skeleton":"grip/trigger fallback");
    }
    return allowed;
}
