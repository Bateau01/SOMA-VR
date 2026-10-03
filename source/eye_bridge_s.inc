static volatile u32 g_s26sEyeOptions=3u; /* environment, AI, flashlight, extra distortion */
static i32 s26s_vr_active(void){return g_h576mScriptRuntimePublished==1&&p2_xr_on()&&p2_xr_running();}
/* View frame is shared with the visible VR camera, including authored scenes.
   No eye-FOV, desktop-window, supersampling or projection-size assumption. */
static i32 s26s_view_frame(float p[3],float R[9]){
    if(!s26s_vr_active()||g_h576bfMapTransitionActive||!g_s26nHeadHeightFresh||(u32)(g_frameCounter-g_s26nHeadValidFrame)>2u)return 0;
    u8* F=(u8*)__atomic_load_n(p2_main_frustum_ptr(),__ATOMIC_ACQUIRE);
    if(!F||!h20_mem_readable(F+0x158,64))return 0;
    float V[16];h10_copy_f(V,(float*)(F+0x158),16);
    for(i32 i=0;i<16;++i)if(!(V[i]>-1000000&&V[i]<1000000))return 0;
    for(i32 row=0;row<3;++row){float norm=0;for(i32 k=0;k<3;++k)norm+=V[row*4+k]*V[row*4+k];if(norm<.98f||norm>1.02f)return 0;}
    for(i32 row=0;row<3;++row)for(i32 other=row+1;other<3;++other){float dot=0;for(i32 k=0;k<3;++k)dot+=V[row*4+k]*V[other*4+k];if(dot<-.02f||dot>.02f)return 0;}
    for(i32 k=0;k<3;++k){p[k]=-(V[k]*V[3]+V[4+k]*V[7]+V[8+k]*V[11]);for(i32 j=0;j<3;++j)R[k*3+j]=V[j*4+k];}
    return 1;
}
static void s26s_rotate3(const float R[9],const float v[3],float out[3]){for(i32 k=0;k<3;++k)out[k]=R[3*k]*v[0]+R[3*k+1]*v[1]+R[3*k+2]*v[2];}
static float g_s26sReadOrigin[3],g_s26sReadDirection[3],g_s26sReadLocal[3];
static i32 g_s26sReadValid;
static u32 g_s26dgEyeBridgeSeen;
static i32 s26dg_eye_bridge_status(u32 reason){
    u32 bit=1u<<reason;
    if(!(g_s26dgEyeBridgeSeen&bit)){
        g_s26dgEyeBridgeSeen|=bit;
        ext_Log(">>> S26DG eye gameplay bridge status %u (0=ready 1=camera/frame unavailable 2=no fresh tracked sample 3=eye/head origin mismatch 4=script-vector signature mismatch)",reason);
    }
    return reason==0;
}
static i32 s26s_read_gaze(void){
    g_s26sReadValid=0;float cp[3],R[9];if(!s26s_view_frame(cp,R))return s26dg_eye_bridge_status(1);if(!s26s_eye_lock())return 0;
    S26SEyeSample sample=g_s26sEyeSample;s26s_eye_unlock();
    u8* xr=(u8*)p2_xr_obj();i64 now=xr?*(i64*)(xr+0xE8):0;
    if(!sample.valid||!sample.headValid||now<=0||sample.time>now+100000000LL||sample.time<now-100000000LL)return s26dg_eye_bridge_status(2);
    XrQuaternionf inv={-sample.head.orientation.x,-sample.head.orientation.y,-sample.head.orientation.z,sample.head.orientation.w};
    float f[3]={0,0,-1},raw[3],local[3],offset[3],offlocal[3],offworld[3];
    s26s_quat_rotate(&sample.eye.orientation,f,raw);s26s_quat_rotate(&inv,raw,local);
    for(i32 k=0;k<3;++k)offset[k]=(&sample.eye.position.x)[k]-(&sample.head.position.x)[k];
    if(h10_len3(offset[0],offset[1],offset[2])>.20f)return s26dg_eye_bridge_status(3);
    s26s_quat_rotate(&inv,offset,offlocal);s26s_rotate3(R,offlocal,offworld);
    for(i32 k=0;k<3;++k){g_s26sReadOrigin[k]=cp[k]+offworld[k]*h5755ea_world_units_per_meter();g_s26sReadLocal[k]=local[k];}
    s26s_rotate3(R,local,g_s26sReadDirection);g_s26sReadValid=1;return s26dg_eye_bridge_status(0);
}
typedef void (__attribute__((ms_abi)) *S26SSetVector)(const float*);
static S26SSetVector p_s26sSetVector;
static i32 s26s_set_vector(const float value[3]){
    if(!p_s26sSetVector){
        u8* base=(u8*)ext_GetModuleHandleA(0);if(!base||!h20_mem_readable(base+0x48ed40,12))return 0;
        static const u8 expected[12]=S26S_VECTOR_SIGNATURE;
        for(i32 k=0;k<12;++k)if(base[0x48ed40+k]!=expected[k])return s26dg_eye_bridge_status(4);
        p_s26sSetVector=(S26SSetVector)(void*)(base+0x48ed40);
    }
    p_s26sSetVector(value);return 1;
}
static u64 s26s_eye_token(const H5730TString* cls,const H5730TString* fn){
    if(h5748t_sso_eq(fn,"VR",2u))return s26s_vr_active();
    if(h5748t_sso_eq(fn,"AVAILABLE",9u))return g_s26sEyeSpace!=0&&g_s26dgEyeView!=0;
    if(h5748t_sso_eq(fn,"BLINK",5u))return 0; /* No valid blink provider; never infer from loss. */
    if(h5748t_sso_eq(fn,"ACTIVE",6u))return s26s_read_gaze();
    if(h5748t_sso_eq(fn,"ENV",3u))return (g_s26sEyeOptions&1u)!=0;
    if(h5748t_sso_eq(fn,"AI",2u))return (g_s26sEyeOptions&2u)!=0;
    if(h5748t_sso_eq(fn,"FLASH",5u))return (g_s26sEyeOptions&4u)!=0;
    if(h5748t_sso_eq(fn,"DISTORT",7u))return (g_s26sEyeOptions&8u)!=0;
    if(h5748t_sso_eq(fn,"ORIGIN",6u))return s26s_read_gaze()&&s26s_set_vector(g_s26sReadOrigin);
    if(h5748t_sso_eq(fn,"DIRECTION",9u))return g_s26sReadValid&&s26s_set_vector(g_s26sReadDirection);
    if(h5748t_sso_eq(fn,"LOCAL",5u))return g_s26sReadValid&&s26s_set_vector(g_s26sReadLocal);
    if(cls&&cls->size==1u&&cls->capacity<=15u&&fn&&fn->size==1u&&fn->capacity<=15u){
        u32 bit=cls->storage[0]-'0';if(bit<4u&&(fn->storage[0]=='0'||fn->storage[0]=='1')){
            u32 mask=1u<<bit;if(fn->storage[0]=='1')__atomic_fetch_or(&g_s26sEyeOptions,mask,__ATOMIC_RELAXED);else __atomic_fetch_and(&g_s26sEyeOptions,~mask,__ATOMIC_RELAXED);return 1;
        }
    }
    return 0;
}
