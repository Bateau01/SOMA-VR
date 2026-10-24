/* A separate comfort anchor for hints: no subtitle or gameplay camera state.
   Rigid row-major view in world units; position follows locomotion, orientation
   changes atomically past 30 degrees yaw / 20 degrees pitch. */
typedef struct {float rotation[16],yaw,pitch;u32 epoch,frame;i32 valid;} S26HSHintAnchor;
static S26HSHintAnchor g_s26hsHintAnchor;
static i32 s26hs_hint_view(S26HSHintAnchor* a,const float* v,float* out,u32 frame,u32 epoch){
    if(!a||!v||!out||!h5755bl_resolve_atan2f())return 0;
    for(i32 i=0;i<16;i++)if(!h9_good(v[i],100000.0f))return 0;
    float horizontal=ext_Sqrtf(v[8]*v[8]+v[10]*v[10]);if(horizontal<.0001f)return 0;
    float yaw=p_h5755blAtan2f(-v[8],v[10]);
    float pitch=p_h5755blAtan2f(-v[9],horizontal);
    if(!a->valid||a->epoch!=epoch||(u32)(frame-a->frame)>2u||
       h9_abs(h5755eb_wrap_pi(yaw-a->yaw))>.523598776f||h9_abs(pitch-a->pitch)>.34906585f){
        h10_copy_f(a->rotation,v,16);a->yaw=yaw;a->pitch=pitch;a->valid=1;a->epoch=epoch;
    }
    a->frame=frame;float pos[3];
    for(i32 i=0;i<3;i++)pos[i]=-(v[i]*v[3]+v[4+i]*v[7]+v[8+i]*v[11]);
    h10_copy_f(out,a->rotation,16);
    for(i32 i=0;i<3;i++)out[i*4+3]=-(out[i*4]*pos[0]+out[i*4+1]*pos[1]+out[i*4+2]*pos[2]);
    return 1;
}
