/* XR_EXT_hand_tracking alone does not prove independent controller fingers.
   Quest/Touch runtimes can supply inferred controller-holding skeletons. */
static i32 s26u_controller_fingers_allowed(Handle session,i32 hand){
    if(hand<0||hand>1||!session||!pGetCurrentInteractionProfile||!g_handPath[hand]||!g_s26nProfiles[1])return 0;
    XrInteractionProfileState state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_INTERACTION_PROFILE_STATE;
    if(pGetCurrentInteractionProfile(session,g_handPath[hand],&state)<0)return 0;
    /* Currently verified independent-finger controller profile: Valve Index.
       Unknown profiles fall back to grip/trigger instead of guessing capability. */
    return state.interactionProfile==g_s26nProfiles[1];
}
