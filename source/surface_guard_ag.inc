/* S26AG: only active, free HPL hands against ownerless zero-mass world bodies.
   Contact data comes from the existing traversal. Exact shape metadata is reused per
   hand-body generation. Four planes, 32 contact points and 12 rotation trials
   are hard bounds; no broadphase scans or new Newton queries are introduced. */
typedef struct {S26AGCore core;const void* body;const void* world;u32 generation,enabled,points;float pre[16];} S26AGRuntime;
static S26AGRuntime g_s26ag[2];
static u32 g_s26agCorrections[2],g_s26agLogs[2],g_s26agBuildFailures[2];
static i32 h536_sync_managed_transform(i32 hand,const float* target,const char* why);
static void s26ag_begin(i32 h){
    S26AGRuntime* t=&g_s26ag[h];t->enabled=0;t->points=0;
    const void* b=g_h34HandNewton[h];
    if(!b||!g_h34HandWrapper[h]||!g_h538PreSolverValid[h]||!g_h34BodyToHandValid[h]||!g_h545PoseValid[h]||g_h14GripBody[h]||g_h549AcquireTicks[h]||g_h532Dormant[h]||g_h532ArmState[h]!=2||!p_h14GetMatrix||!p_h14GetVelocity||!p_h14GetOmega||!p_h14SetVelocity||!p_h14SetOmega||h5748_is_stump(h)){
        t->body=0;t->core.count=0;t->core.admitted=0;t->core.clear=0;return;
    }
    if(t->body!=b||t->world!=g_h14NewtonWorld||t->generation!=g_h526BodyCreates[h]){
        t->body=0;t->core.count=0;t->core.admitted=0;t->core.clear=0;
        if(!s26ag_load_shape(h,g_h536NativePalmShape[h],&t->core.hull)){g_s26agBuildFailures[h]++;return;}
        t->body=b;t->world=g_h14NewtonWorld;t->generation=g_h526BodyCreates[h];
    }
    h10_copy_f(t->pre,g_h538PreSolverM[h],16);s26ag_begin_contacts(&t->core);t->enabled=1;
}
static void s26ag_note(i32 h,const void* b,const void* other,const void* joint){
    S26AGRuntime* t=&g_s26ag[h];if(!t->enabled||!t->core.admitted||t->points>=32u||!p_h14GetMass||!p_h567ContactFirst||!p_h567ContactNext||!p_h567ContactMaterial||!p_h567ContactPosNormal)return;
    float mass=-1,ix=0,iy=0,iz=0;p_h14GetMass(other,&mass,&ix,&iy,&iz);if(mass!=0.0f||h482_body_owner(other,0))return;
    for(void* ct=p_h567ContactFirst(joint);ct&&t->points<32u;ct=p_h567ContactNext(joint,ct)){
        t->points++;void* material=p_h567ContactMaterial(ct);if(!material)continue;float p[3],n[3];p_h567ContactPosNormal(material,b,p,n);
        i32 valid=1;for(i32 a=0;a<3;++a)if(!h9_good(p[a],100000.0f)||!h9_good(n[a],1.1f))valid=0;
        if(valid)s26ag_contact_plane(&t->core,other,p,n,t->pre);
    }
}
static void s26ag_finish(i32 h,i32 worldContact){
    S26AGRuntime* t=&g_s26ag[h];if(!t->enabled)return;s26ag_end_contacts(&t->core,worldContact);
    if(!t->core.count)return;float post[16],out[16],v[4]={0},w[4]={0};p_h14GetMatrix(t->body,post);p_h14GetVelocity(t->body,v);p_h14GetOmega(t->body,w);
    for(i32 i=0;i<16;++i)if(!h9_good(post[i],100000.0f)||!h9_good(t->pre[i],100000.0f))return;
    if(!s26ag_correct(&t->core,t->pre,post,out,v,w))return;
    if(!h536_sync_managed_transform(h,out,"S26AG static surface crossing guard"))return;
    p_h14SetVelocity(t->body,v);p_h14SetOmega(t->body,w);g_s26agCorrections[h]++;
    if(g_s26agLogs[h]<32u){g_s26agLogs[h]++;float correction=h10_len3(out[12]-post[12],out[13]-post[13],out[14]-post[14]);float travel=h10_len3(out[12]-t->pre[12],out[13]-t->pre[13],out[14]-t->pre[14]);
        ext_Log(">>> S26AG SURFACE GUARD %s #%u: step %u planes %d | rejected-solver correction %.5f | visible pre-to-safe travel %.5f | static free-hand only",h==0?"L":"R",g_s26agCorrections[h],g_h14PhysicsSteps,t->core.count,correction,travel);}
}
