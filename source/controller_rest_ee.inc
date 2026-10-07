/* Optional Index release evidence. No gameplay binding or grab threshold is
   changed. Other profiles retain manual reset unless a verified contact map
   is added here. Generic skeletal mapping and motion range are independent. */
static u32 s26ee_rest_profile(Handle session,i32 hand){
    if(!session||hand<0||hand>1||!pGetCurrentInteractionProfile||!g_handPath[hand])return 0;
    XrInteractionProfileState state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_INTERACTION_PROFILE_STATE;
    if(pGetCurrentInteractionProfile(session,g_handPath[hand],&state)<0||!state.interactionProfile)return 0;
    if(state.interactionProfile==g_s26nProfiles[5])return 1u;
    if(state.interactionProfile==g_s26nProfiles[1])return 2u;
    return 0;
}
static i32 s26ee_index_rest_binding(Handle inst,const XrActionSuggestedBinding* base,u32 count){
    g_s26dlRestBindings&=~2u;
    if(count<21u||count>23u||!g_s26nProfiles[1])return -1;
    XrActionSuggestedBinding binds[33];for(u32 i=0;i<count;++i)binds[i]=base[i];
    /* Inline strings keep the injected payload position-independent. */
    static const char paths[2][5][64]={
        {"/user/hand/left/input/thumbstick/touch","/user/hand/left/input/trackpad/touch","/user/hand/left/input/a/touch","/user/hand/left/input/b/touch","/user/hand/left/input/trigger/touch"},
        {"/user/hand/right/input/thumbstick/touch","/user/hand/right/input/trackpad/touch","/user/hand/right/input/a/touch","/user/hand/right/input/b/touch","/user/hand/right/input/trigger/touch"}};
    i32 available=s26ee_rest_actions();u32 n=count;
    for(i32 h=0;h<2&&available;++h)for(i32 k=0;k<5;++k){
        XrPath path=0;
        if(pStringToPath(inst,paths[h][k],&path)<0||!path){available=0;break;}
        binds[n].action=g_s26dlRestTouchAction[h][k==4?1:0];binds[n++].binding=path;
    }
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));
    sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=g_s26nProfiles[1];sb.suggestedBindings=binds;
    sb.countSuggestedBindings=available?n:count;i32 result=pSuggestBindings(inst,&sb);
    if(result>=0&&available)g_s26dlRestBindings|=2u;
    if(result<0){sb.countSuggestedBindings=count;result=pSuggestBindings(inst,&sb);}
    if(result<0&&count>21u){sb.countSuggestedBindings=21u;result=pSuggestBindings(inst,&sb);}
    ext_Log(">>> S26EE Index rest contact %s; gameplay binding result %d",(g_s26dlRestBindings&2u)?"available":"unavailable; manual reset retained",result);
    return result;
}
