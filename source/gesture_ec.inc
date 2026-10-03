/* S26EC: HANDS AND HAPTICS settings and finger gestures for capacitive
   skeletal controllers (Valve Index, Steam Frame). Every gesture needs valid
   skeletal fingers on such a controller; other controllers keep the existing
   grip/trigger behaviour exactly. Settings arrive through VRCOMFORT classes
   U (smart grip), Z (grip pressure), P (point to press), K (any-finger
   keypads), X (creature haptics) and I (button hints). */
#define S26EC_SET_SMART_GRIP 1u
#define S26EC_SET_PRESSURE   2u
#define S26EC_SET_POINT      4u
#define S26EC_SET_ANY_FINGER 8u
#define S26EC_SET_CREATURE   16u
#define S26EC_SET_HINTS      32u
/* S26ED options share this word: VRCOMFORT H (head tap flashlight), L (ladder
   hands), Q (depth for reprojection), Y (texture budget boost). */
#define S26EC_SET_HEAD_TAP   64u
#define S26EC_SET_LADDER     128u
#define S26EC_SET_DEPTH      256u
#define S26EC_SET_TEXTURE    512u
static u32 g_s26ecSettings=S26EC_SET_SMART_GRIP|S26EC_SET_PRESSURE|S26EC_SET_POINT|S26EC_SET_CREATURE|S26EC_SET_HINTS|S26EC_SET_HEAD_TAP|S26EC_SET_LADDER;
static void s26ec_set_option(u32 bit,u32 enabled){
    if(enabled)__atomic_fetch_or(&g_s26ecSettings,bit,__ATOMIC_ACQ_REL);
    else __atomic_fetch_and(&g_s26ecSettings,~bit,__ATOMIC_ACQ_REL);
}
static i32 s26ec_option(u32 bit){return (__atomic_load_n(&g_s26ecSettings,__ATOMIC_ACQUIRE)&bit)!=0;}

/* Normalised curls 0 open .. 1 closed, from the same packets that animate the
   hand. The thumb's authored range ends at 0.55, so it is rescaled to 0..1. */
typedef struct {float thumb,index,middle,ring,little;} S26ECFingers;
static i32 s26ec_fingers(i32 hand,S26ECFingers* out){
    if(hand<0||hand>1||!out||!g_s26diFrameHand[hand])return 0;
    float v[5];
    for(i32 f=0;f<5;++f){
        float cv[4];if(!s26q_finger_values(hand,f,cv))return 0;
        v[f]=f==0?clamp01((cv[1]+cv[2])*0.5f/0.55f):clamp01((cv[1]+cv[2]+cv[3])/3.0f);
    }
    out->thumb=v[0];out->index=v[1];out->middle=v[2];out->ring=v[3];out->little=v[4];return 1;
}
static float s26ec_lower_three(const S26ECFingers* f){return (f->middle+f->ring+f->little)/3.0f;}

/* Point gesture: index extended, middle/ring/little curled. The index limit
   is the long-standing poke curl gate, so a point is always a valid poke. */
#define S26EC_POINT_INDEX_MAX 0.40f
#define S26EC_POINT_OTHERS_MIN 0.45f
static i32 s26ec_is_point(const S26ECFingers* f){
    return f->index<=S26EC_POINT_INDEX_MAX&&s26ec_lower_three(f)>=S26EC_POINT_OTHERS_MIN;
}
static float s26ec_finger_curl(const S26ECFingers* f,i32 finger){
    return finger==0?f->thumb:finger==1?f->index:finger==2?f->middle:finger==3?f->ring:f->little;
}
/* Which fingers may press a control this step, as a bit mask over fingers
   1..4 (index..little).
   - Without skeletal fingers: index only, behind the existing curl gate.
   - ANY FINGER ON KEYPADS: every extended finger (point not required).
   - POINT TO PRESS: index only, and a new press needs a point. A contact
     already engaged (terminal finger down / rocker latched) only needs the
     finger to stay extended, so relaxing the others never lifts mid-drag.
   - Neither option: index behind the existing curl gate. */
static u32 s26ec_poke_mask(i32 hand,i32 engaged){
    if(hand<0||hand>1)return 0;
    S26ECFingers f;
    if(!s26ec_fingers(hand,&f))return h10_raw_finger_input(hand,1)<=S26EC_POINT_INDEX_MAX?2u:0u;
    if(s26ec_option(S26EC_SET_ANY_FINGER)){
        u32 mask=0;for(i32 k=1;k<=4;++k)if(s26ec_finger_curl(&f,k)<=S26EC_POINT_INDEX_MAX)mask|=1u<<k;return mask;
    }
    if(f.index>S26EC_POINT_INDEX_MAX)return 0;
    if(s26ec_option(S26EC_SET_POINT)&&!engaged&&!s26ec_is_point(&f))return 0;
    return 2u;
}
/* Fingertip skin radius slot used by h572_index_skin_radius: the finger that
   is currently probing a control. Always restored to the index afterwards. */
static i32 g_s26ecPokeFinger[2]={1,1};
static i32 g_s26ecTerminalFinger[2]={1,1},g_s26ecSwitchFinger[2]={1,1};

/* Smart grip state, written by the XR input thread (grip_ec.inc) and read by
   physics/latch code. */
#define S26EC_GRIP_HISTORY 12
typedef struct {i64 t[S26EC_GRIP_HISTORY];float g[S26EC_GRIP_HISTORY];u32 head,count;u8 pinch,openLatch;float openMin;} S26ECGrip;
static S26ECGrip g_s26ecGrip[2];
static volatile u32 g_s26ecPinch[2];
/* Set by the semantic haptic flush; the creature channel yields to it. */
static volatile u32 g_s26ecSemanticFired[2];
