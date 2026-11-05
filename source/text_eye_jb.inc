/* Native main-camera view contains raw eye orientation and eye-mid translation.
   P2 world submission adds eye separation later; GuiSet bypasses that submission.
   Input/output: row-major model-view, world units. XrPose translations: metres.
   Correct only the missing translation, never projection, camera or GUI ownership. */
static i32 s26jb_text_eye_model(const float* mv,const XrPosef* left,const XrPosef* right,i32 eye,float metric,float* out){
    if(!mv||!left||!right||!out||eye<0||eye>1||!h9_good(metric,100.0f)||metric<=0)return 0;
    for(i32 i=0;i<16;i++)if(!h9_good(mv[i],100000.0f))return 0;
    const XrPosef* e=eye?right:left;float q[4]={e->orientation.x,e->orientation.y,e->orientation.z,e->orientation.w};
    float n=0;for(i32 i=0;i<4;i++){if(!h9_good(q[i],2.0f))return 0;n+=q[i]*q[i];}
    if(n<.5f||n>1.5f)return 0;
    float delta[3]={right->position.x-left->position.x,right->position.y-left->position.y,right->position.z-left->position.z};
    float d2=0;for(i32 i=0;i<3;i++){if(!h9_good(delta[i],.2f))return 0;d2+=delta[i]*delta[i];}
    if(d2>.0225f)return 0;
    float inv=1.0f/ext_Sqrtf(n);for(i32 i=0;i<4;i++)q[i]*=inv;
    float rot[9];h5753h_quat_to_rot3(q,rot);h10_copy_f(out,mv,16);
    float sign=eye?-.5f:.5f;
    for(i32 i=0;i<3;i++)out[i*4+3]+=sign*metric*(rot[i]*delta[0]+rot[3+i]*delta[1]+rot[6+i]*delta[2]);
    return 1;
}
