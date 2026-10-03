/* S26EC: Valve Index controller ("Knuckles") parity with the Steam Frame path.
   The six gameplay roles keep the Index layout already in use: right A=jump,
   right B=run/back, left A=pause, left B=recenter, stick clicks unchanged.
   Index additionally supplies the shared per-group capacitive contact actions
   and both trackpads as remappable extra sources. The profile has no
   trackpad/click and no squeeze/touch: OpenXR thresholds (with hysteresis) a
   boolean action bound to the scalar trackpad/force and squeeze/value paths.
   Each optional layer is dropped independently if the runtime rejects it, so
   the established 23/21-binding Index suggestion always remains available. */
#define S26EC_INDEX_EXTRA_COUNT 2u
#define S26EC_INDEX_TOUCH_PER_HAND 6u
static const char g_s26ecIndexExtraPaths[S26EC_INDEX_EXTRA_COUNT][48]={
    "/user/hand/left/input/trackpad/force","/user/hand/right/input/trackpad/force"};
/* Thumb surfaces (0), index finger (1) and the grip capacitive curl (2). The
   system button is omitted: the runtime may reserve it for its dashboard. */
static const char g_s26ecIndexTouch[S26EC_INDEX_TOUCH_PER_HAND][24]={
    "thumbstick/touch","trackpad/touch","a/touch","b/touch","trigger/touch","squeeze/value"};
static const u8 g_s26ecIndexTouchGroup[S26EC_INDEX_TOUCH_PER_HAND]={0,0,0,0,1,2};
static i32 s26ec_index_binding(Handle inst,XrPath profile,const XrActionSuggestedBinding* base,u32 count){
    g_s26dlRestBindings&=~2u;g_s26ebExtraBound&=(u8)~2u;
    if(!profile||count<21u||count>23u)return -1;
    XrActionSuggestedBinding binds[23u+S26EC_INDEX_EXTRA_COUNT+2u*S26EC_INDEX_TOUCH_PER_HAND];
    for(u32 i=0;i<count;++i)binds[i]=base[i];
    u32 shared=s26ec_shared_actions();
    u32 buttonCount=0;
    for(u32 k=0;k<S26EC_INDEX_EXTRA_COUNT&&(shared&1u);++k){
        XrPath path=0;if(pStringToPath(inst,g_s26ecIndexExtraPaths[k],&path)<0||!path)break;
        binds[count+k].action=g_s26ebExtraAction[k];binds[count+k].binding=path;++buttonCount;
    }
    if(buttonCount!=S26EC_INDEX_EXTRA_COUNT)buttonCount=0;
    i32 touchOk=(shared&2u)?1:0;u32 at=count+buttonCount;
    for(i32 hand=0;hand<2&&touchOk;++hand)for(u32 k=0;k<S26EC_INDEX_TOUCH_PER_HAND;++k){
        char path[64];const char* prefix=hand?"/user/hand/right/input/":"/user/hand/left/input/";u32 n=0;
        for(u32 j=0;prefix[j];++j)path[n++]=prefix[j];
        for(u32 j=0;g_s26ecIndexTouch[k][j];++j)path[n++]=g_s26ecIndexTouch[k][j];path[n]=0;
        XrPath pt=0;if(pStringToPath(inst,path,&pt)<0||!pt){touchOk=0;break;}
        binds[at].action=g_s26dlRestTouchAction[hand][g_s26ecIndexTouchGroup[k]];binds[at++].binding=pt;
    }
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));
    sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;sb.suggestedBindings=binds;
    sb.countSuggestedBindings=count+buttonCount+(touchOk?2u*S26EC_INDEX_TOUCH_PER_HAND:0u);
    i32 r=pSuggestBindings(inst,&sb);
    if(r>=0&&touchOk)g_s26dlRestBindings|=2u;
    if(r<0&&touchOk){sb.countSuggestedBindings=count+buttonCount;r=pSuggestBindings(inst,&sb);}
    if(r>=0&&buttonCount)g_s26ebExtraBound|=2u;
    if(r<0&&buttonCount){sb.countSuggestedBindings=count;r=pSuggestBindings(inst,&sb);}
    if(r<0&&count>21u){sb.countSuggestedBindings=21u;r=pSuggestBindings(inst,&sb);}
    ext_Log(">>> S26EC Valve Index bindings %s (%d): right A=jump, B=run/back; left A=pause, B=recenter | capacitive finger release %s | trackpad press sources %s",
        r>=0?"accepted":"unavailable",r,(g_s26dlRestBindings&2u)?"bound":"unavailable",(g_s26ebExtraBound&2u)?"bound":"unavailable");
    return r;
}
