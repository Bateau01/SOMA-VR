/* Observation only: script/physics thread, no pose/ownership/solver writes.
   Opt-in flag read once; fixed buffer; one binary write outside NewtonUpdate.
   No pointer is dereferenced from a prior sample. */
typedef struct {
    u32 frame,step,phase,hand,state,flags; float dt;
    u64 body,held; i64 displayTime;
    float controller[3],origin[3],camera[3],tracked[3],servo[3],physical[3],velocity[3],targetVelocity[3];
} S26IFHandSample;
#define S26IF_HAND_ROWS 8192u
static S26IFHandSample g_s26ifRows[S26IF_HAND_ROWS];
static u32 g_s26ifCount,g_s26ifInit,g_s26ifEnabled,g_s26ifFinished;
static void s26if_hand_capture(u32 phase){
    if(!g_s26ifInit){
        g_s26ifInit=1;char path[520];void* f=make_sibling_path(path,sizeof(path),"hpl3vr_hand_timing.flag")?ext_fopen(path,"rb"):0;
        if(f){ext_fclose(f);
            /* IH supersedes this recorder when explicitly requested: avoid its
               mid-capture disk save perturbing the frame-timing measurement. */
            void* frameFlag=make_sibling_path(path,sizeof(path),"hpl3vr_frame_timing.flag")?ext_fopen(path,"rb"):0;
            if(frameFlag)ext_fclose(frameFlag);
            else {g_s26ifEnabled=1;ext_Log("S26IF HAND AUDIT armed: observation-only, bounded binary capture");}
        }
    }
    if(!g_s26ifEnabled||g_s26ifFinished||g_s26ifCount>=S26IF_HAND_ROWS)return;
    if(g_h576bfMapTransitionActive||g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||g_h5755asUiIslandActive||g_h5755asResumeClassifyActive||g_h5755azExitPending||g_s26CutsceneHandsHidden)return;
    void* camera=p2_camera_obj();if(!camera||!p2_xr_origin_set()||!p_h14GetMatrix||!p_h14GetVelocity)return;
    for(i32 h=0;h<2&&g_s26ifCount<S26IF_HAND_ROWS;h++){
        if(!g_h34HandNewton[h]||g_h532Dormant[h]||g_h532ArmState[h]!=2||!g_h531TrackedTargetValid[h])continue;
        S26IFHandSample* row=g_s26ifRows+g_s26ifCount++;zero_bytes(row,sizeof(*row));
        row->frame=g_frameCounter;row->step=g_h14PhysicsSteps;row->phase=phase;row->hand=(u32)h;
        row->state=g_h5755bhPresentationState;row->dt=g_h14LastPhysicsDt;
        row->body=(u64)g_h34HandNewton[h];row->held=(u64)g_h14GripBody[h];
        row->flags=(g_h545ContactThisStep[h]?1u:0u)|(g_h5755efHandIdleParked[h]?2u:0u)|(g_h5755deContactVisualActive[h]?4u:0u)|(g_h567BlockedHold[h]?8u:0u)|(g_h15GripJointed[h]?16u:0u);
        u8* xr=(u8*)p2_xr_obj();row->displayTime=xr?*(i64*)(xr+0xe8):0;
        float m[16],v[4]={0};p_h14GetMatrix(g_h34HandNewton[h],m);p_h14GetVelocity(g_h34HandNewton[h],v);
        for(i32 k=0;k<3;k++){
            row->controller[k]=((float*)&g_lastPose[h].position)[k];row->origin[k]=p2_xr_origin()[k];
            row->camera[k]=((float*)((u8*)camera+0x10))[k];row->tracked[k]=g_h531TrackedTarget[h][12+k];
            row->servo[k]=g_h526Target[h][12+k];row->physical[k]=m[12+k];row->velocity[k]=v[k];row->targetVelocity[k]=g_h528TargetVel[h][k];
        }
    }
}
static void s26if_hand_flush(void){
    if(!g_s26ifEnabled||g_s26ifFinished||g_s26ifCount<S26IF_HAND_ROWS)return;
    g_s26ifFinished=1;char path[520];if(!make_sibling_path(path,sizeof(path),"hpl3vr_hand_timing_IF.bin"))return;
    void* f=ext_fopen(path,"wb");if(!f){ext_Log("S26IF HAND AUDIT save failed");return;}
    u32 header[4]={0x46494853u,1u,(u32)sizeof(S26IFHandSample),g_s26ifCount};
    u64 a=ext_fwrite(header,sizeof(header),1,f),b=ext_fwrite(g_s26ifRows,sizeof(S26IFHandSample),g_s26ifCount,f);ext_fclose(f);
    ext_Log("S26IF HAND AUDIT saved=%u rows=%u bytesPerRow=%u file=%s",(u32)(a==1&&b==g_s26ifCount),g_s26ifCount,(u32)sizeof(S26IFHandSample),path);
}
