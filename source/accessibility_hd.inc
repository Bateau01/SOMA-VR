/* Opt-in accessibility. Newton 2.36 ray ABI verified against its header.
   Physical contact paths run first. No SetMatrix, collision disabling, socket
   extraction, inventory callbacks or changes to the ordinary holding solver. */
typedef float (__attribute__((ms_abi)) *S26HDRayFilter)(const void*,const float*,i32,void*,float);
typedef u32 (__attribute__((ms_abi)) *S26HDRayPre)(const void*,const void*,void*);
typedef void (__attribute__((ms_abi)) *S26HDRayCast)(const void*,const float*,const float*,S26HDRayFilter,void*,S26HDRayPre);
static S26HDRayCast p_s26hdRay;
static void (__attribute__((ms_abi)) *p_s26hdWake)(const void*,i32);
typedef struct { const void* body;float t; } S26HDHit;
typedef struct { const void* body;void* wrapper;void* owner;float last[3],age; } S26HDPull;
static S26HDPull g_s26hdPull[2];
static S26HDPull g_s26hlInteraction[2];
static float g_s26hlInteractionPoint[2][3];
static u8 g_s26hlReadStage[2],g_s26hlHeld[2];
static u32 g_s26hlReadId[2];
static float g_s26hlReadPoint[2][3];
static i32 s26hl_read_catch(const void* body){
    if(!body||!g_s26hdRemoteEnabled)return 0;
    for(i32 h=0;h<2;h++)if(g_s26hlReadStage[h]==2&&g_s26hdPull[h].body==body)return 1;
    return 0;
}
static i32 s26hl_read_inflight(u32 id){
    if(!g_s26hdRemoteEnabled)return 0;
    for(i32 h=0;h<2;h++)if(g_s26hlReadStage[h]==2&&g_s26hdPull[h].body&&g_s26hlReadId[h]==id)return 1;
    return 0;
}
/* Visual nominations only, renewed by the exact accepted remote target. */
static S26HDPull g_s26heOutline[2];
static u32 g_s26heOutlineStep[2];
static void s26he_nominate(i32 h,const void* body,void* wrapper,void* owner){
    S26HDPull* p=&g_s26heOutline[h];float m[16];
    p_h14GetMatrix(body,m);p->body=body;p->wrapper=wrapper;p->owner=owner;
    h10_copy_f(p->last,m+12,3);g_s26heOutlineStep[h]=g_h14PhysicsSteps;
}
static const void* g_s26hdHover[2];
static S26HDPull g_s26hgFocus[2];
static float g_s26hgScanAge[2];
static u32 g_s26hdBeamStep[2],g_s26hdBeamKind[2];
static float g_s26hdBeamStart[2][3],g_s26hdBeamEnd[2][3];
static u8 g_s26hdTriggerPrev[2];
static u32 g_s26hfDiagStep,g_s26hfDiagCount;
static u32 g_s26hiOutlinePosts,g_s26hiOutlineCalls,g_s26hiOutlinePhaseReject;
static const void* g_s26hfRayBody;
static float g_s26hfRayT;
static i32 g_s26hfTargetResult,g_s26hfIcon=-1;
static void s26hf_diag(void){
 if((!g_s26hdRemoteEnabled&&!g_s26hdLaserEnabled)||g_s26hfDiagCount>=80u||(u32)(g_h14PhysicsSteps-g_s26hfDiagStep)<180u)return;
 g_s26hfDiagStep=g_h14PhysicsSteps;g_s26hfDiagCount++;

 /* The ray pointer is cleared after each report, and only the current step's
    callback may populate it; do not dereference it in telemetry. */

 ext_Log(">>> S26HF ACCESS #%u step %u enabled %u/%u aim %u/%u pose %d/%d state %s hidden %u pause %d native %u laser %d rayAPI %p lastHit %p fraction %.3f target %d icon %d beam %u/%u",
 g_s26hfDiagCount,g_h14PhysicsSteps,g_s26hdRemoteEnabled,g_s26hdLaserEnabled,g_h5754dAimValid[0],g_h5754dAimValid[1],visual_pose_valid(0),visual_pose_valid(1),g_h5729LastClassName,g_s26CutsceneHandsHidden,h5754h_pause_active(),g_h30NativeMouseDown,g_s26hdLaserHand,p_s26hdRay,g_s26hfRayBody,g_s26hfRayT,g_s26hfTargetResult,g_s26hfIcon,g_s26hdBeamKind[0],g_s26hdBeamKind[1]);
 ext_Log(">>> S26HI OUTLINE: posts %u native submissions %u stale rejects %u nominations %p/%p step %u/%u current %u",g_s26hiOutlinePosts,g_s26hiOutlineCalls,g_s26hiOutlinePhaseReject,g_s26heOutline[0].body,g_s26heOutline[1].body,g_s26heOutlineStep[0],g_s26heOutlineStep[1],g_h14PhysicsSteps);
 g_s26hfRayBody=0;
}
static i32 s26hd_free_state(void){return h5720_streq(g_h5729LastModuleName,"player/PlayerState_Normal.hps")&&h5720_streq(g_h5729LastClassName,"cScrPlayerState_Normal");}
/* A validated ordinary prop hold may coexist with a remote pull in the free
   hand. Terminal, mechanism and scripted native-use states remain excluded. */
static i32 s26hk_remote_state(void){return s26hd_free_state()||h5755fm_grab_gameplay_actions_allowed();}
static i32 s26hk_remote_native_busy(void){return g_h30NativeMouseDown&&!h5755fm_grab_gameplay_actions_allowed();}
static void s26hd_reset(void){
    /* No body dereference during world teardown or pause. */
    zero_bytes(g_s26hgFocus,sizeof(g_s26hgFocus));zero_bytes(g_s26hgScanAge,sizeof(g_s26hgScanAge));
    zero_bytes(g_s26hlInteraction,sizeof(g_s26hlInteraction));zero_bytes(g_s26hlReadStage,sizeof(g_s26hlReadStage));zero_bytes(g_s26hlReadId,sizeof(g_s26hlReadId));
    zero_bytes(g_s26hdPull,sizeof(g_s26hdPull));zero_bytes(g_s26hdHover,sizeof(g_s26hdHover));
    zero_bytes(g_s26hdBeamKind,sizeof(g_s26hdBeamKind));zero_bytes(g_s26heOutline,sizeof(g_s26heOutline));
    if(g_s26hdLaserHand>=0)h576bo_release_pointer(1,"laser inactive");
    g_s26hdLaserHand=-1;g_s26hdFixedOwner=0;g_s26hdTriggerPrev[0]=g_s26hdTriggerPrev[1]=1;
}
static u32 __attribute__((ms_abi)) s26hd_ray_pre(const void* body,const void* collision,void* data){
    if(body==g_h34HandNewton[0]||body==g_h34HandNewton[1])return 0;
    if(p_h14IsTrigger&&p_h14IsTrigger(collision))return 0;
    /* HPL scripted areas need not be Newton triggers. ToolArea_TracerFluid
       encloses the apartment and reports t=0 despite GetCollide()==false.
       Skip only verified inactive HPL bodies / non-colliding non-prop helpers.
       Unknown bodies, solid areas, geometry and prop screen colliders block. */
    void* w=p_h14GetUserData?p_h14GetUserData(body):0;
    if(w&&h20_mem_readable(w,0x2f0u)&&*(const void**)((u8*)w+0x2e8)==body){
        char rt[96]={0};
        if(h22_rtti_name(w,rt,sizeof(rt))&&h25_str_contains(rt,"cPhysicsBodyNewton")){
            if(!*((u8*)w+0xe4))return 0;
            if(!*((u8*)w+0x2e0)){
                void* owner=*(void**)((u8*)w+0x2c0);rt[0]=0;
                if(!h22_rtti_name(owner,rt,sizeof(rt))||!h25_str_contains(rt,"cLuxProp"))return 0;
            }
        }
    }
    return 1;
}
static float __attribute__((ms_abi)) s26hd_ray_hit(const void* body,const float* normal,i32 id,void* data,float t){
    S26HDHit* h=(S26HDHit*)data;
    if(t>=0.0f&&t<h->t){h->body=body;h->t=t;}
    return h->t;
}
static S26HDHit s26hd_ray(const float* a,const float* b){
    S26HDHit h={0,1.0f};
    if(!p_s26hdRay){void* n=ext_GetModuleHandleA("Newton.dll");if(n){p_s26hdRay=(S26HDRayCast)ext_GetProcAddress(n,"NewtonWorldRayCast");p_s26hdWake=(void (__attribute__((ms_abi)) *)(const void*,i32))ext_GetProcAddress(n,"NewtonBodySetFreezeState");}}
    if(p_s26hdRay&&g_h14NewtonWorld)p_s26hdRay(g_h14NewtonWorld,a,b,s26hd_ray_hit,&h,s26hd_ray_pre);
    static const void* reported[16];static u32 reports;
    if(h.body&&reports<16u){
        i32 seen=0;for(u32 i=0;i<reports;i++)if(reported[i]==h.body)seen=1;
        if(!seen){
            reported[reports++]=h.body;void* w=p_h14GetUserData?p_h14GetUserData(h.body):0;
            char rt[96]={0},name[96]={0},ort[96]={0};i32 active=-1,collide=-1,character=-1;u32 flags=0;void* owner=0;
            if(w&&h22_rtti_name(w,rt,sizeof(rt))&&h25_str_contains(rt,"cPhysicsBodyNewton")&&h20_mem_readable(w,0x2f0u)){
                const char* n=*(const char**)((u8*)w+0x10);if(n)h21_copy_ascii(n,name,sizeof(name));
                active=*((u8*)w+0xe4);collide=*((u8*)w+0x2e0);character=*((u8*)w+0x249);flags=*(u32*)((u8*)w+0x240);owner=*(void**)((u8*)w+0x2c0);h22_rtti_name(owner,ort,sizeof(ort));
            }
            ext_Log(">>> S26HF RAY BODY #%u raw %p wrapper %p type %s name %s active %d collide %d character %d flags %u owner %p owner-type %s fraction %.6f start %.3f %.3f %.3f end %.3f %.3f %.3f",reports,h.body,w,rt,name,active,collide,character,flags,owner,ort,h.t,a[0],a[1],a[2],b[0],b[1],b[2]);
        }
    }
    g_s26hfRayBody=h.body;g_s26hfRayT=h.t;return h;
}
static i32 s26hd_aim(i32 h,float* start,float* dir){
    if(!visual_pose_valid(h)||!g_h5754dAimValid[h]||!p2_xr_origin_set()||!p2_camera_obj())return 0;
    XrPosef p=g_h5754dAimPose[h];volatile float* o=p2_xr_origin();
    float x,y,z;tracking_delta_to_game(p.position.x-o[0],p.position.y-o[1],p.position.z-o[2],&x,&y,&z);
    float* camera=(float*)((u8*)p2_camera_obj()+0x10);start[0]=camera[0]+x;start[1]=camera[1]+y;start[2]=camera[2]+z;s26ch_bob_apply(p2_camera_obj(),start);
    float spread=*p2_hand_spread()-0.18f,reach=*p2_hand_reach()-0.40f,ox,oz;
    h5748o_tracking_horizontal_to_game(h==0?-spread:spread,reach,&ox,&oz);
    start[0]+=ox;start[1]+=*p2_hand_drop()+0.18f;start[2]+=oz;
    XrVector3f d=h5754d_q_rotate_vec(p.orientation,(XrVector3f){0,0,-1});
    tracking_vector_to_game_unscaled(d.x,d.y,d.z,&dir[0],&dir[1],&dir[2]);return h10_norm3(dir);
}
static void s26hd_beam(i32 hand,const float* a,const float* b,u32 kind){
    h10_copy_f(g_s26hdBeamStart[hand],a,3);h10_copy_f(g_s26hdBeamEnd[hand],b,3);
    g_s26hdBeamKind[hand]=kind;g_s26hdBeamStep[hand]=g_h14PhysicsSteps;
}
static i32 s26hd_target(const void* body,void** wrapper,void** owner,i32* icon,void** on){
    g_s26hfTargetResult=1;g_s26hfIcon=-1;
    void* can=0;u32 off=0;char rt[96];const void* raw=0;
    if(!body||body==g_h14GripBody[0]||body==g_h14GripBody[1]||body==g_s26ckPadBody||body==g_s26xPhoneRaw)return 0;
    if(!h25_resolve_native_target(body,wrapper,owner,&can,on,&off,rt,sizeof(rt))||!h25_str_contains(rt,"cLuxProp"))return 0;
    /* Handheld CanInteract can reject this probe without altering its ordinary
       physical pickup or touch eligibility. Restore the scoped flag always. */
    g_s26hfTargetResult=2;
    u32 was=g_s26hdRemoteEntry;g_s26hdRemoteEntry=1;
    i32 ok=h483_surface_target_info(*wrapper,*owner,icon,&raw,&can,on)&&raw==body;
    g_s26hdRemoteEntry=was;g_s26hfTargetResult=ok?3:2;g_s26hfIcon=*icon;return ok;
}
/* Only a previously acquired and explicitly dropped carrier can bypass the
   desktop interaction icon. No OnInteract, detach or inventory mutation here. */
static i32 s26hj_dropped_owned(const void* body,void** wrapper,void** owner){
    if(!body||body==g_h14GripBody[0]||body==g_h14GripBody[1]||body==g_s26xPhoneRaw||body==g_s26ckPadBody||
       g_h576mScriptRuntimePublished!=1||g_h576bfMapTransitionActive||g_s26CutsceneHandsHidden||g_s26ManualHeal)return 0;
    void* expected=0;
    if(body==g_h576bOmniBody){
        if(g_h576bOmniState!=H576B_OMNI_LOOSE||!g_h576cCanonicalEntityName[0]||
           g_h576dDockReleasePending||g_h576dDockReleaseActive||g_h576eBindPending||
           g_h576bCaptureNextInteract||g_h576aoOmniHidePending)return 0;
        expected=g_h576bOmniOwner;
    }else{
        H576AAInvItem* it=h576aa_inv_find_body(body);
        if(!it||it->stowed||!it->remoteDropped||!it->logical[0])return 0;
        expected=it->owner;
    }
    void* can=0,*on=0;u32 off=0;char rt[96];
    if(!expected||!h25_resolve_native_target(body,wrapper,owner,&can,&on,&off,rt,sizeof(rt))||
       *owner!=expected||!h25_str_contains(rt,"cLuxProp")||!h37_native_wrapper_matches_entity(*wrapper,*owner)||
       !h20_mem_readable(*wrapper,0x2f0u))return 0;
    /* Active, colliding, exact current Newton body; hidden/parked carriers fail. */
    return *(const void**)((u8*)*wrapper+0x2e8)==body&&*((u8*)*wrapper+0xe4)&&*((u8*)*wrapper+0x2e0);
}
/* Read-only topology proof. No cache publication or acquisition side effects.
   All connected bodies must be dynamic, same-owner, unheld and <=25 kg total.
   Limits fail closed; world anchors and foreign/unknown joints are excluded. */
typedef struct {const void* body[32];u32 count;float mass;} S26HLAssembly;
static i32 s26hl_assembly(const void* start,void* owner,S26HLAssembly* a){
    zero_bytes(a,sizeof(*a));a->body[a->count++]=start;
    for(u32 i=0;i<a->count;i++){
        const void* b=a->body[i];
        if(b==g_h14GripBody[0]||b==g_h14GripBody[1]||h482_body_owner(b,0)!=owner)return 0;
        float mass,x,y,z;p_h14GetMass(b,&mass,&x,&y,&z);
        if(!(mass>.001f)||!(a->mass+mass<=25.0f))return 0;a->mass+=mass;
        const void* j=p_h14GetFirstJoint(b);u32 steps=0;
        while(j){
            if(++steps>32||!p_h14GetNextJoint||!p_h15JointGetBody0||!p_h15JointGetBody1||!p_h21JointGetUserData)return 0;
            const void* b0=p_h15JointGetBody0(j),*b1=p_h15JointGetBody1(j);
            if(b0!=b&&b1!=b)return 0;const void* other=b0==b?b1:b0;
            char rt[96]={0};void* jw=p_h21JointGetUserData(j);
            if(!other||!jw||!h22_rtti_name(jw,rt,sizeof(rt))||(!h25_str_contains(rt,"JointHinge")&&!h25_str_contains(rt,"JointBall")))return 0;
            i32 seen=0;for(u32 k=0;k<a->count;k++)if(a->body[k]==other)seen=1;
            if(!seen){if(a->count>=32)return 0;a->body[a->count++]=other;}
            j=p_h14GetNextJoint(b,j);
        }
    }return 1;
}
static i32 s26hl_same_free_prop(const void* target,const void* hit,void* owner){
    if(!hit||target==hit)return 1;
    S26HLAssembly a;if(!s26hl_assembly(target,owner,&a))return 0;
    for(u32 i=0;i<a.count;i++)if(a.body[i]==hit)return 1;return 0;
}
static i32 s26hd_loose(const void* body,void** wrapper,void** owner,float* mass){
    i32 icon=-1;void* on=0,*mo=0;
    if(!p_s26hdWake||!p_h14GetMass||!p_h14GetFirstJoint||!p_h14GetVelocity||!p_h14SetVelocity||!p_h14GetMatrix||!p_h14WorldAABB)return 0;
    if(!s26hj_dropped_owned(body,wrapper,owner)){
        if(body==g_h576bOmniBody||h576aa_inv_find_body(body))return 0;
        if(!s26hd_target(body,wrapper,owner,&icon,&on)||(icon!=H5755HL_CARRY_ONE_HANDED_ICON&&icon!=22))return 0;
    }
    if(h553_body_semantic_mechanism(body,&mo)!=H481_MECH_NONE)return 0;
    float ix,iy,iz;p_h14GetMass(body,mass,&ix,&iy,&iz);
    if(!p_h14GetFirstJoint(body)&&icon==22)return *mass>=0&&*mass<=25.0f;
    S26HLAssembly a;if(!s26hl_assembly(body,*owner,&a))return 0;
    *mass=a.mass;return 1;
}
static void __attribute__((ms_abi)) s26hd_find_live(const void* body,void* data){
    S26HDHit* hit=(S26HDHit*)data;if(body==hit->body)hit->t=1;
}
static i32 s26hd_live(S26HDPull* p,float metric){
    float a[3],b[3];for(i32 i=0;i<3;i++){a[i]=p->last[i]-metric;b[i]=p->last[i]+metric;}
    S26HDHit live={p->body,0};p_h14WorldAABB(g_h14NewtonWorld,a,b,s26hd_find_live,&live);
    return live.t>0&&p_h14GetUserData&&p_h14GetUserData(p->body)==p->wrapper&&h37_native_wrapper_matches_entity(p->wrapper,p->owner);
}

static i32 s26hl_interaction_target(void* w,void* o,void** on){
    char rt[96];i32 icon=-1;const void* raw=0;void* can=0;
    if(!h22_rtti_name(o,rt,sizeof(rt))||(!h25_str_contains(rt,"cLuxProp")&&!h25_str_contains(rt,"cLuxAgent")))return 0;
    if(!h483_surface_target_info(w,o,&icon,&raw,&can,on))return 0;
    /* Discrete authored talk/datamine/examine only. Never remote-operate a
       socket, pickup, door, ladder, heal gesture or held phone/tablet. */
    return (icon==18||icon==20||icon==28)&&raw!=g_s26xPhoneRaw&&raw!=g_s26ckPadBody&&raw!=g_h14GripBody[0]&&raw!=g_h14GripBody[1];
}
static void s26hl_interaction_step(const u8* edge){
    if(!g_s26hlInteractionEnabled||!s26hd_free_state()||g_h30NativeMouseDown)return;
    PFN_H37_GetClosestEntity fn=0;void* helper=h37_map_helper(&fn);if(!helper||!fn)return;
    for(i32 h=0;h<2;h++){
        if(g_h14GripBody[h]||g_h25PendingValid[h]||g_s26hdPull[h].body||g_s26hdLaserHand==h)continue;
        float a[3],d[3],point[3],distance=0;void* w=0,*o=0,*on=0;
        if(!s26hd_aim(h,a,d)||!fn(helper,a,d,3.0f*h5755ea_world_units_per_meter(),0,1,&distance,&w,&o)||!s26hl_interaction_target(w,o,&on))continue;
        if(!(distance>=0&&distance<=3.0f*h5755ea_world_units_per_meter()))continue;
        for(i32 i=0;i<3;i++)point[i]=a[i]+d[i]*distance;
        s26hd_beam(h,a,point,3);
        if(edge[h]){
            S26HDPull* p=&g_s26hlInteraction[h];p->body=*(const void**)((u8*)w+0x2e8);p->wrapper=w;p->owner=o;
            float m[16];p_h14GetMatrix(p->body,m);h10_copy_f(p->last,m+12,3);h10_copy_f(g_s26hlInteractionPoint[h],point,3);
        }
    }
}

/* HG: bounded angular candidate selection. Source 2's selector compares aim
   alignment, distance and previous selection; these are independent HPL rules,
   not copied Source 2 constants. Eight shortlisted dynamic bodies maximum. */
typedef struct { const void* body[8];float score[8],a[3],d[3],range,metric;u32 count; } S26HGQuery;
static void __attribute__((ms_abi)) s26hg_candidate(const void* body,void* data){
    S26HGQuery* q=(S26HGQuery*)data;
    if(body==g_h34HandNewton[0]||body==g_h34HandNewton[1]||body==g_h14GripBody[0]||body==g_h14GripBody[1])return;
    float mass,ix,iy,iz;p_h14GetMass(body,&mass,&ix,&iy,&iz);
    if(!(mass>=0&&mass<=25.0f))return;
    float m[16],v[3];p_h14GetMatrix(body,m);
    for(i32 i=0;i<3;i++)v[i]=m[12+i]-q->a[i];
    float along=h10_dot(v,q->d),dist=h10_len3(v[0],v[1],v[2]);
    if(!(along>.10f*q->metric&&dist<=q->range+.25f*q->metric))return;
    float side2=dist*dist-along*along,width=.20f*q->metric+.35f*along;
    if(!(side2<=width*width))return;
    float score=side2/(along*along)+.02f*dist/q->range;
    u32 at=q->count;if(at>7)at=7;
    if(q->count==8&&score>=q->score[7])return;
    while(at&&score<q->score[at-1]){q->body[at]=q->body[at-1];q->score[at]=q->score[at-1];at--;}
    q->body[at]=body;q->score[at]=score;if(q->count<8)q->count++;
}
static i32 s26hg_visible(const void* body,const float* a,const float* d,float range,float metric,float slope,float* point,float* score,void** wrapper,void** owner){
    float mass;if(!s26hd_loose(body,wrapper,owner,&mass))return 0;
    float m[16],v[3],probe[3],gap;p_h14GetMatrix(body,m);
    for(i32 i=0;i<3;i++)v[i]=m[12+i]-a[i];
    float along=h10_dot(v,d);if(!(along>0))return 0;
    if(along>range)along=range;
    for(i32 i=0;i<3;i++)probe[i]=a[i]+d[i]*along;
    if(!h14_point_to_body(body,probe,&gap,point))return 0;
    for(i32 i=0;i<3;i++)v[i]=point[i]-a[i];
    float dist=h10_len3(v[0],v[1],v[2]);along=h10_dot(v,d);
    if(!(dist>=.18f*metric&&dist<=range&&along>0))return 0;
    float side2=dist*dist-along*along,width=.025f*metric+slope*along;
    if(!(side2<=width*width))return 0;
    S26HDHit hit=s26hd_ray(a,point);
    if(!s26hl_same_free_prop(body,hit.body,*owner))return 0;
    *score=side2/(along*along)+.02f*dist/range;return 1;
}
static const void* s26hg_select(i32 hand,const float* a,const float* d,float range,float metric,float dt,float* point,void** wrapper,void** owner){
    S26HDPull* old=&g_s26hgFocus[hand];float best=1e9f;const void* selected=0;
    if(!p_h14WorldAABB||!p_h14GetMass||!p_h14GetFirstJoint||!p_h14GetMatrix||!g_h14NewtonWorld)return 0;
    if(old->body&&s26hd_live(old,metric)&&s26hg_visible(old->body,a,d,range,metric,.40f,point,&best,wrapper,owner)&&*wrapper==old->wrapper&&*owner==old->owner){
        selected=old->body;best-=.008f;
    }
    g_s26hgScanAge[hand]+=dt>0&&dt<.1f?dt:.05f;
    if(g_s26hgScanAge[hand]<0){if(!selected)zero_bytes(old,sizeof(*old));return selected;}
    g_s26hgScanAge[hand]=-.05f;
    /* Exact aim gets an independent chance even in densely cluttered scenes. */
    float end[3];for(i32 i=0;i<3;i++)end[i]=a[i]+d[i]*range;
    S26HDHit direct=s26hd_ray(a,end);
    S26HGQuery q;zero_bytes(&q,sizeof(q));q.range=range;q.metric=metric;
    h10_copy_f(q.a,a,3);h10_copy_f(q.d,d,3);
    float lo[3],hi[3],pad=.20f*metric+.35f*range;
    for(i32 i=0;i<3;i++){lo[i]=(a[i]<end[i]?a[i]:end[i])-pad;hi[i]=(a[i]>end[i]?a[i]:end[i])+pad;}
    p_h14WorldAABB(g_h14NewtonWorld,lo,hi,s26hg_candidate,&q);
    for(u32 i=0;i<=q.count;i++){
        const void* body=i==q.count?direct.body:q.body[i];if(!body||body==selected)continue;
        float cp[3],score;void* w=0,*o=0;
        if(!s26hg_visible(body,a,d,range,metric,.30f,cp,&score,&w,&o)||score>=best)continue;
        best=score;selected=body;*wrapper=w;*owner=o;h10_copy_f(point,cp,3);
    }
    zero_bytes(old,sizeof(*old));
    if(selected){float m[16];p_h14GetMatrix(selected,m);old->body=selected;old->wrapper=*wrapper;old->owner=*owner;h10_copy_f(old->last,m+12,3);}
    return selected;
}
/* Velocity-only servo. Faster cruise with a near-hand brake; acceleration is
   expressed per second so 60/120 Hz retain the same physical response. */
static void s26hg_pull_velocity(float* v,const float* gc,const float* cp,float metric,float dt){
    float delta[3],distance=h10_len3(gc[0]-cp[0],gc[1]-cp[1],gc[2]-cp[2]);
    float speed=distance*14.0f;if(speed>4.5f*metric)speed=4.5f*metric;
    for(i32 i=0;i<3;i++)delta[i]=(distance>.0001f?(gc[i]-cp[i])*speed/distance:0)-v[i];
    float dv=h10_len3(delta[0],delta[1],delta[2]),cap=30.0f*metric*dt;
    for(i32 i=0;i<3;i++)v[i]+=delta[i]*(dv>cap?cap/dv:1.0f);
}

/* Observation only: bounded one-line outcomes, no changes to pull policy. */
static u32 g_s26hnOutcomes;
static char g_s26hnName[2][96];
static void s26hn_outcome(i32 hand,const char* reason,float gap,const void* blocker){
    S26HDPull* p=&g_s26hdPull[hand];
    if(!g_s26hdRemoteEnabled||!p->body||g_s26hnOutcomes>=48u)return;
    char blockName[96]={0};void* w=blocker&&p_h14GetUserData?p_h14GetUserData(blocker):0;
    if(w&&h20_mem_readable(w,0x2f0u)&&*(const void**)((u8*)w+0x2e8)==blocker){
        const char* name=*(const char**)((u8*)w+0x10);if(name)h21_copy_ascii(name,blockName,sizeof(blockName));
    }
    g_s26hnOutcomes++;
    ext_Log(">>> S26HN REMOTE OUTCOME #%u hand %d name %s reason %s age %.3f gap %.4f readStage %u raw %p blocker %p blockerName %s held %p pending %u nativeBusy %d state %s",
       g_s26hnOutcomes,hand,g_s26hnName[hand],reason,p->age,gap,g_s26hlReadStage[hand],p->body,blocker,blockName,g_h14GripBody[hand],g_h25PendingValid[hand],s26hk_remote_native_busy(),g_h5729LastClassName);
}
static void s26hd_grab(i32 hand,const float* handM,const void* scanPtr,i32 edge,i32 pressed,float dt){
    g_s26hlHeld[hand]=(u8)pressed;
    if(!g_s26hdPull[hand].body){g_s26hlReadStage[hand]=0;g_s26hlReadId[hand]=0;}
    zero_bytes(&g_s26heOutline[hand],sizeof(g_s26heOutline[hand]));
    S26HDPull* p=&g_s26hdPull[hand];const H14Scan* scan=(const H14Scan*)scanPtr;
    float metric=h5755ea_world_units_per_meter();
    if(!g_s26hdRemoteEnabled||!p2_xr_running()||!s26hk_remote_state()||g_s26CutsceneHandsHidden||!visual_pose_valid(hand)||g_h14GripBody[hand]||s26hk_remote_native_busy()||g_h25PendingValid[hand]||g_s26hdLaserHand==hand||h5730_exact_terminal_state(0,0,0,0)){
        s26hn_outcome(hand,"state/input ownership",-1,0);zero_bytes(p,sizeof(*p));zero_bytes(&g_s26hgFocus[hand],sizeof(g_s26hgFocus[hand]));g_s26hdHover[hand]=0;return;
    }
    if(p->body){
        if(g_s26hlReadStage[hand]==1)return;
        if(!pressed||!(dt>0&&dt<0.1f)||p->age>3.0f||!s26hd_live(p,metric)){s26hn_outcome(hand,!pressed?"grip released":(!(dt>0&&dt<0.1f)?"invalid timestep":(p->age>3.0f?"timeout":"body lifetime")),-1,0);zero_bytes(p,sizeof(*p));return;}
        void* wrapper=0,*owner=0;float mass=0;
        if(!s26hd_loose(p->body,&wrapper,&owner,&mass)||wrapper!=p->wrapper||owner!=p->owner){s26hn_outcome(hand,"eligibility changed",-1,0);zero_bytes(p,sizeof(*p));return;}
        p->age+=dt;float gc[3],cp[3],gap,bm[16];
        // Only an already-authorized remote pull uses the validated interior
        // result. An interior catch point has zero gap, not a failed query.
        // Ordinary contact selection and hand collision helpers are unchanged.
        if(!h15_grip_center_world(hand,handM,gc)||!s26eq_return_point(p->body,gc,&gap,cp)){s26hn_outcome(hand,"closest point failed",-1,0);zero_bytes(p,sizeof(*p));return;}
        p_h14GetMatrix(p->body,bm);h10_copy_f(p->last,bm+12,3);
        S26HDHit path=s26hd_ray(gc,cp);
        if(!s26hl_same_free_prop(p->body,path.body,p->owner)){s26hn_outcome(hand,"obstructed",gap,path.body);zero_bytes(p,sizeof(*p));return;}
        s26hd_beam(hand,gc,cp,1);
        /* Only the previously selected body can complete this delayed pickup.
           Existing contact eligibility, callbacks and grab solver own handoff. */
        if(gap<0.08f*metric&&h560_try_loose_latch(hand,p->body,scan,handM,0)){s26hn_outcome(hand,"caught",gap,0);zero_bytes(p,sizeof(*p));return;}
        s26he_nominate(hand,p->body,wrapper,owner);
        float v[4]={0};p_h14GetVelocity(p->body,v);
        s26hg_pull_velocity(v,gc,cp,metric,dt);
        S26HLAssembly assembly;if(!s26hl_assembly(p->body,p->owner,&assembly)){s26hn_outcome(hand,"assembly changed",gap,0);zero_bytes(p,sizeof(*p));return;}
        float original[4]={0};p_h14GetVelocity(p->body,original);
        for(u32 k=0;k<assembly.count;k++){
            float velocity[4]={0};p_h14GetVelocity(assembly.body[k],velocity);
            for(i32 i=0;i<3;i++)velocity[i]+=v[i]-original[i];
            p_h14SetVelocity(assembly.body[k],velocity);
        }return;
    }
    if(pressed&&!edge)return;
    float a[3],d[3],b[3];if(!s26hd_aim(hand,a,d))return;
    float range=(1.0f+0.5f*(float)g_s26hdRemoteRange)*metric;
    void* wrapper=0,*owner=0;
    const void* selected=s26hg_select(hand,a,d,range,metric,edge?.05f:dt,b,&wrapper,&owner);
    if(!selected){g_s26hdHover[hand]=0;return;}
    S26HDHit hit={selected,0};
    s26hd_beam(hand,a,b,1);
    if(g_s26hdHover[hand]!=hit.body)h576ac_queue_haptic(hand,H576AC_HAPTIC_READY);
    g_s26hdHover[hand]=hit.body;
    s26he_nominate(hand,hit.body,wrapper,owner);
    if(!edge||g_s26hdPull[1-hand].owner==owner)return;
    p->body=hit.body;p->wrapper=wrapper;p->owner=owner;p->age=0;
    g_s26hnName[hand][0]=0;
    if(h20_mem_readable(wrapper,0x18u)){const char* name=*(const char**)((u8*)wrapper+0x10);if(name)h21_copy_ascii(name,g_s26hnName[hand],sizeof(g_s26hnName[hand]));}
    i32 icon=-1;void* on=0;void* w=0,*o=0;
    if(s26hd_target(hit.body,&w,&o,&icon,&on)&&icon==22){
        g_s26hlReadStage[hand]=1;h10_copy_f(g_s26hlReadPoint[hand],b,3);
    }
    p_s26hdWake(hit.body,0); // Wake once; never disable automatic sleep.
    float bm[16];p_h14GetMatrix(hit.body,bm);h10_copy_f(p->last,bm+12,3);
}
/* Native readable callbacks run outside NewtonUpdate, once per fresh grip.
   The actual published read body is verified again before the pull starts. */
static void s26hl_dispatch(void){
    for(i32 h=0;h<2;h++){
        S26HDPull p=g_s26hlInteraction[h];zero_bytes(&g_s26hlInteraction[h],sizeof(p));
        if(!p.body||!g_s26hlInteractionEnabled||!s26hd_free_state()||g_h30NativeMouseDown||g_h14GripBody[h]||g_h25PendingValid[h]||g_s26CutsceneHandsHidden||h5754h_pause_active()||g_h576bfMapTransitionActive)continue;
        void* on=0;if(!s26hd_live(&p,h5755ea_world_units_per_meter())||!s26hl_interaction_target(p.wrapper,p.owner,&on))continue;
        float a[3],d[3];if(!s26hd_aim(h,a,d))continue;
        S26HDHit hit=s26hd_ray(a,g_s26hlInteractionPoint[h]);
        if(hit.body&&hit.body!=p.body)continue;
        H25TString empty;zero_bytes(&empty,sizeof(empty));empty.capacity=15;
        u64 ok=((PFN_H25_OnInteract)on)(p.owner,0,p.wrapper,g_s26hlInteractionPoint[h],&empty);
        if(ok&255u)h576ac_queue_haptic(h,H576AC_HAPTIC_CONFIRM);
    }

    for(i32 h=0;h<2;h++){
        if(g_s26hlReadStage[h]!=1)continue;
        g_s26hlReadStage[h]=0;S26HDPull* p=&g_s26hdPull[h];
        if(!g_s26hdRemoteEnabled||!g_s26hlHeld[h]||g_h14GripBody[h]||g_h25PendingValid[h]||!s26hk_remote_state()||s26hk_remote_native_busy()||g_s26CutsceneHandsHidden||h5754h_pause_active()||g_h576bfMapTransitionActive){zero_bytes(p,sizeof(*p));continue;}
        void* w=0,*o=0,*on=0;i32 icon=-1;
        if(!p->body||!s26hd_live(p,h5755ea_world_units_per_meter())||!s26hd_target(p->body,&w,&o,&icon,&on)||w!=p->wrapper||o!=p->owner||icon!=22){zero_bytes(p,sizeof(*p));continue;}
        float a[3],d[3],point[3],score;void* w2=0,*o2=0;
        if(!s26hd_aim(h,a,d)||!s26hg_visible(p->body,a,d,(1.0f+.5f*g_s26hdRemoteRange)*h5755ea_world_units_per_meter(),h5755ea_world_units_per_meter(),.40f,point,&score,&w2,&o2)){zero_bytes(p,sizeof(*p));continue;}
        H25TString empty;zero_bytes(&empty,sizeof(empty));empty.capacity=15;
        i32 oldHand=g_h576avActiveInteractHand;const void* oldBody=g_h576avActiveInteractBody;
        g_h576avActiveInteractHand=h;g_h576avActiveInteractBody=p->body;g_s26hlReadScope=1;g_s26bvReadableWrapper=0;
        u64 ok=((PFN_H25_OnInteract)on)(o,0,w,point,&empty);
        g_s26hlReadScope=0;g_h576avActiveInteractHand=oldHand;g_h576avActiveInteractBody=oldBody;
        if(!(ok&255u)||!g_s26bvReadableWrapper||!h20_mem_readable(g_s26bvReadableWrapper,0x2f0)){zero_bytes(p,sizeof(*p));continue;}
        const void* raw=*(const void**)((u8*)g_s26bvReadableWrapper+0x2e8);
        if(raw!=p->body||g_s26bvReadableWrapper!=w||!s26hd_live(p,h5755ea_world_units_per_meter())){zero_bytes(p,sizeof(*p));continue;}
        g_s26hlReadId[h]=*(u32*)((u8*)w+0x3c);g_s26hlReadStage[h]=2;
        p_s26hdWake(raw,0);
    }
}
static i32 s26hd_fixed_state(void){
    char module[192],name[128];
    return h5730_exact_terminal_state(module,sizeof(module),name,sizeof(name))&&h5720_streq(module,"player/PlayerState_Interact_Terminal.hps");
}
static i32 s26hd_screen_ray(const float* a,const float* d,float max,float* u,float* v,float* hit){
    if(!g_h576boTerminalSurfaceValid)return 0;
    const H576BOTerminalSurface* s=&g_h576boTerminalSurface;
    float denom=h10_dot(s->normal,d);if(h9_abs(denom)<0.0001f)return 0;
    float q[3];for(i32 i=0;i<3;i++)q[i]=s->p0[i]-a[i];
    float t=h10_dot(q,s->normal)/denom;if(!(t>0&&t<=max))return 0;
    for(i32 i=0;i<3;i++){hit[i]=a[i]+t*d[i];q[i]=hit[i]-s->p0[i];}
    float uu=h10_dot(s->uSpan,s->uSpan),vv=h10_dot(s->vSpan,s->vSpan),uv=h10_dot(s->uSpan,s->vSpan),det=uu*vv-uv*uv;
    if(det<0.0000000001f)return 0;
    float du=h10_dot(q,s->uSpan),dv=h10_dot(q,s->vSpan);*u=(du*vv-dv*uv)/det;*v=(dv*uu-du*uv)/det;
    if(*u<0||*u>1||*v<0||*v>1)return 0;
    S26HDHit block=s26hd_ray(a,hit);
    if(block.body&&g_s26hdFixedOwner){void* wrapper=0;void* owner=h482_body_owner(block.body,&wrapper);if(owner==g_s26hdFixedOwner)return 1;}
    /* Screen collider can sit slightly in front of the authored surface. */
    return p_s26hdRay&&(!block.body||(1.0f-block.t)*t<0.025f*h5755ea_world_units_per_meter());
}
static void s26hd_step(float dt){
    s26hf_diag();
    if(!g_s26hdRemoteEnabled&&!g_s26hdLaserEnabled&&!g_s26hlInteractionEnabled){s26hd_reset();return;}
    if(!p2_xr_running()||g_s26CutsceneHandsHidden||h5754h_pause_active()||g_h576bfMapTransitionActive){s26hd_reset();return;}
    u8 edge[2],down[2];for(i32 h=0;h<2;h++){down[h]=g_lastTriggerActive[h]&&g_lastTrigger[h]>.55f;edge[h]=down[h]&&!g_s26hdTriggerPrev[h];g_s26hdTriggerPrev[h]=down[h];}
    s26hl_interaction_step(edge);
    if(!g_s26hdLaserEnabled)return;
    i32 old=g_s26hdLaserHand;
    if(!s26hd_fixed_state()){
        if(old>=0){h576bo_release_pointer(1,"laser left fixed terminal");g_s26hdLaserHand=-1;}
        if(!s26hd_free_state())return;
        for(i32 h=0;h<2;h++){
            if(g_h14GripBody[h]||g_h30NativeMouseDown||g_s26hdPull[h].body||!visual_pose_valid(h))continue;
            float a[3],d[3],b[3];if(!s26hd_aim(h,a,d))continue;
            float range=3.0f*h5755ea_world_units_per_meter();for(i32 i=0;i<3;i++)b[i]=a[i]+d[i]*range;
            S26HDHit hit=s26hd_ray(a,b);i32 icon=-1;void* wrapper=0,*owner=0,*on=0;
            if(!s26hd_target(hit.body,&wrapper,&owner,&icon,&on)||icon!=H576BO_TERMINAL_ICON)continue;
            for(i32 i=0;i<3;i++)b[i]=a[i]+d[i]*range*hit.t;s26hd_beam(h,a,b,2);
            if(edge[h]){H25TString empty;zero_bytes(&empty,sizeof(empty));empty.capacity=15u;
                g_s26hdRemoteEntry=1;u64 ok=((PFN_H25_OnInteract)on)(owner,0,wrapper,b,&empty);g_s26hdRemoteEntry=0;
                if(ok&0xffu){g_s26hdFixedOwner=owner;g_s26hdLaserHand=h;g_h576boEntryHand=-1;h576ac_queue_haptic(h,H576AC_HAPTIC_CONFIRM);}return;
            }
        }return;
    }
    /* A physical touch owns the GUI until lifted; never enqueue a second down. */
    if(g_h576boPointerDown&&old<0)return;
    for(i32 h=0;h<2;h++){float u,v,p,r;if(h576bo_terminal_tip(h,&u,&v,&p,&r)>0&&u>=0&&u<=1&&v>=0&&v<=1&&h9_abs(p)-r<=H576BP_SURFACE_CAPTURE_M){
        if(old>=0)h576bo_release_pointer(1,"physical touch takes priority");g_s26hdLaserHand=-1;return;}}
    i32 first=old>=0?old:(g_h576boEntryHand>=0?g_h576boEntryHand:1);
    for(i32 j=0;j<2;j++){
        i32 h=j?1-first:first;if(old>=0&&g_h576boPointerDown&&h!=old)continue;
        if(g_h14GripBody[h]||!visual_pose_valid(h))continue;
        float a[3],d[3],hit[3],u,v;if(!s26hd_aim(h,a,d)||!s26hd_screen_ray(a,d,3.0f*h5755ea_world_units_per_meter(),&u,&v,hit))continue;
        g_s26hdLaserHand=h;g_h576boPointerHand=h;s26hd_beam(h,a,hit,2);
        if(!h576bo_push_motion(u,v))break;
        if(g_h576boPointerDown&&!down[h])h576bo_release_pointer(1,"laser trigger released");
        else if(!g_h576boPointerDown&&edge[h]){g_h576boPointerDown=1;if(!h576bo_push_button(1))g_h576boPointerDown=0;else h576ac_queue_haptic(h,H576AC_HAPTIC_CONFIRM);}
        return;
    }
    if(old>=0)h576bo_release_pointer(1,"laser lost screen");g_s26hdLaserHand=-1;
}

/* Filled terminal visuals: fixed triangle geometry, independent of driver
   GL line-width support. No blending, depth or world-render state changes. */
static u32 g_s26hiVao,g_s26hiVbo;
static i32 s26hi_build_visuals(void){
    if(g_s26hiVao&&g_s26hiVbo)return 1;
    PFN_GenVertexArraysH9 gv=p2_gen_vaos();PFN_BindVertexArrayH9 bv=p2_bind_vao();PFN_GenBuffersH9 gb=p2_gen_buffers();PFN_BindBufferH9 bb=p2_bind_buffer();PFN_BufferDataH9 bd=p2_buffer_data();PFN_VertexAttribPointerH9 at=p2_attrib_ptr();PFN_EnableVertexAttribArrayH9 en=p2_enable_attrib();
    if(!gv||!bv||!gb||!bb||!bd||!at||!en)return 0;
    H10Vert v[648];zero_bytes(v,sizeof(v));i32 n=0;
    /* Twelve-sided beam, z=0..1, radius=1. */
    for(i32 i=0;i<12;i++){
        float a=6.2831853f*i/12,b=6.2831853f*(i+1)/12;
        float x[4]={ext_Cosf(a),ext_Cosf(b),ext_Cosf(b),ext_Cosf(a)},y[4]={ext_Sinf(a),ext_Sinf(b),ext_Sinf(b),ext_Sinf(a)};
        const i32 ix[6]={0,1,2,0,2,3};
        for(i32 j=0;j<6;j++){i32 k=ix[j];v[n].f[0]=x[k];v[n].f[1]=y[k];v[n++].f[2]=k>1?1:0;}
    }
    /* Filled spherical cursor: 12 segments, 8 latitude bands, 576 vertices. */
    for(i32 band=0;band<8;band++)for(i32 i=0;i<12;i++){
        float lat[2]={-1.5707963f+3.1415926f*band/8,-1.5707963f+3.1415926f*(band+1)/8};
        float lon[2]={6.2831853f*i/12,6.2831853f*(i+1)/12};
        const i32 ix[6]={0,1,3,0,3,2};
        for(i32 j=0;j<6;j++){i32 k=ix[j],t=k/2,u=k%2;v[n].f[0]=ext_Cosf(lat[t])*ext_Cosf(lon[u]);v[n].f[1]=ext_Sinf(lat[t]);v[n++].f[2]=ext_Cosf(lat[t])*ext_Sinf(lon[u]);}
    }
    gv(1,&g_s26hiVao);gb(1,&g_s26hiVbo);if(!g_s26hiVao||!g_s26hiVbo)return 0;
    bv(g_s26hiVao);bb(0x8892u,g_s26hiVbo);bd(0x8892u,sizeof(v),v,0x88E4u);at(0,3,0x1406u,0,sizeof(H10Vert),0);en(0);bb(0x8892u,0);bv(0);return 1;
}
static void s26hi_solid(const float* m,i32 first,i32 count,float r,float g,float b){
    PFN_UseProgramH9 use=p2_use_program();PFN_BindVertexArrayH9 bind=p2_bind_vao();PFN_Uniform1iH9 u1=p2_uniform1i();PFN_Uniform3fH10 u3=p2_uniform3f();PFN_Uniform4fH10 u4=p2_uniform4f();PFN_UniformMatrix4fvH10 um=p2_uniform_matrix4fv();u32 prog=p2_hand_prog();
    if(!use||!bind||!u1||!u3||!u4||!um||!prog)return;
    float mvp[16];h10_matmul(p2_view_proj(),m,mvp);use(prog);um(p2_hand_model_loc(),1,0,m);um(p2_hand_mvp_loc(),1,0,mvp);u4(p2_hand_col_loc(),r,g,b,1);u1(p2_hand_hastex_loc(),0);u1(p2_hand_skinned_loc(),0);u3(p2_hand_pivot_loc(),0,0,0);bind(g_s26hiVao);ext_glDrawArrays(0x0004u,first,count);bind(0);use(0);
}
static void s26hd_draw(void){
    if((!g_s26hdLaserEnabled&&!g_s26hlInteractionEnabled)||g_s26CutsceneHandsHidden||g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||h5754h_pause_active())return;
    for(i32 h=0;h<2;h++){
        if(!((g_s26hdLaserEnabled&&g_s26hdBeamKind[h]==2u)||(g_s26hlInteractionEnabled&&g_s26hdBeamKind[h]==3u))||g_s26hdBeamStep[h]!=g_h14PhysicsSteps||!visual_pose_valid(h))continue;
        if(!s26hi_build_visuals())return;
        float m[16],d[3],side[3],up[3],metric=h5755ea_world_units_per_meter();
        for(i32 i=0;i<3;i++)d[i]=g_s26hdBeamEnd[h][i]-g_s26hdBeamStart[h][i];
        float len=h10_len3(d[0],d[1],d[2]);if(!(len>.001f))continue;
        for(i32 i=0;i<3;i++)d[i]/=len;
        if(h9_abs(d[1])<.9f){side[0]=d[2];side[1]=0;side[2]=-d[0];}else{side[0]=0;side[1]=-d[2];side[2]=d[1];}
        h10_norm3(side);up[0]=d[1]*side[2]-d[2]*side[1];up[1]=d[2]*side[0]-d[0]*side[2];up[2]=d[0]*side[1]-d[1]*side[0];
        h10_identity(m);for(i32 i=0;i<3;i++){m[i]=side[i]*.0025f*metric;m[4+i]=up[i]*.0025f*metric;m[8+i]=d[i]*len;m[12+i]=g_s26hdBeamStart[h][i];}
        u8 cull=ext_glIsEnabled(0x0B44u);if(cull)ext_glDisable(0x0B44u);
        s26hi_solid(m,0,72,.20f,.90f,1.0f);
        h10_identity(m);m[0]=m[5]=m[10]=.009f*metric;
        for(i32 i=0;i<3;i++)m[12+i]=g_s26hdBeamEnd[h][i]-d[i]*.006f*metric;
        s26hi_solid(m,72,576,.85f,1.0f,1.0f);
        if(cull)ext_glEnable(0x0B44u);
    }
}

/* Native AddEdgeGlowObject: Steam 0xAABF0, Epic/GOG 0xA8660.
   Both wrappers pass EffectHandler+0x190 to the same mesh-ID queue contract.
   Submitted at script PostUpdate, as required by native effect helpers. No
   permanent component/material modification and no GL-state changes here. */
static void s26he_submit_edge(void* entity){
    u8* soma=(u8*)ext_GetModuleHandleA(0);if(!soma||!entity)return;
    if(!h20_mem_readable(soma+H5716_LUX_GLOBAL_RVA,8))return;
    void* lux=*(void**)(soma+H5716_LUX_GLOBAL_RVA);
    if(!lux||!h20_mem_readable((u8*)lux+0xd0,8))return;
    void* effect=*(void**)((u8*)lux+0xd0);if(!effect||!h20_mem_readable(effect,0x290))return;
    u8* fn=soma+0xAABF0;
    static const u8 prefix[]={0x48,0x83,0xec,0x38,0xf3,0x0f,0x10,0x44,0x24,0x68,0xf3,0x0f,0x10,0x4c,0x24,0x60,0x48,0x81,0xc1,0x90,0x01,0x00,0x00};
    if(!h20_mem_executable(fn)||!h20_mem_readable(fn,sizeof(prefix)))return;
    for(u32 i=0;i<sizeof(prefix);i++)if(fn[i]!=prefix[i])return;
    /* w=2 tags only our remote selection for material-independent rim shading.
       Stock effects keep their original shader path. Native queue preserves RGBA. */
    const float color[4]={0.20f,0.75f,0.90f,2.0f};
    ((void (__attribute__((ms_abi)) *)(void*,void*,const float*,float,float,float))fn)(effect,entity,color,0.45f,0.30f,100.0f);
    g_s26hiOutlineCalls++;
}
static void s26he_outline_postupdate(void){
    g_s26hiOutlinePosts++;
    if(!g_s26hdRemoteEnabled||!p2_xr_running()||g_s26CutsceneHandsHidden||
       h5754h_pause_active()||g_h576bfMapTransitionActive||!s26hk_remote_state()||
       g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR)return;
    void* submitted=0;
    for(i32 h=0;h<2;h++){
        S26HDPull* p=&g_s26heOutline[h];
        if(p->body&&(u32)(g_h14PhysicsSteps-g_s26heOutlineStep[h])>1u)g_s26hiOutlinePhaseReject++;
        if(!p->body||(u32)(g_h14PhysicsSteps-g_s26heOutlineStep[h])>1u||!visual_pose_valid(h)||
           g_h14GripBody[h]||g_h25PendingValid[h]||s26hk_remote_native_busy()||g_s26hdLaserHand==h||
           p->owner==submitted)continue;
        if(!p_h14WorldAABB||!g_h14NewtonWorld||!s26hd_live(p,h5755ea_world_units_per_meter()))continue;
        s26he_submit_edge(p->owner);submitted=p->owner;
    }
}
