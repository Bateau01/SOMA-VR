/* S26EC: Valve Index controller ("Knuckles") parity with the Steam Frame path.
   The six gameplay roles keep the Index layout already in use: right A=jump,
   right B=run/back, left A=pause, left B=recenter, stick clicks unchanged.
   Index additionally supplies optional layers:
     extras   - both trackpads as remappable extra sources (trackpad/force)
     contacts - the shared per-group capacitive contact actions
     feel     - grip force (squeeze/force) and per-button A/B thumb rest
   The profile has no trackpad/click and no squeeze/touch: OpenXR thresholds
   (with hysteresis) a boolean action bound to a scalar path. Each optional
   layer is kept or dropped on its own if the runtime rejects it, so the
   established 23/21-binding Index suggestion always remains available. */
#define S26EC_INDEX_EXTRA_COUNT 2u
#define S26EC_INDEX_TOUCH_PER_HAND 6u
#define S26EC_INDEX_FEEL_PER_HAND 3u
#define S26EC_LAYERS 3u
static const char g_s26ecIndexExtraPaths[S26EC_INDEX_EXTRA_COUNT][48]={
    "/user/hand/left/input/trackpad/force","/user/hand/right/input/trackpad/force"};
/* Thumb surfaces (0), index finger (1) and the grip capacitive curl (2). The
   system button is omitted: the runtime may reserve it for its dashboard. */
static const char g_s26ecIndexTouch[S26EC_INDEX_TOUCH_PER_HAND][24]={
    "thumbstick/touch","trackpad/touch","a/touch","b/touch","trigger/touch","squeeze/value"};
static const u8 g_s26ecIndexTouchGroup[S26EC_INDEX_TOUCH_PER_HAND]={0,0,0,0,1,2};
static const char g_s26ecIndexFeel[S26EC_INDEX_FEEL_PER_HAND][24]={"squeeze/force","a/touch","b/touch"};
/* Index-only feel actions: grip force and A/B thumb rest, per hand. */
static Handle g_s26ecForceAction[2],g_s26ecFaceTouchAction[2][2];
static u8 g_s26ecLayers; /* bit per accepted optional layer: 1 extras, 2 contacts, 4 feel */
static float g_s26ecForce[2];
static u8 g_s26ecForceValid[2],g_s26ecFaceTouch[2][2],g_s26ecFaceTouchValid[2][2];
static u32 s26ec_feel_actions(void){
    static const char names[2][3][32]={{"left_grip_force_ec","left_a_rest_ec","left_b_rest_ec"},{"right_grip_force_ec","right_a_rest_ec","right_b_rest_ec"}};
    static const char labels[2][3][32]={{"Left Grip Force","Left A Thumb Rest","Left B Thumb Rest"},{"Right Grip Force","Right A Thumb Rest","Right B Thumb Rest"}};
    u32 ok=1;
    for(i32 h=0;h<2;++h){
        if(!g_s26ecForceAction[h]&&create_action(names[h][0],labels[h][0],XR_ACTION_TYPE_FLOAT_INPUT,&g_s26ecForceAction[h])<0){g_s26ecForceAction[h]=0;ok=0;}
        for(i32 b=0;b<2;++b)if(!g_s26ecFaceTouchAction[h][b]&&
            create_action(names[h][1+b],labels[h][1+b],XR_ACTION_TYPE_BOOLEAN_INPUT,&g_s26ecFaceTouchAction[h][b])<0){g_s26ecFaceTouchAction[h][b]=0;ok=0;}
    }
    return ok;
}
static i32 s26ec_hand_path(Handle inst,i32 hand,const char* suffix,XrPath* out){
    char path[64];const char* prefix=hand?"/user/hand/right/input/":"/user/hand/left/input/";u32 n=0;
    for(u32 j=0;prefix[j];++j)path[n++]=prefix[j];
    for(u32 j=0;suffix[j]&&n<63u;++j)path[n++]=suffix[j];path[n]=0;
    *out=0;return pStringToPath(inst,path,out)>=0&&*out;
}
static i32 s26ec_suggest(Handle inst,XrPath profile,const XrActionSuggestedBinding* base,u32 count,
                         XrActionSuggestedBinding layer[S26EC_LAYERS][12],const u32 size[S26EC_LAYERS],u32 mask){
    XrActionSuggestedBinding binds[23u+S26EC_INDEX_EXTRA_COUNT+2u*(S26EC_INDEX_TOUCH_PER_HAND+S26EC_INDEX_FEEL_PER_HAND)];
    u32 n=0;for(u32 i=0;i<count;++i)binds[n++]=base[i];
    for(u32 l=0;l<S26EC_LAYERS;++l)if(mask&(1u<<l))for(u32 i=0;i<size[l];++i)binds[n++]=layer[l][i];
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));
    sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;sb.suggestedBindings=binds;sb.countSuggestedBindings=n;
    return pSuggestBindings(inst,&sb);
}
static i32 s26ec_index_binding(Handle inst,XrPath profile,const XrActionSuggestedBinding* base,u32 count){
    g_s26dlRestBindings&=~2u;g_s26ebExtraBound&=(u8)~2u;g_s26ecLayers=0;
    if(!profile||count<21u||count>23u)return -1;
    XrActionSuggestedBinding layer[S26EC_LAYERS][12];u32 size[S26EC_LAYERS]={0,0,0};
    u32 shared=s26ec_shared_actions();
    for(u32 k=0;k<S26EC_INDEX_EXTRA_COUNT&&(shared&1u);++k){
        XrPath path=0;if(pStringToPath(inst,g_s26ecIndexExtraPaths[k],&path)<0||!path){size[0]=0;break;}
        layer[0][size[0]].action=g_s26ebExtraAction[k];layer[0][size[0]++].binding=path;
    }
    if(size[0]!=S26EC_INDEX_EXTRA_COUNT)size[0]=0;
    for(i32 hand=0;hand<2&&(shared&2u);++hand)for(u32 k=0;k<S26EC_INDEX_TOUCH_PER_HAND;++k){
        XrPath pt=0;if(!s26ec_hand_path(inst,hand,g_s26ecIndexTouch[k],&pt)){size[1]=0;hand=2;break;}
        layer[1][size[1]].action=g_s26dlRestTouchAction[hand][g_s26ecIndexTouchGroup[k]];layer[1][size[1]++].binding=pt;
    }
    if(s26ec_feel_actions())for(i32 hand=0;hand<2;++hand)for(u32 k=0;k<S26EC_INDEX_FEEL_PER_HAND;++k){
        XrPath pt=0;if(!s26ec_hand_path(inst,hand,g_s26ecIndexFeel[k],&pt)){size[2]=0;hand=2;break;}
        layer[2][size[2]].action=k==0?g_s26ecForceAction[hand]:g_s26ecFaceTouchAction[hand][k-1];layer[2][size[2]++].binding=pt;
    }
    u32 want=0;for(u32 l=0;l<S26EC_LAYERS;++l)if(size[l])want|=1u<<l;
    u32 cores[2]={count,21u};i32 r=-1;u32 accepted=0;
    for(u32 c=0;c<2u&&r<0;++c){
        if(c&&count<=21u)break;
        u32 core=cores[c];
        r=s26ec_suggest(inst,profile,base,core,layer,size,want);
        if(r>=0){accepted=want;break;}
        /* Some layer was rejected: rebuild greedily from the core suggestion,
           keeping each optional layer that the runtime accepts on its own. */
        r=s26ec_suggest(inst,profile,base,core,layer,size,0);
        if(r<0)continue;
        i32 lastOk=1;
        for(u32 l=0;l<S26EC_LAYERS;++l){
            if(!(want&(1u<<l)))continue;
            if(s26ec_suggest(inst,profile,base,core,layer,size,accepted|(1u<<l))>=0){accepted|=1u<<l;lastOk=1;}else lastOk=0;
        }
        /* A rejected call is not guaranteed to leave the previous suggestion
           in place; finish on the accepted set itself. */
        if(!lastOk)r=s26ec_suggest(inst,profile,base,core,layer,size,accepted);
        if(r<0)accepted=0;
    }
    if(r>=0){
        g_s26ecLayers=(u8)accepted;
        if(accepted&1u)g_s26ebExtraBound|=2u;
        if(accepted&2u)g_s26dlRestBindings|=2u;
    }
    ext_Log(">>> S26EC Valve Index bindings %s (%d): right A=jump, B=run/back; left A=pause, B=recenter | trackpad press sources %s | capacitive finger release %s | grip force + thumb rest %s",
        r>=0?"accepted":"unavailable",r,(accepted&1u)?"bound":"unavailable",(accepted&2u)?"bound":"unavailable",(accepted&4u)?"bound":"unavailable");
    return r;
}
/* After xrSyncActions. Inactive/failed input is never treated as pressure or
   contact; the feel layer only exists on Index, so other controllers read 0. */
static void s26ec_index_tick(Handle session,i32 focused){
    for(i32 h=0;h<2;++h){
        g_s26ecForce[h]=0.0f;g_s26ecForceValid[h]=0;
        for(i32 b=0;b<2;++b)g_s26ecFaceTouch[h][b]=g_s26ecFaceTouchValid[h][b]=0;
        if(!focused||!(g_s26ecLayers&4u)||!session||!pGetActionStateFloat||!pGetActionStateBoolean)continue;
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;gi.action=g_s26ecForceAction[h];
        XrActionStateFloat fs;zero_bytes(&fs,sizeof(fs));fs.type=XR_TYPE_ACTION_STATE_FLOAT;
        if(gi.action&&pGetActionStateFloat(session,&gi,&fs)==0&&fs.isActive&&fs.currentState>=0.0f&&fs.currentState<=1.0f){g_s26ecForce[h]=fs.currentState;g_s26ecForceValid[h]=1;}
        for(i32 b=0;b<2;++b){
            gi.action=g_s26ecFaceTouchAction[h][b];XrActionStateBoolean bs;zero_bytes(&bs,sizeof(bs));bs.type=XR_TYPE_ACTION_STATE_BOOLEAN;
            if(gi.action&&pGetActionStateBoolean(session,&gi,&bs)==0&&bs.isActive){g_s26ecFaceTouchValid[h][b]=1;g_s26ecFaceTouch[h][b]=(u8)(bs.currentState!=0);}
        }
    }
}
