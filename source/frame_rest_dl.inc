/* After xrSyncActions and before skeletal conversion. Contact is grouped by
   physical surface; absent/failed input never establishes release. */
static i32 s26dl_is_released(i32 known,i32 touched,i32 analogKnown,float analog){
    return known&&!touched&&analogKnown&&analog>=0.0f&&analog<=0.02f;
}
static void s26dl_rest_tick(Handle session,i32 focused){
    for(i32 h=0;h<2;++h){
        g_s26dlReleased[h]=g_s26dlTouchKnown[h]=g_s26dlTouched[h]=g_s26dmReleasedMask[h]=0;
        if(!focused||!g_s26dlRestBindings||!session||!pGetActionStateBoolean||!pGetActionStateFloat)continue;
        /* Binding availability is per profile, and checked every sync. A
           profile switch must not reuse the previous controller's release. */
        u32 profile=s26ee_rest_profile(session,h);
        if(!(profile&g_s26dlRestBindings))continue;
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;
        XrActionStateFloat gs,ts;zero_bytes(&gs,sizeof(gs));zero_bytes(&ts,sizeof(ts));gs.type=ts.type=XR_TYPE_ACTION_STATE_FLOAT;
        gi.action=g_squeezeAction[h];i32 gr=pGetActionStateFloat(session,&gi,&gs);
        gi.action=g_triggerAction[h];i32 tr=pGetActionStateFloat(session,&gi,&ts);
        u32 knownMask=0;
        for(i32 group=0;group<3;++group){
            XrActionStateBoolean bs;zero_bytes(&bs,sizeof(bs));bs.type=XR_TYPE_ACTION_STATE_BOOLEAN;
            gi.action=g_s26dlRestTouchAction[h][group];i32 br=pGetActionStateBoolean(session,&gi,&bs);
            i32 known=br==0&&bs.isActive;
            /* Index has squeeze/value, not squeeze/touch. Use the active
               scalar directly; boolean conversion thresholds cannot prove
               that the grip fingers are released. */
            if(profile==2u&&group==2){
                known=gr==0&&gs.isActive&&gs.currentState>=0.0f&&gs.currentState<=1.0f;
                bs.currentState=known&&gs.currentState>0.02f;
            }
            u32 mask=group==0?1u:(group==1?2u:28u);
            if(known)knownMask|=mask;if(known&&bs.currentState)g_s26dlTouched[h]|=mask;
            // Thumb has no analog squeeze dependency. Trigger and grip guard
            // against a delayed capacitive release during an actual press.
            i32 ak=group==0?1:(group==1?tr==0&&ts.isActive:gr==0&&gs.isActive);
            float av=group==0?0.0f:(group==1?ts.currentState:gs.currentState);
            if(s26dl_is_released(known,bs.currentState,ak,av))g_s26dmReleasedMask[h]|=mask;
        }
        g_s26dlTouchKnown[h]=knownMask;g_s26dlReleased[h]=g_s26dmReleasedMask[h]==31u;
    }
}
