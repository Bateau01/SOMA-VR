/* Optional OpenXR gaze; no desktop tracker emulation and no synthetic blinks. */
static Handle g_s26sEyeAction,g_s26sEyeSpace,g_s26sEyeSession,g_s26dgEyeView;
typedef struct {i32 type;const void* next;i32 referenceSpaceType;XrPosef poseInReferenceSpace;} S26DGEyeRefInfo;
typedef i32 (__attribute__((ms_abi)) *S26DGEyeCreateRef)(Handle,const S26DGEyeRefInfo*,Handle*);
_Static_assert(sizeof(S26DGEyeRefInfo)==48,"eye VIEW create ABI");
typedef struct {i32 type;const void* next;i32 formFactor;} S26DGEyeSystemInfo;
typedef struct {i32 type;void* next;u32 supported;} S26DGEyeProperties;
typedef struct {i32 type;void* next;u64 systemId;u32 vendorId;char name[256];u32 graphics[3],tracking[2];} S26DGSystemProperties;
_Static_assert(sizeof(S26DGSystemProperties)==304,"system properties ABI");
static void s26dg_eye_system(void* self,Handle inst){
    PFN_GIPA get=*(PFN_GIPA*)((u8*)self+0x1c8);
    i32 (__attribute__((ms_abi)) *system)(Handle,const S26DGEyeSystemInfo*,u64*)=0;
    i32 (__attribute__((ms_abi)) *properties)(Handle,u64,S26DGSystemProperties*)=0;
    if(!get||get(inst,"xrGetSystem",(void**)&system)<0||!system||
       get(inst,"xrGetSystemProperties",(void**)&properties)<0||!properties)return;
    S26DGEyeSystemInfo info={4,0,1};u64 id=0;i32 r=system(inst,&info,&id);
    if(r<0||!id){ext_Log(">>> S26DG eye gaze system query failed (%d)",r);return;}
    S26DGEyeProperties eye={1000030000,0,0};S26DGSystemProperties props;zero_bytes(&props,sizeof(props));props.type=5;props.next=&eye;
    r=properties(inst,id,&props);
    ext_Log(">>> S26DG eye gaze device support %u (system query %d); action activity still requires runtime access and calibration",eye.supported,r);
}
typedef struct {i32 type;void* next;i64 time;} S26SEyeSampleTime;
typedef struct {XrPosef eye,head;i64 time;u8 valid,headValid;} S26SEyeSample;
static S26SEyeSample g_s26sEyeSample;
static u32 g_s26sEyeLock,g_s26sEyeLogs;
static u8 g_s26sEyeReported=255;
static i32 s26s_eye_lock(void){u32 expected=0;return __atomic_compare_exchange_n(&g_s26sEyeLock,&expected,1u,0,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED);}
static void s26s_eye_unlock(void){__atomic_store_n(&g_s26sEyeLock,0u,__ATOMIC_RELEASE);}
static void s26s_eye_end(Handle session){
    if(session!=g_s26sEyeSession)return;
    g_s26sEyeAction=0;g_s26sEyeSpace=0;g_s26sEyeSession=0;g_s26dgEyeView=0;
    if(s26s_eye_lock()){g_s26sEyeSample.valid=0;g_s26sEyeSample.headValid=0;s26s_eye_unlock();}
    g_s26sEyeReported=255;g_s26sEyeLogs=0;
}
static void s26s_eye_binding(void* self,Handle inst,Handle sess){
    if(!g_s26sEyeExtension){ext_Log(">>> S26DG eye gaze unavailable: runtime extension not enabled");return;}
    if(!self||!inst||!sess)return;
    s26dg_eye_system(self,inst);
    XrPath profile=0,path=0;
    if(pStringToPath(inst,"/interaction_profiles/ext/eye_gaze_interaction",&profile)<0||
       pStringToPath(inst,"/user/eyes_ext/input/gaze_ext/pose",&path)<0){ext_Log(">>> S26DG eye gaze path creation failed");return;}
    i32 r=create_action("eye_gaze_s1","Eye Gaze",XR_ACTION_TYPE_POSE_INPUT,&g_s26sEyeAction);
    if(r<0||!g_s26sEyeAction){ext_Log(">>> S26DG eye gaze action creation failed (%d)",r);return;}
    XrActionSuggestedBinding b={g_s26sEyeAction,path};
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;sb.countSuggestedBindings=1;sb.suggestedBindings=&b;
    r=pSuggestBindings(inst,&sb);
    if(r<0){ext_Log(">>> S26DG eye gaze binding rejected (%d)",r);g_s26sEyeAction=0;return;}
    g_s26sEyeSession=sess;s26q_hook_destroy(self);
    ext_Log(">>> S26DG eye gaze binding accepted; awaiting action-set attachment");
}
/* Create spaces after the shared sets attach, matching the standard gaze
   lifecycle. Head and gaze are located in one base space at one timestamp. */
static void s26s_eye_spaces(void* self,Handle inst,Handle sess){
    if(!g_s26sEyeAction||sess!=g_s26sEyeSession)return;
    XrActionSpaceCreateInfo ci;zero_bytes(&ci,sizeof(ci));ci.type=XR_TYPE_ACTION_SPACE_CREATE_INFO;ci.action=g_s26sEyeAction;ci.poseInActionSpace.orientation.w=1;
    i32 r=pCreateActionSpace(sess,&ci,&g_s26sEyeSpace);
    if(r<0||!g_s26sEyeSpace){ext_Log(">>> S26DG eye gaze action space failed (%d)",r);g_s26sEyeSpace=0;return;}
    PFN_GIPA get=*(PFN_GIPA*)((u8*)self+0x1c8);S26DGEyeCreateRef create=0;
    if(!get||get(inst,"xrCreateReferenceSpace",(void**)&create)<0||!create){ext_Log(">>> S26DG eye VIEW entry point unavailable");return;}
    S26DGEyeRefInfo view;zero_bytes(&view,sizeof(view));view.type=37;view.referenceSpaceType=1;view.poseInReferenceSpace.orientation.w=1;
    r=create(sess,&view,&g_s26dgEyeView);
    if(r<0||!g_s26dgEyeView){g_s26dgEyeView=0;ext_Log(">>> S26DG eye VIEW space failed (%d)",r);return;}
    ext_Log(">>> S26DG eye gaze spaces ready; waiting for active, tracked input (runtime permission/calibration may be required)");
}
static i32 s26s_pose_finite(const XrPosef* p){
    const float* q=&p->orientation.x;float n=0;
    for(i32 i=0;i<4;++i){if(!(q[i]>=-1.01f&&q[i]<=1.01f))return 0;n+=q[i]*q[i];}
    const float* x=&p->position.x;
    for(i32 i=0;i<3;++i)if(!(x[i]>-1000&&x[i]<1000))return 0;
    return n>.98f&&n<1.02f;
}
static void s26s_eye_tick(Handle sess,Handle baseSpace,i64 time,i32 sync){
    XrSpaceLocation loc;zero_bytes(&loc,sizeof(loc));loc.type=XR_TYPE_SPACE_LOCATION;
    XrSpaceLocation head;zero_bytes(&head,sizeof(head));head.type=XR_TYPE_SPACE_LOCATION;
    S26SEyeSampleTime sample={1000030001,0,0};loc.next=&sample;
    i32 valid=0,headValid=0,reason=1,stateResult=0,locResult=0;
    if(g_s26sEyeAction&&g_s26sEyeSpace&&g_s26dgEyeView&&sess==g_s26sEyeSession&&baseSpace&&time>0&&sync==0){
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;gi.action=g_s26sEyeAction;
        XrActionStatePose state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_ACTION_STATE_POSE;
        stateResult=pGetActionStatePose(sess,&gi,&state);reason=2;
        if(stateResult==0&&state.isActive){
            locResult=pLocateSpace(g_s26sEyeSpace,baseSpace,time,&loc);reason=3;
            if(locResult==0&&(loc.locationFlags&15u)==15u&&s26s_pose_finite(&loc.pose)){
                reason=4;
                if(!sample.time||(sample.time>=time-100000000LL&&sample.time<=time+100000000LL)){
                    /* Eye tracking can be unpredicted. Match VIEW to the returned
                       gaze sample time instead of mixing it with a later camera. */
                    i64 headTime=sample.time?sample.time:time;
                    headValid=pLocateSpace(g_s26dgEyeView,baseSpace,headTime,&head)==0&&
                        (head.locationFlags&3u)==3u&&s26s_pose_finite(&head.pose);
                    reason=headValid?0:5;valid=headValid;
                }
            }
        }
    }
    if(s26s_eye_lock()){g_s26sEyeSample.valid=(u8)valid;g_s26sEyeSample.headValid=(u8)headValid;g_s26sEyeSample.head=head.pose;g_s26sEyeSample.eye=loc.pose;g_s26sEyeSample.time=sample.time?sample.time:time;s26s_eye_unlock();}
    if(g_s26sEyeReported!=(u8)reason&&g_s26sEyeLogs<24u){++g_s26sEyeLogs;ext_Log(">>> S26DG eye gaze %s: reason %d (0=active 1=setup/focus 2=inactive/action 3=tracking/pose 4=stale 5=head-space), state %d locate %d flags %u; no gaze coordinates logged",valid?"active":"unavailable",reason,stateResult,locResult,(u32)loc.locationFlags);}
    g_s26sEyeReported=(u8)reason;
}
static void s26s_quat_rotate(const XrQuaternionf* q,const float in[3],float out[3]){
    float tx=2*(q->y*in[2]-q->z*in[1]),ty=2*(q->z*in[0]-q->x*in[2]),tz=2*(q->x*in[1]-q->y*in[0]);
    out[0]=in[0]+q->w*tx+q->y*tz-q->z*ty;out[1]=in[1]+q->w*ty+q->z*tx-q->x*tz;out[2]=in[2]+q->w*tz+q->x*ty-q->y*tx;
}
