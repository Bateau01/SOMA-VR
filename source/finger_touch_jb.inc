/* Choose one fingertip before entering the existing one-shot dispatch chain.
   No callback, input edge or ownership change happens during this selection.
   Extra fingers are confined to icon13 world controls; index terminal entry
   and all connected-screen/phone pointer paths retain their existing rules. */
static i32 g_s26jbTouchFinger[2]={1,1};
// Current-call values, refreshed before either endpoint or crossing selection.
static float g_s26jbTouchPoints[2][5][5][3];
static i32 g_s26jbTouchLengths[2][5],g_s26jbTouchValid[2][5];
static i32 s26jb_choose_touch_finger(i32 hand,const float* m,float out[5][3],i32* outLen){
    float (*pts)[5][3]=g_s26jbTouchPoints[hand];i32* len=g_s26jbTouchLengths[hand];i32* valid=g_s26jbTouchValid[hand];
    for(i32 f=0;f<5;f++)valid[f]=s26jb_raw_finger(hand,f,m,pts[f],&len[f]);
    i32 chosen=-1;float best=999.0f;
    // Any finger maintaining the accepted contact keeps its one-shot latch.
    // This prevents changing fingers on one button from producing extra clicks.
    if(g_h574RockerLatchBody[hand]){
        for(i32 f=0;f<5;f++)if(valid[f]){
            float gap,cp[3];
            if(!s26eq_return_point(g_h574RockerLatchBody[hand],pts[f][len[f]],&gap,cp))continue;
            float skin=gap-s26jb_finger_skin_radius(hand,f,len[f]);
            if(skin<=H574_ROCKER_RELEASE_GAP_M&&skin<best){best=skin;chosen=f;}
        }
    }
    if(chosen<0){
        PFN_H37_GetClosestEntity fn=0;void* helper=h37_map_helper(&fn);
        // Index wins exact ties, retaining its familiar targeting priority.
        const i32 order[5]={1,0,2,3,4};best=999.0f;
        for(i32 k=0;k<5;k++){
            i32 f=order[k];if(!valid[f]||h10_raw_finger_input(hand,f)>H48_POKE_INDEX_CURL_MAX)continue;
            if(!helper||!fn)continue;
            float* tip=pts[f][len[f]];float* prev=pts[f][len[f]-1];
            float dir[3]={tip[0]-prev[0],tip[1]-prev[1],tip[2]-prev[2]};if(!h10_norm3(dir))continue;
            float start[3]={tip[0]-dir[0]*.001f,tip[1]-dir[1]*.001f,tip[2]-dir[2]*.001f};
            float distance=999.0f;void* wrapper=0;void* owner=0;
            float length=g_s26yCount?.035f:H485_SWITCH_RAY_M;
            if(!fn(helper,start,dir,length,0,0,&distance,&wrapper,&owner)||distance<0||distance>length||
               !h37_native_wrapper_matches_entity(wrapper,owner))continue;
            const void* body=0;void* can=0;void* on=0;i32 icon=-1;
            if(!h20_mem_readable(wrapper,0x2f0u))continue;
            body=*(const void**)((u8*)wrapper+0x2e8);
            i32 slot=s26y_body_slot(body);
            if(slot>=0){if(!g_s26yRocker[slot].active)continue;}
            else if(!h483_surface_target_info(wrapper,owner,&icon,&body,&can,&on)||icon!=H482_POKE_SWITCH_ICON)continue;
            float gap,cp[3];if(!h14_point_to_body(body,tip,&gap,cp))continue;
            float skin=gap-s26jb_finger_skin_radius(hand,f,len[f]);
            if(skin<0)skin=0;
            if(skin<=H572_SWITCH_SKIN_TOUCH_M&&skin<best){best=skin;chosen=f;}
        }
        // Preserve the index's cached-body fallback and terminal-entry path.
        if(chosen<0&&valid[1]&&h10_raw_finger_input(hand,1)<=H48_POKE_INDEX_CURL_MAX)chosen=1;
    }
    if(chosen<0)return -1;
    *outLen=len[chosen];for(i32 j=0;j<=*outLen;j++)for(i32 a=0;a<3;a++)out[j][a]=pts[chosen][j][a];
    return chosen;
}
