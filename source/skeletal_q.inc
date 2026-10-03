/* XR_EXT_hand_tracking joint flexion, retargeted to the authored Simon rigs.
   Gameplay grip/trigger actions remain separate from skeletal pose input. */
typedef struct {i32 type;const void* next;i32 hand,jointSet;} S26QHandCreate;
typedef struct {i32 type;const void* next;Handle baseSpace;i64 time;} S26QHandLocate;
typedef struct {u64 flags;XrPosef pose;float radius;} S26QJoint;
typedef struct {i32 type;void* next;u32 active,count;S26QJoint* joints;} S26QJoints;
_Static_assert(sizeof(S26QHandCreate)==24,"hand create ABI");
_Static_assert(sizeof(S26QHandLocate)==32,"hand locate ABI");
_Static_assert(sizeof(S26QJoint)==40,"hand joint ABI");
_Static_assert(sizeof(S26QJoints)==32,"hand locations ABI");
typedef i32 (__attribute__((ms_abi)) *S26QCreateHand)(Handle,const S26QHandCreate*,Handle*);
typedef i32 (__attribute__((ms_abi)) *S26QLocateHand)(Handle,const S26QHandLocate*,S26QJoints*);
typedef i32 (__attribute__((ms_abi)) *S26QDestroyHand)(Handle);
static S26QCreateHand p_s26qCreateHand;
static S26QLocateHand p_s26qLocateHand;
static S26QDestroyHand p_s26qDestroyHand;
static u8 g_s26qHandExtension;
static u8 g_s26dnMotionRangeEnabled;
#include "motion_range_dn.inc"
static Handle g_s26qHandSession,g_s26qHandTracker[2];
static u64 g_s26qFingerInput[2][5]; /* four 12-bit curls plus validity bit */
static u64 g_s26qHeldFingerInput[2][5],g_s26qIdleFingerInput[2][5];
static u8 g_s26qHandReported[2];
static u32 g_s26qHandLogs;
#include "frame_rest_dz.inc"
#include "finger_reset_ea.inc"
static void s26q_hook_destroy(void* self);
static void s26q_clear_root_input(void);
static void s26q_clear_finger_input(void){
    s26q_clear_root_input();
    for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f)__atomic_store_n(&g_s26qFingerInput[h][f],0ULL,__ATOMIC_RELEASE);
}
static void s26q_hands_end(Handle session){
    if(session!=g_s26qHandSession)return;
    s26q_clear_finger_input();
    for(i32 h=0;h<2;++h){if(g_s26qHandTracker[h]&&p_s26qDestroyHand)p_s26qDestroyHand(g_s26qHandTracker[h]);g_s26qHandTracker[h]=0;g_s26qHandReported[h]=0;}
    g_s26qHandSession=0;
}
static void s26q_hands_setup(void* self){
    if(!self||!g_s26qHandExtension)return;
    Handle inst=*(Handle*)((u8*)self+0x10),session=*(Handle*)((u8*)self+0x20);
    PFN_GIPA get=*(PFN_GIPA*)((u8*)self+0x1c8);
    if(!inst||!session||!get||g_s26qHandSession==session)return;
    if(g_s26qHandSession)return; /* no reuse across an unobserved session teardown */
    if(get(inst,"xrCreateHandTrackerEXT",(void**)&p_s26qCreateHand)<0||!p_s26qCreateHand||
       get(inst,"xrLocateHandJointsEXT",(void**)&p_s26qLocateHand)<0||!p_s26qLocateHand||
       get(inst,"xrDestroyHandTrackerEXT",(void**)&p_s26qDestroyHand)<0||!p_s26qDestroyHand)return;
    s26dz_rest_reset(0);s26dz_rest_reset(1);
    g_s26eaResetState=0;g_s26eaResetRequest=0;
    s26q_clear_finger_input();g_s26qHandSession=session;s26q_hook_destroy(self);
    for(i32 h=0;h<2;++h){
        S26QHandCreate ci;zero_bytes(&ci,sizeof(ci));ci.type=1000051001;ci.hand=h+1;
        i32 r=p_s26qCreateHand(session,&ci,&g_s26qHandTracker[h]);
        if(r<0)g_s26qHandTracker[h]=0;
        if(g_s26qHandLogs++<24u)ext_Log(">>> S26Q skeletal hand %d tracker %s (%d); grip/trigger actions unchanged",h,g_s26qHandTracker[h]?"ready":"unavailable",r);
    }
}
static i32 s26q_joint_position(const S26QJoint* j,float* out){
    if((j->flags&2u)==0u)return 0;
    out[0]=j->pose.position.x;out[1]=j->pose.position.y;out[2]=j->pose.position.z;
    for(i32 k=0;k<3;++k)if(!(out[k]>-1000.0f&&out[k]<1000.0f))return 0;
    return 1;
}
#include "root_input_q.inc"
static i32 s26q_joint_bend(const S26QJoint* joints,i32 a,i32 b,i32 c,float* angle){
    float pa[3],pb[3],pc[3];
    if(!s26q_joint_position(joints+a,pa)||!s26q_joint_position(joints+b,pb)||!s26q_joint_position(joints+c,pc))return 0;
    float u[3],v[3],nu=0.0f,nv=0.0f,dot=0.0f;
    for(i32 k=0;k<3;++k){u[k]=pb[k]-pa[k];v[k]=pc[k]-pb[k];nu+=u[k]*u[k];nv+=v[k]*v[k];dot+=u[k]*v[k];}
    if(!(nu>0.000001f&&nu<0.04f&&nv>0.000001f&&nv<0.04f))return 0;
    float cos=dot/ext_Sqrtf(nu*nv);if(cos>1.0f)cos=1.0f;if(cos<-1.0f)cos=-1.0f;
    float sin=ext_Sqrtf(1.0f-cos*cos);
    if(!h5755bl_resolve_atan2f())return 0;
    *angle=p_h5755blAtan2f(sin,cos);return *angle>=0.0f&&*angle<3.15f;
}
static u64 s26q_pack_finger(const float curl[4]){
    u64 out=1ULL<<63;
    for(i32 d=0;d<4;++d){float v=curl[d];if(!(v>=0.0f&&v<=1.0f))return 0;out|=(u64)(u32)(v*4095.0f+0.5f)<<(d*12);}
    return out;
}
static i32 s26q_retarget_finger(const S26QJoint* joints,i32 finger,float curl[4]){
    if(finger<0||finger>4)return 0;
    for(i32 d=0;d<4;++d)curl[d]=0.0f;
    if(finger==0){
        float a,b;if(!s26q_joint_bend(joints,2,3,4,&a)||!s26q_joint_bend(joints,3,4,5,&b))return 0;
        /* Thumb opposition has a different rest pose on each suit. Preserve the
           authored opposition arc; drive it using the measured thumb flexion. */
        curl[1]=clamp01(a/1.22f);curl[2]=clamp01(b/1.22f);curl[0]=0.55f*(curl[1]+curl[2])*0.5f;curl[3]=curl[2];
    }else{
        i32 start=6+(finger-1)*5;
        const float range[3]={0.872664626f,1.256637061f,0.802851456f};
        for(i32 d=1;d<4;++d){float angle;if(!s26q_joint_bend(joints,start+d-1,start+d,start+d+1,&angle))return 0;curl[d]=clamp01(angle/range[d-1]);}
        /* Metacarpal root stays authored; it is not another knuckle. */
        curl[0]=0.0f;
    }
    return 1;
}
#include "frame_curl_di.inc"

static void s26q_hands_tick(Handle session,Handle space,i64 time,i32 focused){
    if(session!=g_s26qHandSession||!space||time<=0||!focused){s26q_clear_finger_input();if(g_s26eaResetState==1||g_s26eaResetState==2)g_s26eaResetState=4;return;}
    float resetRaw[2][5]={{0}};u8 resetValid[2]={1,1};
    for(i32 h=0;h<2;++h){
        S26QJoint joints[26];zero_bytes(joints,sizeof(joints));
        S26QJoints out;zero_bytes(&out,sizeof(out));out.type=1000051003;out.count=26;out.joints=joints;
        S26QHandLocate li;zero_bytes(&li,sizeof(li));li.type=1000051002;li.baseSpace=space;li.time=time;
        u8 allowed=s26u_controller_fingers_allowed(session,h);
        S26DNMotionRange range;s26dn_motion_range(&li,&range,g_s26dnMotionRangeEnabled&&g_s26diFrameHand[h]);
        u8 valid=allowed&&g_s26qHandTracker[h]&&p_s26qLocateHand&&p_s26qLocateHand(g_s26qHandTracker[h],&li,&out)==0&&out.active&&out.count==26;
        u8 any=0;
        /* Missing profile/tracking data must not erase a confirmed reference. */
        if(g_s26ebProfileChanged[h]){s26dz_rest_reset(h);g_s26ebProfileChanged[h]=0;if(g_s26eaResetState==1||g_s26eaResetState==2)g_s26eaResetState=4;}
        for(i32 f=0;f<5;++f){float cv[4];
            i32 mapped=valid&&s26di_frame_curl(joints,h,f,cv);
            if(mapped)resetRaw[h][f]=cv[0]/(f==0?0.55f:1.0f);else resetValid[h]=0;
            if(mapped)s26dz_rest_correct(h,f,time,cv);
            u64 packed=mapped?s26q_pack_finger(cv):0;
            // A learned resting reference does not replace runtime motion.
            // Unknown/invalid skeletal samples retain the existing fallback.
            __atomic_store_n(&g_s26qFingerInput[h][f],packed,__ATOMIC_RELEASE);
            __atomic_store_n(&g_s26qRootInput[h][f],0ULL,__ATOMIC_RELEASE);if(packed)any=1;}
        if(any!=g_s26qHandReported[h]&&g_s26qHandLogs<24u){++g_s26qHandLogs;ext_Log(">>> S26Q skeletal hand %d input %s",h,any?"active":"unavailable; controller curl fallback");}
        g_s26qHandReported[h]=any;

    }
    s26ea_finger_reset_tick(time,focused,resetRaw,resetValid);
}
static i32 s26q_finger_values(i32 hand,i32 finger,float out[4]){
    if(hand<0||hand>1||finger<0||finger>4)return 0;
    u64 packed=__atomic_load_n(&g_s26qFingerInput[hand][finger],__ATOMIC_ACQUIRE);
    if(!(packed&(1ULL<<63)))return 0;
    for(i32 d=0;d<4;++d)out[d]=(float)((packed>>(12*d))&4095u)/4095.0f;
    return 1;
}
static i32 s26q_finger_changed(u64 a,u64 b){
    if((a^b)&(1ULL<<63))return 1;
    if(!(a&(1ULL<<63)))return 0;
    for(i32 d=0;d<4;++d){i32 delta=(i32)((a>>(12*d))&4095u)-(i32)((b>>(12*d))&4095u);if(delta>12||delta<-12)return 1;}
    return 0;
}
static i32 s26q_hand_input_changed(i32 hand,const u64 previous[5]){
    for(i32 f=0;f<5;++f)if(s26q_finger_changed(__atomic_load_n(&g_s26qFingerInput[hand][f],__ATOMIC_ACQUIRE),previous[f]))return 1;
    return 0;
}
static void s26q_save_hand_input(i32 hand,u64 previous[5]){
    for(i32 f=0;f<5;++f)previous[f]=__atomic_load_n(&g_s26qFingerInput[hand][f],__ATOMIC_ACQUIRE);
}

