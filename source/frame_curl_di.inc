/* Controller-independent joint geometry: interpret source skeletal flexion independently of Simon's rig.
   Reference endpoints are measured from Valve's supplied hand_right_poses.glb
   open/fist samples (see tests/fixtures/frame_reference_positions.json).
   They are not player calibration, and are not inferred from a startup pose.
   All controllers use the authored open-to-grip curve; runtime root spread
   cannot change the neutral pose. Maps thumb
   flexion to the existing grip-driven thumb curve, without runtime opposition. Gameplay grip/trigger actions are never replaced. */
static i32 s26di_frame_curl(const S26QJoint* joints,i32 hand,i32 finger,float curl[4]){
    if(hand<0||hand>1||finger<0||finger>4)return 0;
    if(finger==0){
        float a,b;if(!s26q_joint_bend(joints,2,3,4,&a)||!s26q_joint_bend(joints,3,4,5,&b))return 0;
        /* Same supplied open/fist reference poses; grip animation's authored
           thumb endpoint is 0.55, rather than 1.0, on every thumb joint. */
        float value=0.55f*clamp01((a+b-0.566961826f)/(2.065302268f-0.566961826f));
        for(i32 d=0;d<4;++d)curl[d]=value;return 1;
    }
    static const float open[4]={0.12683541f,0.11057418f,0.23616299f,0.20579153f};
    static const float closed[4]={4.82845678f,4.96191741f,4.85911875f,4.38118567f};
    float wrist[3],index[3],middle[3],little[3],lateral[3],forward[3],normal[3],axis[3];
    if(!s26q_joint_position(joints+1,wrist)||!s26q_joint_position(joints+7,index)||
       !s26q_joint_position(joints+12,middle)||!s26q_joint_position(joints+22,little))return 0;
    for(i32 k=0;k<3;++k){lateral[k]=index[k]-little[k];forward[k]=middle[k]-wrist[k];}
    s26q_root_cross(forward,lateral,normal);if(!s26q_root_unit(normal))return 0;
    float p[5][3];i32 start=6+(finger-1)*5;
    for(i32 d=0;d<5;++d)if(!s26q_joint_position(joints+start+d,p[d]))return 0;
    for(i32 k=0;k<3;++k)forward[k]=p[1][k]-p[0][k];
    if(!s26q_root_unit(forward))return 0;
    s26q_root_cross(forward,normal,axis);if(!s26q_root_unit(axis)||!h5755bl_resolve_atan2f())return 0;
    float sum=0.0f;
    for(i32 d=1;d<4;++d){
        float u[3],v[3],cross[3];
        for(i32 k=0;k<3;++k){u[k]=p[d][k]-p[d-1][k];v[k]=p[d+1][k]-p[d][k];}
        float nu=s26q_root_dot(u,u),nv=s26q_root_dot(v,v);
        if(!(nu>0.000001f&&nu<0.04f&&nv>0.000001f&&nv<0.04f))return 0;
        /* Ignore sideways displacement, preserve inward/outward bend sign.
           Use one anatomical flexion plane for the chain; rebuilding it from
           the palm normal at every joint flips sign beyond a 90-degree bend. */
        float du=s26q_root_dot(u,axis),dv=s26q_root_dot(v,axis);
        for(i32 k=0;k<3;++k){u[k]-=du*axis[k];v[k]-=dv*axis[k];}
        if(s26q_root_dot(u,u)<nu*0.01f||s26q_root_dot(v,v)<nv*0.01f)return 0;
        if(!s26q_root_unit(u)||!s26q_root_unit(v))return 0;
        s26q_root_cross(u,v,cross);
        float a=p_h5755blAtan2f(s26q_root_dot(cross,axis),s26q_root_dot(u,v));
        if(!(a>=-3.142f&&a<=3.142f))return 0;sum+=hand?-a:a;
    }
    float value=clamp01((sum-open[finger-1])/(closed[finger-1]-open[finger-1]));
    curl[0]=curl[1]=curl[2]=curl[3]=value;return 1;
}
