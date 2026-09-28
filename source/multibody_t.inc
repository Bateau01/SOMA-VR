/* Connected assembly support. No mass, joint, transform, velocity or world
   collision mutation. Gravity ownership is shared across the two held bodies. */
typedef struct {const void* raw;void* wrapper;void* owner;u8 users,gravity;} S26TGravity;
static S26TGravity g_s26tGravity[128];
static float g_s26tSupportMass[2];
static u32 g_s26tHoldLogs;
static i32 s26t_original_gravity(const void* body,i32 observed){
    for(i32 i=0;i<128;++i)if(g_s26tGravity[i].users&&g_s26tGravity[i].raw==body)return g_s26tGravity[i].gravity;
    return observed;
}
static i32 s26t_same_assembly(const void* a,const void* b){
    if(!a||!b)return 0;if(a==b)return 1;
    i32 slot=-1;for(i32 i=0;i<2;++i)if(g_h29BodyState[i].active&&g_h29BodyState[i].body==a)slot=i;
    if(slot<0)return 0;
    for(i32 i=0;i<128;++i)if(g_s26tGravity[i].raw==b&&(g_s26tGravity[i].users&(1u<<slot)))return 1;
    return 0;
}
static i32 s26t_live(const S26TGravity* e){
    return e->wrapper&&h20_mem_readable((u8*)e->wrapper+0x2c0,0x30)&&
        *(void**)((u8*)e->wrapper+0x2c0)==e->owner&&*(const void**)((u8*)e->wrapper+0x2e8)==e->raw;
}
static void s26t_gravity_end(i32 slot){
    if(slot<0||slot>1)return;u8 bit=(u8)(1u<<slot);
    for(i32 i=0;i<128;++i){S26TGravity* e=&g_s26tGravity[i];if(!(e->users&bit))continue;e->users&=(u8)~bit;
        if(p_h29SetGravity&&s26t_live(e))p_h29SetGravity(e->wrapper,e->users?0:e->gravity);
        if(!e->users)zero_bytes(e,sizeof(*e));
    }g_s26tSupportMass[slot]=0;
}
static void s26t_gravity_begin(i32 slot,const void* body){
    if(slot<0||slot>1||!body||!p_h29GetGravity||!p_h29SetGravity)return;
    if(g_s26tProofBody!=body||g_s26tProofStep!=g_h14PhysicsSteps)return;
    void* owner=h482_body_owner(body,0);
    if(!h5755ho_cluster_cache_contains(owner,body)||g_h5755hoClusterCacheDyn<2u)return;
    s26t_gravity_end(slot);
    /* Capture the proven connected set before mutating any flags. */
    S26TGravity candidates[H5755HO_CLUSTER_CACHE_MAX];i32 count=0;
    for(u32 i=0;i<g_h5755hoClusterCacheCount;++i){
        const void* raw=g_h5755hoClusterCacheBody[i];void* wrapper=0;
        if(h482_body_owner(raw,&wrapper)!=owner)return;
        float mass=h482_body_mass(raw);if(mass<=.001f)continue;
        S26TGravity e={raw,wrapper,owner,0,0};if(!s26t_live(&e))return;
        candidates[count++]=e;
    }
    if(count<2)return;
    for(i32 k=0;k<count;++k){S26TGravity* c=&candidates[k];i32 found=-1;
        for(i32 i=0;i<128;++i)if(g_s26tGravity[i].users&&g_s26tGravity[i].raw==c->raw&&g_s26tGravity[i].wrapper==c->wrapper){found=i;break;}
        if(found<0){for(i32 i=0;i<128;++i)if(!g_s26tGravity[i].users){found=i;break;}if(found<0){s26t_gravity_end(slot);return;}
            g_s26tGravity[found]=*c;g_s26tGravity[found].gravity=(u8)(p_h29GetGravity(c->wrapper)&1u);
        }
        g_s26tGravity[found].users|=(u8)(1u<<slot);p_h29SetGravity(c->wrapper,0);
    }
    g_s26tSupportMass[slot]=g_h5755hoClusterCacheMass;
    if(g_s26tHoldLogs++<16u)ext_Log(">>> S26T connected holding support: %d dynamic bodies %.3f kg; static anchors %u retained; shared gravity ownership, mass/inertia unchanged",count,(double)g_s26tSupportMass[slot],g_h5755hoClusterCacheWorld);
}
static float s26t_support_mass(const void* body,float mass){
    for(i32 i=0;i<2;++i)if(g_h29BodyState[i].active&&g_h29BodyState[i].body==body){
        float total=g_s26tSupportMass[i];if(total>mass&&mass>.001f)return total<mass*4.0f?total:mass*4.0f;
    }
    return mass;
}
static void s26t_retire_support(i32 slot){
    s26t_gravity_end(slot);
    H29BodyState* st=&g_h29BodyState[slot];
    if(st->active&&st->wrapper&&h20_mem_readable((u8*)st->wrapper+0x2c0,0x30)&&
       *(const void**)((u8*)st->wrapper+0x2e8)==st->body&&h482_body_mass(st->body)>.001f)
        p_h29SetGravity(st->wrapper,0); /* Existing focused-body hold still owns this flag. */
}
/* Revalidate just the held graph at 10 Hz (native physics is 60 Hz). No world
   or entity enumeration. Lost fragments regain gravity within six ticks. */
static void s26t_gravity_tick(const void* body){
    i32 slot=-1;for(i32 i=0;i<2;++i)if(g_h29BodyState[i].active&&g_h29BodyState[i].body==body)slot=i;
    if(slot<0||g_s26tSupportMass[slot]<=0)return;
    S26TGravity probe={body,g_h29BodyState[slot].wrapper,0,0,0};
    if(!probe.wrapper||!h20_mem_readable((u8*)probe.wrapper+0x2c0,0x30)){s26t_gravity_end(slot);return;}
    probe.owner=*(void**)((u8*)probe.wrapper+0x2c0);
    if(!s26t_live(&probe)||h482_body_mass(body)<=.001f){s26t_gravity_end(slot);return;}
    static u32 last[2];if((u32)(g_h14PhysicsSteps-last[slot])<6u)return;last[slot]=g_h14PhysicsSteps;
    if(!h484_classify_compliant_cluster(slot,body,probe.owner)){s26t_retire_support(slot);return;}
    /* Only refresh ownership if membership changed; stable holds issue no setters. */
    u32 owned=0;int changed=0;
    for(i32 i=0;i<128;++i)if(g_s26tGravity[i].users&(1u<<slot)){
        ++owned;if(!s26t_live(&g_s26tGravity[i])||!h5755ho_cluster_cache_contains(probe.owner,g_s26tGravity[i].raw))changed=1;
    }
    if(owned!=g_h5755hoClusterCacheDyn)changed=1;
    if(changed)s26t_gravity_begin(slot,body);
    else g_s26tSupportMass[slot]=g_h5755hoClusterCacheMass;
}
