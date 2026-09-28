/* Optional OpenXR gaze; no desktop tracker emulation and no synthetic blinks. */
static Handle g_s26sEyeAction,g_s26sEyeSpace,g_s26sEyeSession;
typedef struct {i32 type;void* next;i64 time;} S26SEyeSampleTime;
typedef struct {XrPosef eye,head;i64 time;u8 valid,headValid;} S26SEyeSample;
static S26SEyeSample g_s26sEyeSample;
static u32 g_s26sEyeLock,g_s26sEyeLogs;
static u8 g_s26sEyeReported;
static i32 s26s_eye_lock(void){u32 expected=0;return __atomic_compare_exchange_n(&g_s26sEyeLock,&expected,1u,0,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED);}
static void s26s_eye_unlock(void){__atomic_store_n(&g_s26sEyeLock,0u,__ATOMIC_RELEASE);}
static void s26s_eye_end(Handle session){
    if(session!=g_s26sEyeSession)return;
    g_s26sEyeAction=0;g_s26sEyeSpace=0;g_s26sEyeSession=0;
    if(s26s_eye_lock()){g_s26sEyeSample.valid=0;g_s26sEyeSample.headValid=0;s26s_eye_unlock();}
    g_s26sEyeReported=0;
}
static void s26s_eye_binding(void* self,Handle inst,Handle sess){
    if(!g_s26sEyeExtension||!self||!inst||!sess)return;
    XrPath profile=0,path=0;
    if(pStringToPath(inst,"/interaction_profiles/ext/eye_gaze_interaction",&profile)<0||
       pStringToPath(inst,"/user/eyes_ext/input/gaze_ext/pose",&path)<0)return;
    if(create_action("eye_gaze_s1","Eye Gaze",XR_ACTION_TYPE_POSE_INPUT,&g_s26sEyeAction)<0||!g_s26sEyeAction)return;
    XrActionSuggestedBinding b={g_s26sEyeAction,path};
    XrInteractionProfileSuggestedBinding sb;zero_bytes(&sb,sizeof(sb));sb.type=XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING;sb.interactionProfile=profile;sb.countSuggestedBindings=1;sb.suggestedBindings=&b;
    if(pSuggestBindings(inst,&sb)<0){g_s26sEyeAction=0;return;}
    XrActionSpaceCreateInfo ci;zero_bytes(&ci,sizeof(ci));ci.type=XR_TYPE_ACTION_SPACE_CREATE_INFO;ci.action=g_s26sEyeAction;ci.poseInActionSpace.orientation.w=1;
    if(pCreateActionSpace(sess,&ci,&g_s26sEyeSpace)<0||!g_s26sEyeSpace){g_s26sEyeSpace=0;g_s26sEyeAction=0;return;}
    g_s26sEyeSession=sess;s26q_hook_destroy(self);
}
static i32 s26s_pose_finite(const XrPosef* p){
    const float* q=&p->orientation.x;float n=0;
    for(i32 i=0;i<4;++i){if(!(q[i]>=-1.01f&&q[i]<=1.01f))return 0;n+=q[i]*q[i];}
    const float* x=&p->position.x;
    for(i32 i=0;i<3;++i)if(!(x[i]>-1000&&x[i]<1000))return 0;
    return n>.98f&&n<1.02f;
}
static void s26s_head_sample(const float* q,const float* p,i32 valid){
    if(!s26s_eye_lock())return;
    g_s26sEyeSample.headValid=0;
    if(valid&&q&&p){
        for(i32 i=0;i<4;++i)(&g_s26sEyeSample.head.orientation.x)[i]=q[i];
        for(i32 i=0;i<3;++i)(&g_s26sEyeSample.head.position.x)[i]=p[i];
        g_s26sEyeSample.headValid=(u8)s26s_pose_finite(&g_s26sEyeSample.head);
    }
    s26s_eye_unlock();
}
static void s26s_eye_tick(Handle sess,Handle baseSpace,i64 time,i32 sync){
    XrSpaceLocation loc;zero_bytes(&loc,sizeof(loc));loc.type=XR_TYPE_SPACE_LOCATION;
    S26SEyeSampleTime sample={1000030001,0,0};loc.next=&sample;
    i32 valid=0;
    if(g_s26sEyeAction&&g_s26sEyeSpace&&sess==g_s26sEyeSession&&baseSpace&&time>0&&sync==0){
        XrActionStateGetInfo gi;zero_bytes(&gi,sizeof(gi));gi.type=XR_TYPE_ACTION_STATE_GET_INFO;gi.action=g_s26sEyeAction;
        XrActionStatePose state;zero_bytes(&state,sizeof(state));state.type=XR_TYPE_ACTION_STATE_POSE;
        if(pGetActionStatePose(sess,&gi,&state)==0&&state.isActive&&pLocateSpace(g_s26sEyeSpace,baseSpace,time,&loc)==0&&
           (loc.locationFlags&15u)==15u&&s26s_pose_finite(&loc.pose)&&
           (!sample.time||(sample.time>=time-100000000LL&&sample.time<=time+100000000LL)))valid=1;
    }
    if(s26s_eye_lock()){g_s26sEyeSample.valid=(u8)valid;g_s26sEyeSample.eye=loc.pose;g_s26sEyeSample.time=time;s26s_eye_unlock();}
    if(g_s26sEyeReported!=(u8)valid&&g_s26sEyeLogs<16u){++g_s26sEyeLogs;ext_Log(">>> S26S eye gaze %s; no gaze coordinates logged, blink signal unavailable",valid?"active":"unavailable");}
    g_s26sEyeReported=(u8)valid;
}
static void s26s_quat_rotate(const XrQuaternionf* q,const float in[3],float out[3]){
    float tx=2*(q->y*in[2]-q->z*in[1]),ty=2*(q->z*in[0]-q->x*in[2]),tz=2*(q->x*in[1]-q->y*in[0]);
    out[0]=in[0]+q->w*tx+q->y*tz-q->z*ty;out[1]=in[1]+q->w*ty+q->z*tx-q->x*tz;out[2]=in[2]+q->w*tz+q->x*ty-q->y*tx;
}
