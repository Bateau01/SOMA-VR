/* Initial inventory draw only. Physics, item ownership and map callbacks stay
   in their existing callers. A later world grab never enters this scope. */
static u32 g_s26efHolsterDraws[2];
static void s26ef_holster_profile(i32 hand,i32 kind,const char* logical,float* rotation,float* fraction,float* curl){
    for(i32 i=0;i<9;++i)rotation[i]=(i%4)==0?1.0f:0.0f;
    fraction[0]=fraction[1]=fraction[2]=.5f;
    curl[0]=.45f;curl[1]=.70f;curl[2]=.85f;curl[3]=curl[4]=.90f;
    if(kind==1){ /* Omni-Tool: handle +Z, head -Z, display +Y. OpenXR grip -Z
                         runs through the fingers from little finger to thumb.
                         Preserve that shaft axis; +Y is not the held rod axis. */
        fraction[1]=.40f;fraction[2]=.78f;curl[1]=.60f;
    }else if(kind==2){ /* Phone: long X axis upright; screen +Y toward viewer. */
        for(i32 i=0;i<9;++i)rotation[i]=0;
        rotation[1]=rotation[5]=rotation[6]=1;fraction[0]=.35f;curl[1]=.60f;
    }else if(logical&&h576c_ci_streq(logical,"StunRod")){
        /* The small-radius -X segment is the authored handle. */
        rotation[0]=rotation[8]=0;rotation[2]=-1;rotation[6]=1;fraction[0]=.16f;
    }else if(logical&&h576c_ci_streq(logical,"ARK")){
        /* Side handle; normalized bounds also cover Phi's scaled carrier. */
        fraction[0]=hand==0?.025f:.975f;fraction[1]=.52f;curl[1]=.85f;
    }else if(logical&&h576c_ci_streq(logical,"Tracer_Fluid")){
        fraction[1]=.30f;
    }
}
static i32 s26ef_prepare_holster(i32 hand,i32 kind,const char* logical,const void* body,float* handM,float* gc,float* bodyM){
    if(hand<0||hand>1||!body||!p_h14GetCollision)return 0;
    if(!p_s26efGripThread){void* k=ext_GetModuleHandleA("kernel32.dll");if(k)p_s26efGripThread=(void*)ext_GetProcAddress(k,"GetCurrentThreadId");}
    float profile[9],fraction[3],anchor[3]={0,0,0};
    s26ef_holster_profile(hand,kind,logical,profile,fraction,g_s26efHolsterCurl[hand]);
    const char* authored=s26el_grip_profile(body,logical);
    i32 personal=s26ej_grip_override(hand,kind,authored,profile,fraction);
    if(!p_s26efBounds){void* n=ext_GetModuleHandleA("Newton.dll");if(n)p_s26efBounds=(S26EFBounds)ext_GetProcAddress(n,"NewtonCollisionCalculateAABB");}
    const void* col=p_h14GetCollision(body);if(!col||!p_s26efBounds)return 0;
    float identity[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},lo[4]={0},hi[4]={0};
    p_s26efBounds(col,identity,lo,hi);
    for(i32 i=0;i<3;++i){if(!(lo[i]>-10&&hi[i]<10&&hi[i]>lo[i]))return 0;anchor[i]=lo[i]+fraction[i]*(hi[i]-lo[i]);}
    /* Snap the authored anchor hint to the real collision surface when outside.
       Exactly one native query per inventory draw, never a per-frame scan. */
    if(!personal&&p_h14PointDistance&&g_h14NewtonWorld){float cp[4]={0},normal[4]={0};
        if(p_h14PointDistance(g_h14NewtonWorld,anchor,col,identity,cp,normal,0)){
            if(h9_good(cp[0],10)&&h9_good(cp[1],10)&&h9_good(cp[2],10))for(i32 i=0;i<3;++i)anchor[i]=cp[i];
        }
    }
    /* Initial orientation belongs to the tracked controller. h14_latch already
       stores raw^-1 * physical and physical^-1 * body. Their product must be
       raw^-1 * controller * profile, even if shoulder collision rotated the
       physical hand. Including physical rotation here would bake it into the
       held item a second time. Keep the physical contact POSITION only. */
    float invRaw[16],localContact[3],physical[16],basis9[9],basis[16];
    h14_rigid_inverse(handM,invRaw);h14_transform_point(invRaw,gc,localContact);
    quat_to_game_basis(hand,basis9);for(i32 i=0;i<16;++i)basis[i]=0;
    for(i32 a=0;a<3;++a)for(i32 b=0;b<3;++b)basis[a*4+b]=basis9[a*3+b];basis[15]=1;
    if(h34_physical_hand_model(hand,physical))h10_copy_f(handM,physical,16);
    h14_transform_point(handM,localContact,gc);
    return s26ef_holster_matrix(basis,profile,anchor,gc,bodyM);
}
static void s26ef_holster_latch_begin(i32 hand){g_s26efHolsterLatch[hand]=1;g_h552ContactLatchBypass[hand]=1;}
static void s26ef_holster_latch_end(i32 hand){
    g_s26efHolsterLatch[hand]=0;g_h552ContactLatchBypass[hand]=0;
    if(g_h14GripBody[hand]&&g_s26efHolsterDraws[hand]++<8u)ext_Log(">>> S26EH HOLSTER GRIP %s: controller-relative initial orientation; collision-hand rotation excluded; subsequent regrabs remain contact-driven",hand==0?"L":"R");
}
