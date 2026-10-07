/* Explicit Frame bindings prevent SteamVR's Touch emulation from concealing
   the controller identity. Existing action names and remapping stay intact. */
/* Shared contact actions are created once, before action sets are attached.
   Keep existing action names for saved runtime bindings. */
static i32 s26ee_rest_actions(void){
    const char names[2][3][32]={{"left_frame_thumb_touch","left_frame_index_touch","left_frame_grip_touch"},{"right_frame_thumb_touch","right_frame_index_touch","right_frame_grip_touch"}};
    i32 good=1;
    for(i32 h=0;h<2;++h)for(i32 g=0;g<3;++g)
        if(!g_s26dlRestTouchAction[h][g]&&create_action(names[h][g],names[h][g],XR_ACTION_TYPE_BOOLEAN_INPUT,&g_s26dlRestTouchAction[h][g])<0)good=0;
    return good;
}
static void s26dg_frame_binding(Handle inst,const XrActionSuggestedBinding* base,u32 count){
    g_s26nProfiles[5]=0;
    g_s26dlRestBindings&=~1u;g_s26ebExtraBound=0;
    if(!g_s26dgFrameExtension)return;
    if(count<21u||count>23u)return;
    XrPath profile=0,center=0,menu=0;
    i32 r=pStringToPath(inst,"/interaction_profiles/valve/frame_controller_valve",&profile);
    if(r<0||!profile)return;
    if(pStringToPath(inst,"/user/hand/left/input/dpad_up/click",&center)<0||
       pStringToPath(inst,"/user/hand/left/input/dpad_left/click",&menu)<0||!center||!menu)return;
    XrActionSuggestedBinding binds[51];for(u32 i=0;i<count;++i)binds[i]=base[i];
    binds[18].binding=center;binds[20].binding=menu;
    static const char extraPaths[8][64]={"/user/hand/left/input/bumper/click","/user/hand/right/input/bumper/click",
        "/user/hand/left/input/dpad_down/click","/user/hand/left/input/dpad_right/click",
        "/user/hand/right/input/x/click","/user/hand/right/input/y/click",
        "/user/hand/left/input/view/click","/user/hand/right/input/menu/click"};
    static const char extraNames[8][32]={"left_shoulder","right_shoulder","dpad_down","dpad_right","right_x","right_y","view_button","menu_button"};
    static const char extraLabels[8][32]={"Left Shoulder","Right Shoulder","D-Pad Down","D-Pad Right","Right X","Right Y","View","Menu"};
    u32 buttonCount=0;
    for(u32 k=0;k<8u;++k){
        XrPath path=0;
        if(create_action_in_set(g_h5724FaceActionSet,extraNames[k],extraLabels[k],XR_ACTION_TYPE_BOOLEAN_INPUT,&g_s26ebExtraAction[k])<0||
           pStringToPath(inst,extraPaths[k],&path)<0||!path)break;
        binds[count+k].action=g_s26ebExtraAction[k];binds[count+k].binding=path;++buttonCount;
    }
    if(buttonCount!=8u)buttonCount=0;
    // Separate thumb, index and grip contact. A joystick touch must not wake
    // the runtime's estimated ring/pinky rest curls. OR only within a group.
    const char touch[2][10][16]={
        {"squeeze","trigger","bumper","thumbstick","dpad_up","dpad_down","dpad_left","dpad_right","view","system"},
        {"squeeze","trigger","bumper","thumbstick","a","b","x","y","menu","system"}};
    i32 extraOk=s26ee_rest_actions();
    for(i32 hand=0;hand<2&&extraOk;++hand)for(i32 k=0;k<10;++k){
        char path[96];const char* prefix=hand?"/user/hand/right/input/":"/user/hand/left/input/";u32 at=0;
        for(u32 j=0;prefix[j];++j)path[at++]=prefix[j];
        for(u32 j=0;touch[hand][k][j];++j)path[at++]=touch[hand][k][j];
        const char* suffix="/touch";for(u32 j=0;suffix[j];++j)path[at++]=suffix[j];path[at]=0;
        XrPath pt=0;if(pStringToPath(inst,path,&pt)<0||!pt){extraOk=0;break;}
        binds[count+buttonCount+(u32)hand*10u+(u32)k].action=g_s26dlRestTouchAction[hand][k==0?2:(k<=2?1:0)];binds[count+buttonCount+(u32)hand*10u+(u32)k].binding=pt;
    }
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));
    sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;
    sb.countSuggestedBindings=count+buttonCount+(extraOk?20u:0u);sb.suggestedBindings=binds;
    r=pSuggestBindings(inst,&sb);
    if(r>=0&&extraOk)g_s26dlRestBindings|=1u;
    if(r<0&&extraOk){sb.countSuggestedBindings=count+buttonCount;r=pSuggestBindings(inst,&sb);}
    if(r>=0&&buttonCount==8u)g_s26ebExtraBound=1;
    if(r<0&&buttonCount){sb.countSuggestedBindings=count;r=pSuggestBindings(inst,&sb);}
    if(r<0&&count>21u){sb.countSuggestedBindings=21u;r=pSuggestBindings(inst,&sb);}
    if(r>=0)g_s26nProfiles[5]=profile;
    ext_Log(">>> S26DM Frame per-group capacitive release %s; unknown/inactive touch retains skeletal mapping",g_s26dlRestBindings?"bound":"unavailable");
    ext_Log(">>> S26DG Steam Frame bindings %s (%d): left D-pad left=menu, up=recenter; right A=jump, B=run/back; sticks/grip/trigger unchanged",r>=0?"accepted":"unavailable; existing profiles retained",r);
}
#include "controller_rest_ee.inc"
#include "frame_rest_dl.inc"

static void s26eb_extra_tick(Handle session,i32 focused){
    for(u32 k=0;k<8u;++k){
        g_s26ebExtraRaw[k]=g_s26ebExtraActive[k]=0;
        if(!focused||!g_s26ebExtraBound||!session||!pGetActionStateBoolean)continue;
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;gi.action=g_s26ebExtraAction[k];
        XrActionStateBoolean bs;zero_bytes(&bs,sizeof(bs));bs.type=XR_TYPE_ACTION_STATE_BOOLEAN;
        if(pGetActionStateBoolean(session,&gi,&bs)==0&&bs.isActive){g_s26ebExtraActive[k]=1;g_s26ebExtraRaw[k]=(u8)(bs.currentState!=0);}
    }
}
