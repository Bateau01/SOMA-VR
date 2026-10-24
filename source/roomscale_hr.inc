#include "roomscale_commit_ie.inc"
static u32 g_s26ieRoomLog;
static float g_s26ieRoomCamera[3];
/* Script update thread only. One query per rendered tracking sample; ACK owns
   only collision-accepted horizontal displacement, never stick locomotion. */
static u32 g_s26hrRoomFrame=0xffffffffu,g_s26hrRoomEpoch;
static i32 g_s26hrRoomPending,g_s26ieRoomApplied;
// Excluded physical motion is a locomotion baseline, NOT a camera-origin write.
// This keeps hands/view unchanged when leaving a terminal, pause or script.
static i32 g_s26icRoomSuspend,g_s26icRoomSample;
static u32 g_s26icRoomEpoch;
static float g_s26icRoomNeutral[2],g_s26icRoomHead[2];
static float g_s26hrRoomOrigin[3],g_s26hrRoomBasisX[3],g_s26hrRoomBasisZ[3];
static i32 s26hr_room_token(const H5730TString* cls,const H5730TString* fn){
#ifdef S26IE_NATIVE_TEST
    if(h5748t_sso_eq(fn,"TESTAPPLY",9u)){
        void* p=h5755ax_current_player();if(!p)return 0;u8* c=*(u8**)((u8*)p+0x170);if(!c)return 0;
        void* old=p2_camera_obj();*(void**)p2_camera_obj_slot()=*(void**)(c+0x1b0);
        float d[3]={.05f,0,0};i32 ok=s26ie_room_apply(d);*(void**)p2_camera_obj_slot()=old;
        ext_Log("S26IE NATIVE TEST APPLY=%d",ok);return ok;
    }
#endif
    if(h5748t_sso_eq(fn,"RESET",5u)){g_s26hrRoomPending=0;g_s26icRoomSuspend=1;return 1;}
    if(!s26s_vr_active()||!p2_xr_origin_set()||p2_head_mode()!=0||
       g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||g_h576bfMapTransitionActive||
       g_s26CutsceneHandsHidden||h5754h_pause_active()||!g_s26nHeadHeightFresh||
       (u32)(g_frameCounter-g_s26nHeadValidFrame)>2u){g_s26hrRoomPending=0;g_s26icRoomSuspend=1;return 0;}
    volatile float* origin=p2_xr_origin();
    if(h5748t_sso_eq(fn,"QUERY",5u)){
        if(g_s26hrRoomFrame==g_frameCounter)return 0;
        u32 gap=g_frameCounter-g_s26hrRoomFrame;
        g_s26hrRoomFrame=g_frameCounter;g_s26hrRoomPending=0;g_s26ieRoomApplied=0;
        volatile float* head=p2_eye_mid();float x=head[0]-origin[0],z=head[2]-origin[2];
        if(!h9_good(x,32.0f)||!h9_good(z,32.0f)){
            g_s26icRoomSuspend=1;g_s26icRoomSample=0;return 0;
        }
        if(g_s26icRoomEpoch!=g_h5735RecenterRequests){
            g_s26icRoomNeutral[0]=g_s26icRoomNeutral[1]=0;
            g_s26icRoomSample=0;g_s26icRoomEpoch=g_h5735RecenterRequests;
        }
        i32 discontinuity=g_s26icRoomSample && (gap>4u ||
            h10_len3(head[0]-g_s26icRoomHead[0],0,head[2]-g_s26icRoomHead[1])>.50f);
        g_s26icRoomHead[0]=head[0];g_s26icRoomHead[1]=head[2];g_s26icRoomSample=1;
        if(g_s26icRoomSuspend || discontinuity){
            g_s26icRoomNeutral[0]=x;g_s26icRoomNeutral[1]=z;
            g_s26icRoomSuspend=0;return 0;
        }
        x-=g_s26icRoomNeutral[0];z-=g_s26icRoomNeutral[1];
        // Numerical guard only: consume full displacement to avoid direction-dependent
        // residual offsets after a lean and return. Collision ACK remains authoritative.
        float length=h10_len3(x,0,z);if(!h9_good(length,64.0f)||length<=.00001f)return 0;
        float metric=h5755ea_world_units_per_meter(),distance=length*metric;
        if(distance>.10f)distance=.10f;
        float world[3];tracking_delta_to_game(x*distance/(length*metric),0,z*distance/(length*metric),world,world+1,world+2);
        if(!s26s_set_vector(world))return 0;
        tracking_delta_to_game(1,0,0,g_s26hrRoomBasisX,g_s26hrRoomBasisX+1,g_s26hrRoomBasisX+2);
        tracking_delta_to_game(0,0,1,g_s26hrRoomBasisZ,g_s26hrRoomBasisZ+1,g_s26hrRoomBasisZ+2);
        for(i32 k=0;k<3;k++)g_s26hrRoomOrigin[k]=origin[k];
        void* camera=p2_camera_obj();if(camera)for(i32 k=0;k<3;k++)g_s26ieRoomCamera[k]=((float*)((u8*)camera+0x10))[k];
        if(g_s26ieRoomLog<121u)g_s26ieRoomLog++;if(g_s26ieRoomLog<=120u){ext_Log("S26IE ROOM QUERY frame=%u step=%u head=%.6f,%.6f origin=%.6f,%.6f request=%.6f,%.6f camera=%.6f,%.6f",g_frameCounter,g_h14PhysicsSteps,(double)head[0],(double)head[2],(double)origin[0],(double)origin[2],(double)world[0],(double)world[2],(double)g_s26ieRoomCamera[0],(double)g_s26ieRoomCamera[2]);}
        g_s26hrRoomEpoch=g_h5735RecenterRequests;g_s26hrRoomPending=1;return 1;
    }
    i32 apply=h5748t_sso_eq(fn,"APPLY",5u);
    if((!apply&&!h5748t_sso_eq(fn,"ACK",3u))||!g_s26hrRoomPending)return 0;
    if(!apply)g_s26hrRoomPending=0;
    if(g_s26hrRoomEpoch!=g_h5735RecenterRequests)return 0;
    for(i32 k=0;k<3;k++)if(origin[k]!=g_s26hrRoomOrigin[k])return 0;
    char text[128];if(!h5748n_copy_tstring((void*)cls,text,sizeof(text)))return 0;
    if(g_s26ieRoomLog<=120u)ext_Log("S26IE ROOM ACK raw=%s epoch=%u",text,g_h5735RecenterRequests);
    char* fields[3]={text,0,0};i32 count=0;
    for(i32 k=0;text[k];k++)if(text[k]==','){text[k]=0;if(++count>=3)return 0;fields[count]=text+k+1;}
    float d[3];if(count!=2)return 0;
    for(i32 k=0;k<3;k++)if(!h11_parse_float(fields[k],d+k)||!h9_good(d[k],.102f))return 0;
    if(h9_abs(d[1])>.0001f||h10_len3(d[0],0,d[2])>.101f)return 0;
    if(apply){if(g_s26ieRoomApplied)return 0;g_s26ieRoomApplied=s26ie_room_apply(d);return g_s26ieRoomApplied;}
    float norm=h10_dot(g_s26hrRoomBasisX,g_s26hrRoomBasisX);if(norm<.24f)return 0;
    origin[0]+=h10_dot(d,g_s26hrRoomBasisX)/norm;
    origin[2]+=h10_dot(d,g_s26hrRoomBasisZ)/norm;
    void* camera=p2_camera_obj();if(camera&&g_s26ieRoomLog<=120u){float* c=(float*)((u8*)camera+0x10);ext_Log("S26IE ROOM COMMIT frame=%u step=%u accepted=%.6f,%.6f cameraDelta=%.6f,%.6f origin=%.6f,%.6f",g_frameCounter,g_h14PhysicsSteps,(double)d[0],(double)d[2],(double)(c[0]-g_s26ieRoomCamera[0]),(double)(c[2]-g_s26ieRoomCamera[2]),(double)origin[0],(double)origin[2]);}
    return 1;
}
