/* Native reference: Soma.exe+558BC0, compound loop 558F5E..5591EA.
   Preserve child order, contact limit, matrices and native narrowphase. Only
   omit primitive pairs with disjoint Newton-calculated world bounds. No shape
   replacement, body mutation, contact-budget change or cross-step caching. */
typedef i32 (__attribute__((ms_abi)) *CTShapeCount)(void*);
typedef void* (__attribute__((ms_abi)) *CTShapeAt)(void*,i32);
typedef void (__attribute__((ms_abi)) *CTShapeBounds)(const void*,const float*,float*,float*);
static CTShapeBounds g_ctShapeBounds;
typedef void (__attribute__((ms_abi)) *CTShapeSupport)(const void*,const float*,float*);
typedef void (__attribute__((ms_abi)) *CTShapeInfo)(const void*,void*);
typedef i32 (__attribute__((ms_abi)) *CTNewtonVersion)(void);
static CTShapeSupport g_ctShapeSupport;
static CTShapeInfo g_ctShapeInfo;
typedef struct {void* shape;i32 ready;float lo[4],hi[4];} CTChildBounds;
static struct {void* shape;void* world;u32 step;i32 count;float matrix[16];CTChildBounds child[256];} g_ctQueryCache;

static i32 ct_valid_bounds(const float* lo,const float* hi){
    for(i32 k=0;k<3;k++)if(!h9_good(lo[k],100000.0f)||!h9_good(hi[k],100000.0f)||lo[k]>hi[k])return 0;
    return 1;
}
static void ct_transpose(const float* a,float* b){for(i32 r=0;r<4;r++)for(i32 c=0;c<4;c++)b[r*4+c]=a[c*4+r];}
/* Newton 2.36 CalculateAABB includes 0.125m broadphase padding per side.
   Use the actual convex support vertices for query rejection, not a guessed
   subtraction from those bounds. SupportVertex includes the collision offset.
   Unknown/nonconvex geometry and invalid results retain the native bounds. */
static void ct_query_bounds(const void* collision,const float* nm,float* lo,float* hi){
    if(g_ctShapeSupport&&g_ctShapeInfo){
        union {double align;u8 bytes[512];} info;
        zero_bytes(&info,sizeof(info));g_ctShapeInfo(collision,&info);
        i32 type=*(i32*)(info.bytes+64);
        if((type>=0&&type<=4)||type==6||type==8){
            i32 valid=1;
            for(i32 k=0;k<3;k++){
                float dir[4]={nm[k],nm[4+k],nm[8+k],0},v[4]={0,0,0,0};
                float len=h10_dot(dir,dir);
                if(!h9_good(len,10000.0f)||len<0.000001f){valid=0;break;}
                g_ctShapeSupport(collision,dir,v);
                hi[k]=dir[0]*v[0]+dir[1]*v[1]+dir[2]*v[2]+nm[12+k];
                for(i32 j=0;j<3;j++)dir[j]=-dir[j];
                g_ctShapeSupport(collision,dir,v);
                lo[k]=-h10_dot(dir,v)+nm[12+k];
            }
            if(valid&&ct_valid_bounds(lo,hi))return;
        }
    }
    g_ctShapeBounds(collision,nm,lo,hi);
}
static i32 ct_shape_children(void* shape,void** out,i32 capacity){
    /* Callers supply the same owned/validated HPL shapes that they previously
       passed directly to native CheckShapeCollision. Do not issue a Windows
       VirtualQuery syscall for every child of those already-live shapes. */
    if(!shape)return 0;
    if(*(i32*)((u8*)shape+0x1c)!=7){out[0]=shape;return 1;}
    void** vt=*(void***)shape;
    if(!vt||!vt[7]||!vt[8])return 0;
    i32 n=((CTShapeCount)vt[8])(shape);if(n<1||n>capacity)return 0;
    for(i32 i=0;i<n;i++){
        void* s=((CTShapeAt)vt[7])(shape,i);
        if(!s||*(i32*)((u8*)s+0x1c)==7||!*(void**)((u8*)s+0x110))return 0;
        out[i]=s;
    }
    return n;
}
static u8 ct_check_shape_collision(void* world,void* a,const float* am,void* b,const float* bm,void* data,i32 limit,u8 correct,i32 thread){
#ifdef S26CT_VERIFY_COMPOUND
    u64 queryStart=h5755eg_tick();
#endif
    if(!b||*(i32*)((u8*)b+0x1c)!=7||limit<1||limit>32||thread!=0)
        return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
    if(!g_ctShapeBounds){void* nd=ext_GetModuleHandleA("Newton.dll");if(nd){
        g_ctShapeBounds=(CTShapeBounds)ext_GetProcAddress(nd,"NewtonCollisionCalculateAABB");
        CTNewtonVersion version=(CTNewtonVersion)ext_GetProcAddress(nd,"NewtonWorldGetVersion");
        if(version&&version()==236){
            g_ctShapeSupport=(CTShapeSupport)ext_GetProcAddress(nd,"NewtonCollisionSupportVertex");
            g_ctShapeInfo=(CTShapeInfo)ext_GetProcAddress(nd,"NewtonCollisionGetInfo");
        }
    }}
    if(!g_ctShapeBounds)return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
    i32 fresh=g_ctQueryCache.shape!=b||g_ctQueryCache.world!=world||g_ctQueryCache.step!=g_h14PhysicsSteps;
    if(!fresh)for(i32 k=0;k<16;k++)if(g_ctQueryCache.matrix[k]!=bm[k]){fresh=1;break;}
    if(fresh){
        void* children[256];i32 n=ct_shape_children(b,children,256);
        if(n<8)return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
        g_ctQueryCache.shape=0;
        /* CU: retain child order, but do not compute bounds for children
           beyond the contact limit's early exit. Invalidate on every original
           cache-key change; no bound survives a physics step or matrix change. */
        for(i32 i=0;i<n;i++){
            CTChildBounds* c=&g_ctQueryCache.child[i];c->shape=children[i];c->ready=0;
        }
        g_ctQueryCache.shape=b;g_ctQueryCache.world=world;g_ctQueryCache.step=g_h14PhysicsSteps;g_ctQueryCache.count=n;
        h10_copy_f(g_ctQueryCache.matrix,bm,16);
    }
    void* ac[32];i32 na=ct_shape_children(a,ac,32);
    if(!na)return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
    float nm[16],bnm[16];ct_transpose(am,nm);ct_transpose(bm,bnm);
    H508CollideData* dst=(H508CollideData*)data;dst->count=0;
    for(i32 i=0;i<na&&dst->count<limit;i++){
      float lo[4],hi[4];
      ct_query_bounds(*(void**)((u8*)ac[i]+0x110),nm,lo,hi);
      if(!ct_valid_bounds(lo,hi))return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
      for(i32 j=0;j<g_ctQueryCache.count&&dst->count<limit;j++){
        CTChildBounds* c=&g_ctQueryCache.child[j];i32 disjoint=0;
        if(!c->ready){
            ct_query_bounds(*(void**)((u8*)c->shape+0x110),bnm,c->lo,c->hi);
            if(!ct_valid_bounds(c->lo,c->hi))return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
            c->ready=1;
        }
        for(i32 k=0;k<3;k++)if(lo[k]>c->hi[k]+0.002f||c->lo[k]>hi[k]+0.002f){disjoint=1;break;}
        if(disjoint)continue;
        H508CollideData part;zero_bytes(&part,sizeof(part));part.begin=dst->begin+dst->count;part.end=dst->end;part.cap=dst->cap;
        p_h508CheckShapeCollision(world,ac[i],am,c->shape,bm,&part,limit-dst->count,0,thread);
        if(part.count<0||part.count>limit-dst->count)return p_h508CheckShapeCollision(world,a,am,b,bm,data,limit,correct,thread);
        dst->count+=part.count;
      }
    }
    if(correct&&*((u8*)a+0x60))for(i32 i=0;i<dst->count;i++){
        H508Contact* c=dst->begin+i;float d[3]={c->point[0]-am[3],c->point[1]-am[7],c->point[2]-am[11]};
        if(h10_dot(d,c->normal)>0.0f)for(i32 k=0;k<3;k++)c->normal[k]=-c->normal[k];
    }
#ifdef S26CT_VERIFY_COMPOUND
    static u32 checks,mismatches,clearChecks,hitChecks;
    if((dst->count>0&&hitChecks<32u)||(dst->count==0&&clearChecks<8u)){
        u64 queryTime=h5755eg_tick()-queryStart,refStart=h5755eg_tick();
        H508Contact cp[32];H508CollideData ref;zero_bytes(&ref,sizeof(ref));ref.begin=cp;ref.end=cp+32;ref.cap=cp+32;
        u8 hit=p_h508CheckShapeCollision(world,a,am,b,bm,&ref,limit,correct,thread);i32 same=(ref.count==dst->count&&((hit!=0)==(dst->count!=0)));
        if(same)for(i32 i=0;i<ref.count;i++)for(i32 k=0;k<7;k++)if(h9_abs((&cp[i].point[0])[k]-(&dst->begin[i].point[0])[k])>0.00001f)same=0;
        u64 refTime=h5755eg_tick()-refStart;
        checks++;if(dst->count>0)hitChecks++;else clearChecks++;if(!same)mismatches++;
        ext_Log(">>> S26CT COMPOUND EQUIVALENCE %u: children %d contacts %d/%d same %d mismatches %u | optimized/reference %.3f/%.3f ms",checks,g_ctQueryCache.count,dst->count,ref.count,same,mismatches,h5755eg_ms(queryTime),h5755eg_ms(refTime));
        if(!same){for(i32 i=0;i<ref.count;i++)dst->begin[i]=cp[i];dst->count=ref.count;return hit;}
    }
#endif
    return dst->count>0?1:0;
}

/* Held articulation performs pure queries while the body and shape geometry
   are unchanged. Memoize only within an explicit synchronous solver scope;
   never retain answers across physics updates, releases, or map transitions.
   A hash collision is a miss unless every input bit and identity matches. */
typedef struct {
    u32 epoch,correct;
    void* world;void* a;void* b;
    float am[16],bm[16];
    H508Contact contact;
    i32 count;u8 hit;
} CTHeldQuery;
static CTHeldQuery g_ctHeldQueries[1024];
static u32 g_ctHeldEpoch,g_ctHeldScope;
#ifdef S26CT_VERIFY_COMPOUND
static u32 g_ctHeldHits,g_ctHeldMisses;
static u64 g_ctHeldQueryTicks;
#endif
static void ct_held_queries_begin(void){
    if(!g_ctHeldScope++){
        if(!++g_ctHeldEpoch){zero_bytes(g_ctHeldQueries,sizeof(g_ctHeldQueries));g_ctHeldEpoch=1;}
    }
}
static void ct_held_queries_end(void){if(g_ctHeldScope)g_ctHeldScope--;}
static u32 ct_query_hash(const void* a,const void* b,const float* am,const float* bm,u8 correct){
    u32 h=2166136261u;
    const u8* p=(const u8*)&a;for(u32 i=0;i<sizeof(a);i++)h=(h^p[i])*16777619u;
    p=(const u8*)&b;for(u32 i=0;i<sizeof(b);i++)h=(h^p[i])*16777619u;
    p=(const u8*)am;for(i32 i=0;i<64;i++)h=(h^p[i])*16777619u;
    p=(const u8*)bm;for(i32 i=0;i<64;i++)h=(h^p[i])*16777619u;
    return (h^correct)&1023u;
}
static i32 ct_matrix_bits_equal(const float* a,const float* b){
    const u8* ap=(const u8*)a;const u8* bp=(const u8*)b;
    for(i32 i=0;i<64;i++)if(ap[i]!=bp[i])return 0;return 1;
}
static u8 ct_held_shape_collision(void* world,void* a,const float* am,void* b,const float* bm,void* data,i32 limit,u8 correct,i32 thread){
    if(!g_ctHeldScope||limit!=1||thread!=0)return ct_check_shape_collision(world,a,am,b,bm,data,limit,correct,thread);
    CTHeldQuery* q=&g_ctHeldQueries[ct_query_hash(a,b,am,bm,correct)];H508CollideData* d=(H508CollideData*)data;
    if(q->epoch==g_ctHeldEpoch&&q->world==world&&q->a==a&&q->b==b&&q->correct==correct&&ct_matrix_bits_equal(q->am,am)&&ct_matrix_bits_equal(q->bm,bm)){
#ifdef S26CT_VERIFY_COMPOUND
        g_ctHeldHits++;
#endif
        d->count=q->count;if(q->count)d->begin[0]=q->contact;return q->hit;
    }
#ifdef S26CT_VERIFY_COMPOUND
    g_ctHeldMisses++;
    u64 queryStart=h5755eg_tick();
#endif
    u8 hit=ct_check_shape_collision(world,a,am,b,bm,data,limit,correct,thread);
#ifdef S26CT_VERIFY_COMPOUND
    g_ctHeldQueryTicks+=h5755eg_tick()-queryStart;
#endif
    if(d->count>=0&&d->count<=1){
        q->epoch=g_ctHeldEpoch;q->world=world;q->a=a;q->b=b;q->correct=correct;
        h10_copy_f(q->am,am,16);h10_copy_f(q->bm,bm,16);q->hit=hit;q->count=d->count;if(d->count)q->contact=d->begin[0];
    }
    return hit;
}
