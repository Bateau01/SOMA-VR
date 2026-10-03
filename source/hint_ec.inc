/* S26EC: BUTTON HINTS. Resting the thumb on an Index A or B button (capacitive
   touch) for a moment shows that button's current role, after any remap, on a
   small label floating above the wrist. Pressing the button fades the label
   until the thumb lifts. The label is a dedicated cGui 3D set ("VR_WristHint")
   that follows the hardware-proven VR_Subtitles route: its early native draw
   caches the per-eye state and it is replayed with the subtitles at the
   GameHud stage, depth test off. Its own 512x128 virtual area has no HUD
   offset; text is drawn at its centre, which HPL places on the set origin. */
#define S26EC_HINT_REST_NS 300000000LL
#define S26EC_HINT_FADE_IN_S 0.15f
#define S26EC_HINT_FADE_OUT_S 0.08f
#define S26EC_WRIST_VIRTUAL_W 512.0f
#define S26EC_WRIST_VIRTUAL_H 128.0f
#define S26EC_WRIST_WIDTH_M 0.24f
#define S26EC_WRIST_LIFT_M 0.09f
typedef struct {i32 source,shown;i64 since;u8 suppressed;float alpha;} S26ECHintHand;
static S26ECHintHand g_s26ecHint[2]={{-1,-1,0,0,0.0f},{-1,-1,0,0,0.0f}};
static i64 g_s26ecHintLast;
/* bit31 valid | hand<<24 | source<<16 | (role+1)<<8 | alpha*255 */
static volatile u32 g_s26ecHintPacked;
static i32 s26ec_hint_role(i32 source){
    for(u32 r=0;r<6u;++r)if((i32)s26n_binding_source(r)==source)return (i32)r;
    return -1;
}
/* Pure per-hand step (tests): source is the touched button's binding source
   or -1, pressed its raw press state. */
static void s26ec_hint_step(S26ECHintHand* H,i32 source,i32 pressed,i64 now,float dt){
    if(source!=H->source){H->source=source;H->since=now;H->suppressed=0;}
    if(source>=0&&pressed)H->suppressed=1;
    i32 want=source>=0&&!H->suppressed&&now-H->since>=S26EC_HINT_REST_NS;
    if(want)H->shown=source;
    H->alpha=clamp01(H->alpha+(want?dt/S26EC_HINT_FADE_IN_S:-dt/S26EC_HINT_FADE_OUT_S));
}
/* Index thumb-rest buttons map onto the established binding sources:
   right A=0 (jump), right B=1 (run/back), left A=2 (pause), left B=3 (center). */
static i32 s26ec_hint_source(i32 hand){
    u8 a=g_s26ecFaceTouchValid[hand][0]&&g_s26ecFaceTouch[hand][0],b=g_s26ecFaceTouchValid[hand][1]&&g_s26ecFaceTouch[hand][1];
    if(a==b)return -1;
    return (hand?0:2)+(b?1:0);
}
static void s26ec_hint_tick(i64 now){
    float dt=(g_s26ecHintLast&&now>g_s26ecHintLast)?(float)(now-g_s26ecHintLast)/1.0e9f:0.0f;if(dt>0.1f)dt=0.1f;g_s26ecHintLast=now;
    i32 allowed=s26ec_option(S26EC_SET_HINTS)&&(g_s26ecLayers&4u)&&h5755dg_gameplay_vr()&&!h5754h_pause_active();
    for(i32 h=0;h<2;++h){
        i32 source=allowed?s26ec_hint_source(h):-1;
        i32 pressed=source>=0&&g_s26ecRawActive[source]&&g_s26ecRawButtons[source];
        s26ec_hint_step(&g_s26ecHint[h],source,pressed,now,dt);
    }
    i32 best=-1;
    for(i32 h=0;h<2;++h)if(g_s26ecHint[h].alpha>0.004f&&g_s26ecHint[h].shown>=0&&(best<0||g_s26ecHint[h].alpha>=g_s26ecHint[best].alpha))best=h;
    u32 packed=0;
    if(best>=0){
        i32 src=g_s26ecHint[best].shown,role=s26ec_hint_role(src);
        packed=0x80000000u|((u32)best<<24)|((u32)src<<16)|((u32)(role+1)<<8)|(u32)(g_s26ecHint[best].alpha*255.0f+0.5f);
    }
    __atomic_store_n(&g_s26ecHintPacked,packed,__ATOMIC_RELEASE);
}

/* Native 3D label surface. */
static void* g_s26ecWristSet;
static void* g_s26ecWristGui;
static void* g_s26ecWristViewport;
static float g_s26ecWristPos[3];
static u8 g_s26ecWristPosValid;
static u32 g_s26ecWristCreates,g_s26ecWristReplays;
static void s26ec_wrist_reset(void){g_s26ecWristSet=0;g_s26ecWristGui=0;g_s26ecWristViewport=0;g_s26ecWristPosValid=0;}
/* Billboard at pos facing the camera. Same row-major layout and axis
   convention as s26bb_subtitle_matrix (local +Z toward the viewer). */
static i32 s26ec_wrist_matrix(float* M,const float* pos,const float* cam){
    float f[3]={pos[0]-cam[0],pos[1]-cam[1],pos[2]-cam[2]};
    float len=ext_Sqrtf(f[0]*f[0]+f[1]*f[1]+f[2]*f[2]);if(!(len>0.0001f))return 0;
    for(i32 k=0;k<3;++k)f[k]/=len;
    float hm=ext_Sqrtf(f[0]*f[0]+f[2]*f[2]);if(!(hm>0.05f))return 0;
    float fx=f[0]/hm,fz=f[2]/hm,s=f[1],c=hm;
    float right[3]={-fz,0.0f,fx},up[3]={-fx*s,c,-fz*s},forward[3]={fx*c,s,fz*c};
    h10_identity(M);
    for(i32 a=0;a<3;++a){M[a*4]=right[a];M[a*4+1]=up[a];M[a*4+2]=-forward[a];M[a*4+3]=pos[a];}
    return 1;
}
static i32 s26ec_wrist_prepare(void){
    u32 packed=__atomic_load_n(&g_s26ecHintPacked,__ATOMIC_ACQUIRE);
    if(!(packed>>31)||g_h576mScriptRuntimePublished!=1||!h5755dg_gameplay_vr())return 0;
    i32 hand=(i32)((packed>>24)&1u);
    void* gui=0;void** slot=0;void* hud=0;if(!h5755du_get_roots(&gui,&slot,&hud))return 0;(void)slot;
    u8* soma=(u8*)ext_GetModuleHandleA(0);if(!soma)return 0;
    PFN_H5755DU_GetViewport getVp=(PFN_H5755DU_GetViewport)(void*)(soma+H5755DU_GET_VIEWPORT_RVA);
    PFN_H5755DU_GetSet getSet=(PFN_H5755DU_GetSet)(void*)(soma+H5755DU_GET_SET_RVA);
    PFN_H5755DU_CreateSet createSet=(PFN_H5755DU_CreateSet)(void*)(soma+H5755DU_CREATE_SET_RVA);
    PFN_H5755DU_AddGuiSet addSet=(PFN_H5755DU_AddGuiSet)(void*)(soma+H5755DU_ADD_GUISET_RVA);
    PFN_H5755DU_SetVirtualSize setVirtual=(PFN_H5755DU_SetVirtualSize)(void*)(soma+H5755DU_SET_VIRTUAL_SIZE_RVA);
    PFN_H5755DU_SetIs3D set3d=(PFN_H5755DU_SetIs3D)(void*)(soma+H5755DU_SET_IS3D_RVA);
    PFN_H5755DU_Set3DVec setSize=(PFN_H5755DU_Set3DVec)(void*)(soma+H5755DU_SET_3D_SIZE_RVA);
    PFN_H5755DU_Set3DMatrix setM=(PFN_H5755DU_Set3DMatrix)(void*)(soma+H5755DU_SET_3D_TRANSFORM_RVA);
    if(!h20_mem_executable((void*)getVp)||!h20_mem_executable((void*)getSet)||!h20_mem_executable((void*)createSet)||!h20_mem_executable((void*)addSet)||
       !h20_mem_executable((void*)setVirtual)||!h20_mem_executable((void*)set3d)||!h20_mem_executable((void*)setSize)||!h20_mem_executable((void*)setM))return 0;
    void* set=(g_s26ecWristGui==gui&&g_s26ecWristSet&&h20_mem_readable(g_s26ecWristSet,0x188u))?g_s26ecWristSet:0;
    if(!set){
        H5755DUTString name;h5755du_small_string(&name,"VR_WristHint");
        set=getSet(gui,&name);
        if(!set){void* skin=*(void**)((u8*)hud+0x18);if(skin&&!h20_mem_readable(skin,8))skin=0;set=createSet(gui,&name,skin);g_s26ecWristCreates++;}
        if(!set||!h20_mem_readable(set,0x188u))return 0;
        g_s26ecWristGui=gui;g_s26ecWristSet=set;g_s26ecWristViewport=0;
        ext_Log(">>> S26EC WRIST HINT SET ready: cGui %p set %p | cGui owns lifetime",gui,set);
    }
    void* vp=getVp();if(!vp||!h20_mem_readable(vp,0xA0u))return 0;
    if(g_s26ecWristViewport!=vp){addSet(vp,set);g_s26ecWristViewport=vp;}
    g_h5755feGameHud=hud;
    float pos[3],m[16],cx=0,cz=0,cp=0;
    if(!h14_hand_pose_raw(hand,pos,m)||!h5755eb_head_view(&cx,&cz,&cp)||!g_h5755eeSubtitleCameraValid)return 0;
    float metric=h5755ea_world_units_per_meter();
    g_s26ecWristPos[0]=pos[0];g_s26ecWristPos[1]=pos[1]+S26EC_WRIST_LIFT_M*metric;g_s26ecWristPos[2]=pos[2];g_s26ecWristPosValid=1;
    float M[16];if(!s26ec_wrist_matrix(M,g_s26ecWristPos,g_h5755eeSubtitleCameraWorld))return 0;
    float minz=*(float*)((u8*)hud+0x108),maxz=*(float*)((u8*)hud+0x10C);
    if(!h9_good(minz,100000.0f)||!h9_good(maxz,100000.0f))return 0;
    float vsize[2]={S26EC_WRIST_VIRTUAL_W,S26EC_WRIST_VIRTUAL_H},voff[2]={0.0f,0.0f};
    float width=S26EC_WRIST_WIDTH_M*metric,phys[3]={width,width*S26EC_WRIST_VIRTUAL_H/S26EC_WRIST_VIRTUAL_W,1.0f*metric};
    setVirtual(set,vsize,minz,maxz,voff);setSize(set,phys);setM(set,M);
    *(u8*)((u8*)set+0x138u)=0u;set3d(set,1u);
    return 1;
}
/* Late replay: face the exact per-eye camera of this render context. */
static void s26ec_wrist_refresh(void* renderContext){
    if(!g_s26ecWristSet||!g_s26ecWristPosValid||!renderContext||!h20_mem_readable((u8*)renderContext+0x158u,64u))return;
    const float* V=(const float*)((u8*)renderContext+0x158u);
    for(i32 i=0;i<12;++i)if(!(V[i]==V[i])||V[i]<-100000.0f||V[i]>100000.0f)return;
    float tx=V[3],ty=V[7],tz=V[11];
    float cam[3]={-(V[0]*tx+V[4]*ty+V[8]*tz),-(V[1]*tx+V[5]*ty+V[9]*tz),-(V[2]*tx+V[6]*ty+V[10]*tz)};
    float M[16];if(!s26ec_wrist_matrix(M,g_s26ecWristPos,cam))return;
    u8* soma=(u8*)ext_GetModuleHandleA(0);if(!soma)return;
    PFN_H5755DU_Set3DMatrix setM=(PFN_H5755DU_Set3DMatrix)(void*)(soma+H5755DU_SET_3D_TRANSFORM_RVA);
    if(h20_mem_executable((void*)setM))setM(g_s26ecWristSet,M);
}
