/* Palm-relative knuckle direction: spreading on intact fingers, plus thumb
   elevation/opposition. Published input is separate from accepted geometry. */
static u64 g_s26qRootInput[2][5],g_s26qRootApplied[2][5];
static u64 g_s26qRootCandidate[2][5],g_s26qRootPending[2][5],g_s26qRootStaged[2][5],g_s26qRootShape[2][5];
static u32 g_s26qRootRigReady[2][5];
static void s26q_clear_root_input(void){for(i32 h=0;h<2;++h)for(i32 f=0;f<5;++f)__atomic_store_n(&g_s26qRootInput[h][f],0ULL,__ATOMIC_RELEASE);}
static float s26q_root_dot(const float* a,const float* b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void s26q_root_cross(const float* a,const float* b,float* c){c[0]=a[1]*b[2]-a[2]*b[1];c[1]=a[2]*b[0]-a[0]*b[2];c[2]=a[0]*b[1]-a[1]*b[0];}
static i32 s26q_root_unit(float* a){float n=ext_Sqrtf(s26q_root_dot(a,a));if(!(n>0.00001f&&n<10000.0f))return 0;for(i32 k=0;k<3;++k)a[k]/=n;return 1;}
static i32 s26q_root_basis(const float* wrist,const float* index,const float* middle,const float* little,float* x,float* y,float* z){
    for(i32 k=0;k<3;++k){x[k]=index[k]-little[k];z[k]=middle[k]-wrist[k];}
    if(!s26q_root_unit(z))return 0;
    float dot=s26q_root_dot(x,z);for(i32 k=0;k<3;++k)x[k]-=dot*z[k];
    if(!s26q_root_unit(x))return 0;s26q_root_cross(z,x,y);return s26q_root_unit(y);
}
static i32 s26q_root_angles(const float* direction,const float* x,const float* y,const float* z,float* yaw,float* elevation){
    float d[3]={direction[0],direction[1],direction[2]};if(!s26q_root_unit(d)||!h5755bl_resolve_atan2f())return 0;
    float dx=s26q_root_dot(d,x),dy=s26q_root_dot(d,y),dz=s26q_root_dot(d,z),flat=ext_Sqrtf(dx*dx+dz*dz);
    if(!(flat>0.12f&&flat<1.01f))return 0; /* closed fingers with no reliable projected heading */
    *yaw=p_h5755blAtan2f(dx,dz);*elevation=p_h5755blAtan2f(dy,flat);
    return *yaw>=-3.142f&&*yaw<=3.142f&&*elevation>=-1.571f&&*elevation<=1.571f;
}
static u64 s26q_root_pack(float yaw,float elevation){
    if(!(yaw>=-3.142f&&yaw<=3.142f&&elevation>=-1.571f&&elevation<=1.571f))return 0;
    u32 a=(u32)((yaw+3.142f)*(65535.0f/6.284f)+0.5f),b=(u32)((elevation+1.571f)*(65535.0f/3.142f)+0.5f);
    return (1ULL<<63)|(u64)a|((u64)b<<16);
}
static i32 s26q_root_unpack(u64 packet,float* yaw,float* elevation){
    if(!(packet&(1ULL<<63)))return 0;
    *yaw=(float)(packet&65535u)*(6.284f/65535.0f)-3.142f;
    *elevation=(float)((packet>>16)&65535u)*(3.142f/65535.0f)-1.571f;return 1;
}
static i32 s26q_root_near(u64 a,u64 b){
    if((a^b)&(1ULL<<63))return 0;if(!(a&(1ULL<<63)))return 1;
    float ay,ae,by,be;
    if(!s26q_root_unpack(a,&ay,&ae)||!s26q_root_unpack(b,&by,&be))return 0;
    float d=ay-by;if(d>3.142f)d-=6.284f;if(d<-3.142f)d+=6.284f;
    return d>-.0174533f&&d<.0174533f&&ae-be>-.0174533f&&ae-be<.0174533f;
}
static i32 s26q_roots_near(const u64* a,const u64* b){for(i32 f=0;f<5;++f)if(!s26q_root_near(a[f],b[f]))return 0;return 1;}
static i32 s26q_roots_equal(const u64* a,const u64* b){for(i32 f=0;f<5;++f)if(a[f]!=b[f])return 0;return 1;}
static void s26q_roots_copy(u64* to,const u64* from){for(i32 f=0;f<5;++f)to[f]=from[f];}
static void s26q_roots_read(i32 hand,u64* out){for(i32 f=0;f<5;++f)out[f]=__atomic_load_n(&g_s26qRootInput[hand][f],__ATOMIC_ACQUIRE);}
static void s26q_roots_reset(i32 hand){
    for(i32 f=0;f<5;++f){__atomic_store_n(&g_s26qRootApplied[hand][f],0ULL,__ATOMIC_RELEASE);__atomic_store_n(&g_s26qRootRigReady[hand][f],0u,__ATOMIC_RELEASE);g_s26qRootCandidate[hand][f]=g_s26qRootPending[hand][f]=g_s26qRootStaged[hand][f]=g_s26qRootShape[hand][f]=0;}
}
static void s26q_roots_commit(i32 hand){for(i32 f=0;f<5;++f)__atomic_store_n(&g_s26qRootApplied[hand][f],g_s26qRootStaged[hand][f],__ATOMIC_RELEASE);}
static u64 s26q_root_applied(i32 hand,i32 finger){return __atomic_load_n(&g_s26qRootApplied[hand][finger],__ATOMIC_ACQUIRE);}
static u64 s26q_root_from_joints(const S26QJoint* joints,i32 finger){
    float wrist[3],index[3],middle[3],little[3],a[3],b[3],x[3],y[3],z[3],d[3],yaw,elevation;
    if(!s26q_joint_position(joints+1,wrist)||!s26q_joint_position(joints+7,index)||!s26q_joint_position(joints+12,middle)||!s26q_joint_position(joints+22,little))return 0;
    if(!s26q_root_basis(wrist,index,middle,little,x,y,z))return 0;
    i32 j=finger?7+(finger-1)*5:2;
    if(!s26q_joint_position(joints+j,a)||!s26q_joint_position(joints+j+1,b))return 0;
    for(i32 k=0;k<3;++k)d[k]=b[k]-a[k];
    if(!s26q_root_angles(d,x,y,z,&yaw,&elevation))return 0;
    /* Non-thumb flexion already has independent knuckle bends. */
    return s26q_root_pack(yaw,finger?0.0f:elevation);
}
