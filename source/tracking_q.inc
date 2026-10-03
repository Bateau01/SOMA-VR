/* Optional OpenXR input. Layouts checked against Khronos OpenXR 1.1.63.
   This code runs on the existing XR initialization/frame thread. */
typedef struct { char applicationName[128];u32 applicationVersion;char engineName[128];u32 engineVersion;u64 apiVersion; } S26QApplicationInfo;
typedef struct { i32 type;const void* next;u64 createFlags;S26QApplicationInfo applicationInfo;u32 enabledApiLayerCount;const char* const* enabledApiLayerNames;u32 enabledExtensionCount;const char* const* enabledExtensionNames; } S26QInstanceInfo;
typedef struct { i32 type;void* next;char extensionName[128];u32 extensionVersion; } S26QExtension;
_Static_assert(sizeof(S26QInstanceInfo)==328,"OpenXR instance ABI");
_Static_assert(sizeof(S26QExtension)==152,"OpenXR extension ABI");
typedef i32 (__attribute__((ms_abi)) *S26QGetProc)(Handle,const char*,void**);
typedef i32 (__attribute__((ms_abi)) *S26QCreateInstance)(const S26QInstanceInfo*,Handle*);
typedef i32 (__attribute__((ms_abi)) *S26QEnumExtensions)(const char*,u32,u32*,S26QExtension*);
typedef i32 (__attribute__((ms_abi)) *S26QDestroy)(Handle);
static S26QCreateInstance g_s26qCreateInstance;
static S26QEnumExtensions g_s26qEnumExtensions;
static S26QDestroy g_s26qDestroySession;
/* S26ED: XR_KHR_composition_layer_depth, used only by the opt-in depth layer. */
static u8 g_s26edDepthExtension;
static u8 g_s26qTrackerEnabled;
static Handle g_s26qWaistAction,g_s26qWaistSpace,g_s26qTrackerSession;
static u32 g_s26qTrackingLogs;
static u8 g_s26qReportedTracking;
static i32 g_s26qWaistAxis;
static float g_s26qWaistMountC=1.0f,g_s26qWaistMountS;
static i32 s26q_waist_heading(const float* q,float* c,float* s){
    /* Choose a horizontal local axis during calibration, since trackers can be
       mounted flat, upright, or sideways. Keep that axis until explicit recenter. */
    float x=q[0],y=q[1],z=q[2],w=q[3];
    float fc[3]={-2.0f*(x*z-w*y),-2.0f*(y*z+w*x),1.0f-2.0f*(x*x+y*y)};
    float fs[3]={-1.0f+2.0f*(y*y+z*z),-2.0f*(x*y-w*z),2.0f*(x*z+w*y)};
    if(!g_s26qWaistCalibrated){
        if(!g_h5745HeadPoseCalls)return 0;
        float best=-1.0f;
        for(i32 a=0;a<3;++a){float n=fc[a]*fc[a]+fs[a]*fs[a];if(n>best){best=n;g_s26qWaistAxis=a;}}
    }
    i32 a=g_s26qWaistAxis;float n=ext_Sqrtf(fc[a]*fc[a]+fs[a]*fs[a]);
    if(!(n>0.15f&&n<1.1f))return 0;
    float rc=fc[a]/n,rs=fs[a]/n;
    if(!g_s26qWaistCalibrated){
        float hc=g_s26HeadMoveC,hs=g_s26HeadMoveS,hn=ext_Sqrtf(hc*hc+hs*hs);
        if(!(hn>0.9f&&hn<1.1f))return 0;
        hc/=hn;hs/=hn;g_s26qWaistMountC=hc*rc+hs*rs;g_s26qWaistMountS=hs*rc-hc*rs;
        g_s26qWaistCalibrated=1;g_s26qWaistNeutral=0;
    }
    *c=g_s26qWaistMountC*rc-g_s26qWaistMountS*rs;
    *s=g_s26qWaistMountS*rc+g_s26qWaistMountC*rs;return 1;
}
static i32 s26q_name_eq(const char* a,const char* b){
    if(!a||!b)return 0;
    for(u32 i=0;i<128u;++i){if(a[i]!=b[i])return 0;if(!a[i])return 1;}return 0;
}
static i32 __attribute__((ms_abi)) s26q_create_instance(const S26QInstanceInfo* in,Handle* out){
    g_s26qTrackerEnabled=0;g_s26qHandExtension=0;g_s26sEyeExtension=0;g_s26dgFrameExtension=0;g_s26dnMotionRangeEnabled=0;g_s26edDepthExtension=0;
    if(!g_s26qCreateInstance)return -6;
    if(!in||!out||in->type!=3||in->enabledExtensionCount>64u||
       (in->enabledExtensionCount&&!in->enabledExtensionNames)||!g_s26qEnumExtensions)
        return g_s26qCreateInstance(in,out);
    static const char optional[6][64]={"XR_HTCX_vive_tracker_interaction","XR_EXT_hand_tracking","XR_EXT_eye_gaze_interaction","XR_VALVE_frame_controller_interaction","XR_EXT_hand_joints_motion_range","XR_KHR_composition_layer_depth"};
    u8 available[6]={0},present[6]={0},enabled[6]={0};
    u32 count=0;i32 r=g_s26qEnumExtensions(0,0,&count,0);
    if(r>=0&&count&&count<=512u){
        S26QExtension* props=(S26QExtension*)ext_malloc((u64)count*sizeof(S26QExtension));
        if(props){
            zero_bytes(props,(u64)count*sizeof(S26QExtension));for(u32 i=0;i<count;++i)props[i].type=2;
            u32 actual=0;r=g_s26qEnumExtensions(0,count,&actual,props);
            if(r>=0&&actual<=count)for(u32 i=0;i<actual;++i)for(u32 j=0;j<6u;++j)
                if(s26q_name_eq(props[i].extensionName,optional[j]))available[j]=1;
            ext_free(props);
        }
    }
    const char* names[70];u32 n=in->enabledExtensionCount;
    for(u32 i=0;i<n;++i){names[i]=in->enabledExtensionNames[i];for(u32 j=0;j<6u;++j)if(s26q_name_eq(names[i],optional[j]))present[j]=1;}
    for(u32 j=0;j<6u;++j){enabled[j]=present[j];if(available[j]&&!present[j]&&(j!=4u||enabled[1])){names[n++]=optional[j];enabled[j]=1;}}
    S26QInstanceInfo ci;
    for(u32 i=0;i<sizeof(ci);++i)((volatile u8*)&ci)[i]=((const u8*)in)[i];
    ci.enabledExtensionCount=n;ci.enabledExtensionNames=names;
    r=g_s26qCreateInstance(n==in->enabledExtensionCount?in:&ci,out);
    if(r<0&&enabled[5]&&!present[5]){
        /* Appended last, so it is dropped first; nothing else depends on it. */
        *out=0;enabled[5]=0;--n;ci.enabledExtensionCount=n;
        ext_Log(">>> S26ED depth-layer extension rejected (%d); retaining prior tracking configuration",r);
        r=g_s26qCreateInstance(n==in->enabledExtensionCount?in:&ci,out);
    }
    if(r<0&&enabled[4]&&!present[4]){
        *out=0;enabled[4]=0;--n;ci.enabledExtensionCount=n;
        ext_Log(">>> S26DN motion-range extension rejected (%d); retaining prior tracking configuration",r);
        r=g_s26qCreateInstance(&ci,out);
    }
    if(r<0&&enabled[3]&&!present[3]){
        /* A newly advertised Frame extension must not take working Index/gaze
           support down with it. Retry the prior optional-extension set first. */
        *out=0;enabled[3]=0;--n;ci.enabledExtensionCount=n;
        ext_Log(">>> S26DG Frame extension rejected (%d); retrying prior tracking configuration",r);
        r=g_s26qCreateInstance(&ci,out);
    }
    if(r<0&&n!=in->enabledExtensionCount){
        *out=0;enabled[0]=present[0];enabled[1]=present[1];enabled[2]=present[2];enabled[3]=present[3];enabled[4]=present[4];enabled[5]=present[5];
        ext_Log(">>> S26Q optional tracking extensions rejected (%d); retrying original OpenXR configuration",r);
        r=g_s26qCreateInstance(in,out);
    }
    if(r>=0&&*out){g_s26qTrackerEnabled=enabled[0];g_s26qHandExtension=enabled[1];g_s26sEyeExtension=enabled[2];g_s26dgFrameExtension=enabled[3];g_s26dnMotionRangeEnabled=enabled[4];g_s26edDepthExtension=enabled[5];
        ext_Log(">>> S26DN unobstructed finger motion request %s",enabled[4]?"enabled":"unsupported; runtime default");
        ext_Log(">>> S26Q OpenXR tracking extensions: waist %u skeletal hands %u eye gaze %u Steam Frame %u depth layer %u",(u32)enabled[0],(u32)enabled[1],(u32)enabled[2],(u32)enabled[3],(u32)enabled[5]);}
    return r;
}
u8 __attribute__((ms_abi)) s26q_instance_wrapper(void* self){
    if(!self)return 0;
    void** slot=(void**)((u8*)self+0x1d0);
    S26QGetProc get=*(S26QGetProc*)((u8*)self+0x1c8);
    g_s26qCreateInstance=(S26QCreateInstance)*slot;g_s26qEnumExtensions=0;
    if(get)get(0,"xrEnumerateInstanceExtensionProperties",(void**)&g_s26qEnumExtensions);
    *slot=(void*)s26q_create_instance;
    u8 result=ext_OrigCreateInstanceAndSystem(self);
    *slot=(void*)g_s26qCreateInstance;
    return result;
}
static i32 __attribute__((ms_abi)) s26q_destroy_session(Handle session){
    s26s_eye_end(session);
    s26q_ref_end(session);
    s26q_hands_end(session);
    if(session==g_s26qTrackerSession){
        /* xrDestroySession destroys its child spaces; no stale child handle is reused. */
        g_s26qWaistSpace=0;g_s26qWaistAction=0;g_s26qTrackerSession=0;
        g_s26qWaistValid=0;g_s26qWaistNeutral=0;g_s26qWaistCalibrated=0;
    }
    return g_s26qDestroySession?g_s26qDestroySession(session):-12;
}
static void s26q_hook_destroy(void* self){
    S26QDestroy* slot=(S26QDestroy*)((u8*)self+0x1f0);
    if(*slot!=s26q_destroy_session){g_s26qDestroySession=*slot;*slot=s26q_destroy_session;}
}
static void s26q_tracker_binding(void* self,Handle inst,Handle sess){
    if(!g_s26qTrackerEnabled||!self||!inst||!sess)return;
    XrPath profile=0,path=0;
    if(pStringToPath(inst,"/interaction_profiles/htc/vive_tracker_htcx",&profile)<0||
       pStringToPath(inst,"/user/vive_tracker_htcx/role/waist/input/grip/pose",&path)<0||!profile||!path)return;
    if(create_action("waist_direction_q1","Waist Tracker Movement Direction",XR_ACTION_TYPE_POSE_INPUT,&g_s26qWaistAction)<0||!g_s26qWaistAction)return;
    XrActionSuggestedBinding binding={g_s26qWaistAction,path};
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));
    sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;sb.countSuggestedBindings=1;sb.suggestedBindings=&binding;
    i32 result=pSuggestBindings(inst,&sb);
    if(result<0){g_s26qWaistAction=0;ext_Log(">>> S26Q waist tracker binding unavailable (%d)",result);return;}
    XrActionSpaceCreateInfo sci;zero_bytes(&sci,sizeof(sci));
    sci.type=XR_TYPE_ACTION_SPACE_CREATE_INFO;sci.action=g_s26qWaistAction;sci.poseInActionSpace.orientation.w=1.0f;
    result=pCreateActionSpace(sess,&sci,&g_s26qWaistSpace);
    if(result<0||!g_s26qWaistSpace){g_s26qWaistSpace=0;g_s26qWaistAction=0;return;}
    g_s26qTrackerSession=sess;g_s26qWaistValid=0;g_s26qWaistNeutral=0;g_s26qWaistCalibrated=0;
    s26q_hook_destroy(self);
    ext_Log(">>> S26Q waist tracker action ready; role must be assigned to WAIST in runtime");
}
static void s26q_tracker_tick(Handle sess,Handle baseSpace,i64 time,i32 syncResult){
    u8 was=g_s26qReportedTracking;g_s26qWaistValid=0;
    if(g_s26qWaistAction&&g_s26qWaistSpace&&sess==g_s26qTrackerSession&&baseSpace&&time>0&&syncResult==0){
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;gi.action=g_s26qWaistAction;
        XrActionStatePose state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_ACTION_STATE_POSE;
        XrSpaceLocation loc;zero_bytes(&loc,sizeof(loc));loc.type=XR_TYPE_SPACE_LOCATION;
        if(pGetActionStatePose(sess,&gi,&state)==0&&state.isActive&&pLocateSpace(g_s26qWaistSpace,baseSpace,time,&loc)==0&&(loc.locationFlags&5u)==5u){
            float q[4]={loc.pose.orientation.x,loc.pose.orientation.y,loc.pose.orientation.z,loc.pose.orientation.w};
            float norm=q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3];
            if(norm>0.98f&&norm<1.02f&&s26q_waist_heading(q,&g_s26qWaistC,&g_s26qWaistS))g_s26qWaistValid=1;
        }
    }
    if(!g_s26qWaistValid)g_s26qWaistNeutral=0;
    if(was!=g_s26qWaistValid&&g_s26qTrackingLogs<32u){++g_s26qTrackingLogs;ext_Log(">>> S26Q waist tracking %s",g_s26qWaistValid?"active; release movement stick to resume":"lost; hip movement stopped");}
    g_s26qReportedTracking=g_s26qWaistValid;
}
