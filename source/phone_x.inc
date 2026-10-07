/* Story phone only. Exact GetMainBody capture, bounded script lease, no scans. */
static i32 s26x_phone_gate(void){
    return g_h576mScriptRuntimePublished==1&&p2_xr_on()&&p2_xr_running()&&!g_h576bfMapTransitionActive&&g_h5753cAuthorityEnabled&&!h5754h_pause_active()&&g_lastSyncResult==0;
}
static void s26x_phone_reset(void){
    g_s26xPhoneActive=0;g_s26xPhonePending=0;g_s26xPhoneRequest=0;g_s26xPhoneCapture=0;
    g_s26xPhoneRaw=0;g_s26xPhoneWrapper=0;g_s26xPhoneWorld=0;g_s26xPhoneCaptured=0;
    g_s26xPhoneTap=0;g_s26xPhoneAnswered=0;g_s26xPhoneGripArmed=0;
    g_s26xPhoneTapArmed[0]=g_s26xPhoneTapArmed[1]=0;g_s26xPhonePulse=0;
}
static i32 s26x_phone_body_valid(void){
    return g_s26xPhoneRaw&&g_s26xPhoneWrapper&&g_s26xPhoneWorld==g_h14NewtonWorld&&
        h20_mem_readable(g_s26xPhoneWrapper,0x2f0u)&&
        *(const void**)((u8*)g_s26xPhoneWrapper+0x2e8)==g_s26xPhoneRaw&&
        p_h14GetUserData&&p_h14GetUserData(g_s26xPhoneRaw)==g_s26xPhoneWrapper;
}
static i32 s26x_phone_token(const H5730TString* command){
    if(h5748t_sso_eq(command,"E",1u)){s26x_phone_reset();return 1;}
    if(!s26x_phone_gate())return 0;
    if(h5748t_sso_eq(command,"B",1u)){s26x_phone_reset();g_s26xPhoneActive=1;}
    if(h5748t_sso_eq(command,"F",1u)){g_s26xPhoneActive=1;g_s26xPhoneLease=g_h14PhysicsSteps;return 1;}
    if(!g_s26xPhoneActive)return 0;
    g_s26xPhoneLease=g_h14PhysicsSteps;
    if(h5748t_sso_eq(command,"P",1u)){
        if(!g_s26xPhonePending){g_s26xPhoneGripArmed=0;g_s26xPhonePulse=0;}
        g_s26xPhonePending=1;g_s26xPhoneRaw=0;g_s26xPhoneWrapper=0;return 1;
    }
    if(h5748t_sso_eq(command,"V",1u)){g_s26xPhonePending=0;g_s26xPhoneRequest=0;return 1;}
    if(h5748t_sso_eq(command,"C",1u)){g_s26xPhoneCapture=1;g_s26xPhoneCaptured=0;return 1;}
    if(h5748t_sso_eq(command,"D",1u)){
        g_s26xPhoneCapture=0;
        if(!g_s26xPhoneCaptured)return 0;
        if(g_s26xPhoneRaw!=g_s26xPhoneCaptured)g_s26xPhoneTapArmed[0]=g_s26xPhoneTapArmed[1]=0;
        g_s26xPhoneRaw=g_s26xPhoneCaptured;g_s26xPhoneWrapper=p_h14GetUserData(g_s26xPhoneRaw);g_s26xPhoneWorld=g_h14NewtonWorld;
        return s26x_phone_body_valid();
    }
    if(h5748t_sso_eq(command,"G",1u))return g_s26xPhoneRequest;
    if(h5748t_sso_eq(command,"K",1u)){g_s26xPhoneRequest=0;g_s26xPhoneGripArmed=0;return 1;}
    if(h5748t_sso_eq(command,"S",1u)){g_s26xPhoneAnswered=1;g_s26xPhoneTap=0;return 1;}
    if(h5748t_sso_eq(command,"A",1u)||h5748t_sso_eq(command,"J",1u)){
        i32 wanted=h5748t_sso_eq(command,"A",1u)?1:2;
        if(g_s26xPhoneTap!=wanted)return 0;g_s26xPhoneTap=0;return 1;
    }
    if(!h5748t_sso_eq(command,"R",1u))return 1;
    if(!g_s26xPhoneRequest||!g_s26xPhonePending||g_h14GripBody[1]||!visual_pose_valid(1)||!g_lastSqueezeActive[1]||g_lastSqueeze[1]<=.55f||!s26x_phone_body_valid())return 0;
    if(g_h14GripBody[0]==g_s26xPhoneRaw||!p_h14GetMatrix||!p_h34NewtonSetMatrix||!p_h536GetTransformCallback||!p_h14GetMass)return 0;
    float pos[3],hm[16],gc[3],bm[16];if(!h14_hand_pose_raw(1,pos,hm))return 0;h15_grip_center_world(1,hm,gc);
    PFN_H536_NewtonTransformCallback cb=p_h536GetTransformCallback(g_s26xPhoneRaw);if(!cb||!h20_mem_executable((void*)cb))return 0;
    float mass=0,ix=0,iy=0,iz=0;p_h14GetMass(g_s26xPhoneRaw,&mass,&ix,&iy,&iz);if(!(mass>.001f&&mass<1.0f))return 0;
    if(!s26ef_prepare_holster(1,2,"Phone",g_s26xPhoneRaw,hm,gc,bm))return 0;
    p_h34NewtonSetMatrix(g_s26xPhoneRaw,bm);cb(g_s26xPhoneRaw,bm,0);
    float zero[4]={0,0,0,0};if(p_h14SetVelocity)p_h14SetVelocity(g_s26xPhoneRaw,zero);if(p_h14SetOmega)p_h14SetOmega(g_s26xPhoneRaw,zero);
    s26ef_holster_latch_begin(1);h14_latch(1,g_s26xPhoneRaw,0,mass,hm,gc,.035f,gc,0,0,0);s26ef_holster_latch_end(1);
    if(g_h14GripBody[1]!=g_s26xPhoneRaw)return 0;
    g_s26xPhoneRequest=0;g_s26xPhonePending=0;g_s26xPhoneTapArmed[0]=g_s26xPhoneTapArmed[1]=0;
    h576ac_queue_haptic(1,H576AC_HAPTIC_CONFIRM);ext_Log(">>> S26X PHONE: right-hand retrieval committed; screen tap required to answer");return 1;
}
/* GUI coordinates from the stock mesh's indexed UVs, with HPL's V flip.
   Body_1 origin is y=.005; screen lies at mesh y=.01189458. */
static i32 s26x_phone_hit(float x,float y,float z,float radius,i32* armed){
    float u=(.04055895f-z)/.08111791f,v=(x+.07223097f)/.1433988f;
    float distance=y-.00689458f;
    if(distance>radius+.025f){*armed=1;return 0;}
    if(distance<-.004f){*armed=0;return 0;}
    if(distance>radius+.012f)return 0;
    /* Keep the approach armed when a light touch lands just outside a button.
       Sliding onto Accept must not require pulling completely away first. */
    i32 hit=v>=.6f&&v<=.775f?(u>=.05f&&u<=.5f?1:(u>=.525f&&u<=.975f?2:0)):0;
    if(!hit||!*armed)return 0;*armed=0;return hit;
}
static void s26x_phone_grip(i32 valid,i32 occupied,i32 active,float squeeze){
    if(!valid||occupied||!active){g_s26xPhoneGripArmed=0;g_s26xPhoneRequest=0;return;}
    if(squeeze<.28f){g_s26xPhoneGripArmed=1;g_s26xPhoneRequest=0;}
    if(squeeze>.55f&&g_s26xPhoneGripArmed){g_s26xPhoneGripArmed=0;g_s26xPhoneRequest=1;}
}
static void s26x_phone_step(float dt){
    if(!g_s26xPhoneActive)return;
    if(g_h576bfMapTransitionActive||g_h14PhysicsSteps-g_s26xPhoneLease>60u){s26x_phone_reset();return;}
    if(!s26x_phone_gate()){
        g_s26xPhoneGripArmed=0;g_s26xPhoneRequest=0;g_s26xPhoneTap=0;g_s26xPhoneTapArmed[0]=g_s26xPhoneTapArmed[1]=0;return;
    }
    if(g_s26xPhonePending){
        s26x_phone_grip(visual_pose_valid(1),g_h14GripBody[1]!=0,g_lastSqueezeActive[1],g_lastSqueeze[1]);
        if(!visual_pose_valid(1)||g_h14GripBody[1]||!g_lastSqueezeActive[1])return;
        if(dt>0&&dt<.1f)g_s26xPhonePulse-=dt;
        if(g_s26xPhonePulse<=0&&!g_s26xPhoneRequest){h576ac_queue_haptic(1,H576AC_HAPTIC_READY);g_s26xPhonePulse=.85f;}
        return;
    }
    if(g_s26xPhoneAnswered||g_s26xPhoneTap||!s26x_phone_body_valid()||!p_h14GetMatrix)return;
    float bm[16];p_h14GetMatrix(g_s26xPhoneRaw,bm);
    for(i32 h=0;h<2;++h){
        if(g_h14GripBody[h]||!visual_pose_valid(h)||h10_raw_finger_input(h,1)>H48_POKE_INDEX_CURL_MAX){g_s26xPhoneTapArmed[h]=0;continue;}
        float visible[16],c[4],pts[5][3];i32 len=0;
        if(!h5755cu_render_hand_model(h,visible)){g_s26xPhoneTapArmed[h]=0;continue;}
        for(i32 j=0;j<4;++j)c[j]=h18_joint_input(h,1,j);
        if(!h18_finger_points_world(h,1,c,visible,pts,&len)||len<1||len>4)continue;
        float d[3]={pts[len][0]-bm[12],pts[len][1]-bm[13],pts[len][2]-bm[14]};
        float x=d[0]*bm[0]+d[1]*bm[1]+d[2]*bm[2],y=d[0]*bm[4]+d[1]*bm[5]+d[2]*bm[6],z=d[0]*bm[8]+d[1]*bm[9]+d[2]*bm[10];
        i32 hit=s26x_phone_hit(x,y,z,h572_index_skin_radius(h,len),&g_s26xPhoneTapArmed[h]);
        if(hit){g_s26xPhoneTap=hit;h576ac_queue_haptic(h,H576AC_HAPTIC_CONFIRM);ext_Log(">>> S26X PHONE: screen tap hand %d action %d",h,hit);break;}
    }
}
