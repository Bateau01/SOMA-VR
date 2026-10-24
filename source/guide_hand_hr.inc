/* Script-owned graphics-only ghost. The scope is consumed synchronously by
   SetCoverageAmount; it never stores a mesh/bone pointer or changes live hands. */
static float g_s26ikGuideContact[3];
static i32 g_s26ikGuideContactValid;
static i32 g_s26hrGuideHand=-1,g_s26hrGuideFist,g_s26hrGuideSuccess;
static i32 s26hr_guide_pose(void* mesh){
    i32 h=g_s26hrGuideHand;g_s26hrGuideHand=-1;g_s26hrGuideSuccess=0;g_s26ikGuideContactValid=0;
    if(h<0||h>1)return 0;
    if(!mesh||!g_s26MeshReady||!s26_native_hand_allowed(h))return 1;
    H10Skin* hs=&p2_skin()[h];if(hs->jointCount<1||hs->jointCount>32)return 1;
    void* bones[32];
    for(i32 j=0;j<hs->jointCount;j++){
        char name[7]={'V','R','_','J',(char)('0'+j/10),(char)('0'+j%10),0};
        H5730TString str;h5730_literal_string(&str,name);bones[j]=p_s26BoneNamed(mesh,&str);
        if(!bones[j])return 1;
    }
    h10_build_rig(h);
    float world[32][16];i32 contactJoint=-1,contactDepth=-1;
    for(i32 j=0;j<hs->jointCount;j++){
        float local[16],native[16];h10_copy_f(local,hs->joints[j].local,16);
        i32 c=g_chainOf[h][j];
        if(c>=0&&c<5)s26q_apply_joint_pose(h,j,g_chainLabel[h][c],g_chainLen[h][c],
            g_chainDepth[h][j],(g_s26hrGuideFist==1 || (g_s26hrGuideFist==2 && g_chainLabel[h][c]!=1))?1.0f:0.0f,0,local);
        i32 parent=hs->joints[j].parent;
        if(parent>=0&&parent<j)h10_matmul(world[parent],local,world[j]);else h10_copy_f(world[j],local,16);
        if(c>=0&&c<5&&g_chainLabel[h][c]==(g_s26hrGuideFist==2?1:2)){
            i32 depth=g_chainDepth[h][j];
            if((g_s26hrGuideFist==2&&depth>contactDepth)||(g_s26hrGuideFist==1&&depth==2)){contactJoint=j;contactDepth=depth;}
        }
        for(i32 a=0;a<3;a++)local[12+a]=(local[12+a]-(hs->joints[j].parent<0?hs->pivot[a]:0.0f))*.01f;
        for(i32 r=0;r<4;r++)for(i32 c2=0;c2<4;c2++)native[r*4+c2]=local[c2*4+r];
        p_s26NodeMatrix(bones[j],native,0);
    }
    if(contactJoint>=0){g_s26ikGuideContactValid=1;for(i32 a=0;a<3;a++)g_s26ikGuideContact[a]=(world[contactJoint][12+a]-hs->pivot[a])*.01f;}
    else {for(i32 a=0;a<3;a++)g_s26ikGuideContact[a]=0;}
    p_s26MeshReset(mesh);g_s26hrGuideSuccess=1;return 1;
}
