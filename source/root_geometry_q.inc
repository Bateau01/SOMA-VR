static i32 s26q_rig_joint(i32 hand,i32 finger,i32 depth){
    i32 chain=h10_chain_for_finger(hand,finger);if(chain<0)return -1;
    H10Skin* hs=&p2_skin()[hand];for(i32 j=0;j<hs->jointCount;++j)if(g_chainOf[hand][j]==chain&&g_chainDepth[hand][j]==depth)return j;return -1;
}
typedef struct {float x[3],y[3],z[3],from[3],yaw,elevation,w[9];} S26QRootRig;
static S26QRootRig g_s26qRootRig[2][5];
static i32 s26q_prepare_root_rig(i32 hand,i32 finger,i32 joint,S26QRootRig* rig){
    H10Skin* hs=&p2_skin()[hand];i32 rootDepth=finger?1:0;
    i32 a=s26q_rig_joint(hand,1,1),b=s26q_rig_joint(hand,2,1),c=s26q_rig_joint(hand,4,1),m=s26q_rig_joint(hand,2,0),child=s26q_rig_joint(hand,finger,rootDepth+1);
    if(a<0||b<0||c<0||m<0||child<0)return 0;i32 wrist=hs->joints[m].parent;if(wrist<0)return 0;
    if(!s26q_root_basis(g_bindWorld[hand][wrist]+12,g_bindWorld[hand][a]+12,g_bindWorld[hand][b]+12,g_bindWorld[hand][c]+12,rig->x,rig->y,rig->z))return 0;
    for(i32 k=0;k<3;++k){rig->from[k]=g_bindWorld[hand][child][12+k]-g_bindWorld[hand][joint][12+k];for(i32 l=0;l<3;++l)rig->w[k*3+l]=g_bindWorld[hand][joint][4*k+l];}
    return s26q_root_unit(rig->from)&&s26q_root_angles(rig->from,rig->x,rig->y,rig->z,&rig->yaw,&rig->elevation);
}
static i32 s26q_rig_root_rotation(i32 hand,i32 finger,i32 joint,u64 packet,float* rotation){
    float yaw,elevation;if(!s26q_root_unpack(packet,&yaw,&elevation))return 0;
    if(g_chainDepth[hand][joint]!=(finger?1:0))return 0;
    u32 ready=__atomic_load_n(&g_s26qRootRigReady[hand][finger],__ATOMIC_ACQUIRE);
    if(ready!=2u){
        u32 expected=0;if(!__atomic_compare_exchange_n(&g_s26qRootRigReady[hand][finger],&expected,1u,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))return 0;
        S26QRootRig prepared;
        if(!s26q_prepare_root_rig(hand,finger,joint,&prepared)){__atomic_store_n(&g_s26qRootRigReady[hand][finger],0u,__ATOMIC_RELEASE);return 0;}
        g_s26qRootRig[hand][finger]=prepared;__atomic_store_n(&g_s26qRootRigReady[hand][finger],2u,__ATOMIC_RELEASE);
    }
    /* Immutable bind data is fitted once per rig lifetime, not per capsule. */
    const S26QRootRig* rig=&g_s26qRootRig[hand][finger];const float* x=rig->x;const float* y=rig->y;const float* z=rig->z;const float* from=rig->from;
    float ry=rig->yaw,re=rig->elevation,to[3];
    float delta=yaw-ry;if(delta>3.14159265f)delta-=6.2831853f;if(delta<-3.14159265f)delta+=6.2831853f;
    float limit=finger?0.45f:0.90f;if(delta>limit)delta=limit;if(delta<-limit)delta=-limit;yaw=ry+delta;
    delta=finger?0.0f:elevation-re;if(delta>0.90f)delta=0.90f;if(delta<-0.90f)delta=-0.90f;elevation=re+delta;
    float ce=ext_Cosf(elevation),sx=ext_Sinf(yaw)*ce,sy=ext_Sinf(elevation),sz=ext_Cosf(yaw)*ce;
    for(i32 k=0;k<3;++k)to[k]=x[k]*sx+y[k]*sy+z[k]*sz;
    float axis[3];s26q_root_cross(from,to,axis);float sin=ext_Sqrtf(s26q_root_dot(axis,axis)),cos=s26q_root_dot(from,to);
    if(!(sin>0.00001f&&sin<1.01f))return 0;for(i32 k=0;k<3;++k)axis[k]/=sin;
    float angle=p_h5755blAtan2f(sin,cos),local[3];
    for(i32 k=0;k<3;++k)local[k]=rig->w[3*k]*axis[0]+rig->w[3*k+1]*axis[1]+rig->w[3*k+2]*axis[2];
    if(!s26q_root_unit(local))return 0;h10_axis_angle(local,angle,rotation);return 1;
}
static void s26q_apply_joint_pose(i32 hand,i32 j,i32 finger,i32 len,i32 depth,float input,u64 root,float* posed){
    H10Skin* hs=&p2_skin()[hand];float rot[16],base[16];const float* bind=hs->joints[j].local;
    if(root&&s26q_rig_root_rotation(hand,finger,j,root,rot)){h10_matmul(bind,rot,base);bind=base;h10_copy_f(posed,base,16);}
    s26q_bend_from_base(hand,j,finger,len,depth,input,bind,posed);
}
static void s26q_apply_joint_bend(i32 hand,i32 j,i32 finger,i32 len,i32 depth,float input,float* posed){
    s26q_apply_joint_pose(hand,j,finger,len,depth,input,s26q_root_applied(hand,finger),posed);
}
