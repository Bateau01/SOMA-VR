#ifndef S26AN_CONTACT_DIAGNOSTICS
#define S26AN_CONTACT_DIAGNOSTICS 0
#endif
#if S26AN_CONTACT_DIAGNOSTICS
/* S26AC read-only, bounded contact recorder. No physics mutation or new hook.
   Existing post-solver traversal supplies live bodies; retained pointers are
   identifiers only and are never dereferenced on delayed log output.
   Per process/hand: <=36000 active free-hand samples, <=300 narrowphase queries,
   <=10 128-frame event histories, <=1 output record per physics step.
   No cap resets at recenter, body replacement or map change. */
#define S26AC_RING 128u
#define S26AC_SAMPLES 36000u
#define S26AC_QUERIES 300u
typedef struct {
    u32 servoMode;float targetOmega[3];
    u32 step,contacts,rollback,points,pending,applied,requested,clear,valid,reason;
    const void* handBody;const void* other;
    float pre[16],post[16],target[16],velocity[3],omega[3],targetVelocity[3];
    float point[3],normal[3],depth,queryNormal[3],lag,displacement;
    char name[80];
} S26ACFrame;
typedef struct {
    S26ACFrame live,ring[S26AC_RING],output[S26AC_RING];
    u32 samples,queries,cursor,count,remaining,outputIndex,events;
    u32 severeEvents,lagEvents,gestureEvents,onsetEvents,lastEventStep,lastRollback;
    u32 priorContact,enabled,normalEvents;
    const void* previousBody;
} S26ACTrace;
static S26ACTrace g_s26ac[2];
static void s26ac_copy(S26ACFrame* dst,const S26ACFrame* src){
    volatile u8* d=(volatile u8*)dst;const u8* s=(const u8*)src;
    for(u32 i=0;i<(u32)sizeof(*dst);++i)d[i]=s[i];
}
static void s26ac_post_before_guard(void){
    for(i32 h=0;h<2;++h){S26ACTrace* t=&g_s26ac[h];t->enabled=0;
        if(t->samples>=S26AC_SAMPLES||t->events>=10u)continue;
        const void* b=g_h34HandNewton[h];
        if(!b||g_h14GripBody[h]||!g_h538PreSolverValid[h]||g_h532Dormant[h]||g_h532ArmState[h]!=2||!g_h526TargetValid[h]||!p_h14GetMatrix||!p_h14GetVelocity||!p_h14GetOmega)continue;
        if(t->previousBody!=b){t->cursor=0;t->count=0;t->priorContact=0;t->previousBody=b;}
        S26ACFrame* f=&t->live;zero_bytes(f,sizeof(*f));f->depth=-1.0f;
        f->servoMode=g_s26afServoMode[h];h10_copy_f(f->targetOmega,g_h528TargetOmega[h],3);
        f->step=g_h14PhysicsSteps;f->handBody=b;f->valid=1;
        h10_copy_f(f->pre,g_h538PreSolverM[h],16);p_h14GetMatrix(b,f->post);
        h10_copy_f(f->target,g_h526Target[h],16);
        float v[4]={0},o[4]={0};p_h14GetVelocity(b,v);p_h14GetOmega(b,o);
        h10_copy_f(f->velocity,v,3);h10_copy_f(f->omega,o,3);h10_copy_f(f->targetVelocity,g_h528TargetVel[h],3);
        f->lag=h10_len3(f->target[12]-f->pre[12],f->target[13]-f->pre[13],f->target[14]-f->pre[14]);
        f->displacement=h10_len3(f->post[12]-f->pre[12],f->post[13]-f->pre[13],f->post[14]-f->pre[14]);
        f->pending=g_h545Pending[h];f->applied=(u32)g_h545AppliedSqueezeLevel[h]*4u+(u32)g_h545AppliedTriggerLevel[h];
        f->requested=(u32)g_h545PendingSqueezeLevel[h]*4u+(u32)g_h545PendingTriggerLevel[h];f->clear=g_h545NoContactSteps[h];
        t->samples++;t->enabled=1;
    }
}
static void s26ac_begin(i32 h){
    S26ACTrace* t=&g_s26ac[h];
    if(t->live.step!=g_h14PhysicsSteps||t->live.handBody!=g_h34HandNewton[h])t->enabled=0;
}
static void s26ac_contact(i32 h,const void* b,const void* other,const void* joint,i32 n){
    S26ACTrace* t=&g_s26ac[h];if(!t->enabled)return;S26ACFrame* f=&t->live;
    f->contacts+=(u32)n;if(f->other)return;f->other=other;
    void* wrapper=p_h14GetUserData?p_h14GetUserData(other):0;
    if(wrapper&&h20_mem_readable((u8*)wrapper+0x10,8)){
        const char* name=*(const char**)((u8*)wrapper+0x10);
        if(name&&h20_mem_readable(name,1))h21_copy_ascii(name,f->name,sizeof(f->name));
    }
    if(p_h567ContactFirst&&p_h567ContactMaterial&&p_h567ContactPosNormal){
        void* ct=p_h567ContactFirst(joint);void* material=ct?p_h567ContactMaterial(ct):0;
        if(material){p_h567ContactPosNormal(material,b,f->point,f->normal);f->points=1;}
    }
    /* One existing exact pair only; no broadphase/world search. Query measures
       overlap at the CURRENT pose (after safety rollback when one occurred).
       The four returned points need not include the deepest global contact. */
    if(t->queries<S26AC_QUERIES&&(f->step%12u==0u||g_h538GuardRollbacks[h]!=t->lastRollback)&&p_h504CollisionCollide&&p_h14GetCollision&&p_h14GetMatrix){
        const void* a=p_h14GetCollision(b);const void* c=p_h14GetCollision(other);
        if(a&&c){float bm[16],om[16],pt[12]={0},normal[12]={0},depth[4]={0};p_h14GetMatrix(b,bm);p_h14GetMatrix(other,om);
            t->queries++;i32 found=p_h504CollisionCollide(g_h14NewtonWorld,4,a,bm,c,om,pt,normal,depth,0);
            f->depth=0.0f;if(found>4)found=4;
            for(i32 i=0;i<found;++i)if(depth[i]>=f->depth&&depth[i]<10.0f){f->depth=depth[i];h10_copy_f(f->queryNormal,normal+i*3,3);}
        }
    }
}
static void s26ac_emit(i32 h,S26ACTrace* t){
    if(!t->remaining)return;S26ACFrame* f=&t->output[t->outputIndex++];t->remaining--;
    ext_Log(">>> S26AC CONTACT HISTORY %s event %u reason %u step %u hand %p other %p name '%s' pts %u rollback %u pending %u pose %u->%u clear %u lag %.4f delta %.4f | pre(%+.4f %+.4f %+.4f) post(%+.4f %+.4f %+.4f) target(%+.4f %+.4f %+.4f) | v(%+.3f %+.3f %+.3f) omega(%+.3f %+.3f %+.3f) targetV(%+.3f %+.3f %+.3f) | contact(%+.4f %+.4f %+.4f) normal(%+.3f %+.3f %+.3f) valid %u | pairDepthMax4 %.5f queryN(%+.3f %+.3f %+.3f) | basisX pre(%+.3f %+.3f %+.3f) target(%+.3f %+.3f %+.3f) basisY pre(%+.3f %+.3f %+.3f) target(%+.3f %+.3f %+.3f) | servoMode %u targetOmega(%+.3f %+.3f %+.3f)",
        h==0?"L":"R",t->events,f->reason,f->step,f->handBody,f->other,f->name,f->contacts,f->rollback,f->pending,f->applied,f->requested,f->clear,f->lag,f->displacement,
        f->pre[12],f->pre[13],f->pre[14],f->post[12],f->post[13],f->post[14],f->target[12],f->target[13],f->target[14],
        f->velocity[0],f->velocity[1],f->velocity[2],f->omega[0],f->omega[1],f->omega[2],f->targetVelocity[0],f->targetVelocity[1],f->targetVelocity[2],
        f->point[0],f->point[1],f->point[2],f->normal[0],f->normal[1],f->normal[2],f->points,f->depth,f->queryNormal[0],f->queryNormal[1],f->queryNormal[2],
        f->pre[0],f->pre[1],f->pre[2],f->target[0],f->target[1],f->target[2],f->pre[4],f->pre[5],f->pre[6],f->target[4],f->target[5],f->target[6],f->servoMode,f->targetOmega[0],f->targetOmega[1],f->targetOmega[2]);
}
static void s26ac_finish(i32 h){
    S26ACTrace* t=&g_s26ac[h];
    if(t->enabled){S26ACFrame* f=&t->live;f->rollback=g_h538GuardRollbacks[h]>=t->lastRollback?g_h538GuardRollbacks[h]-t->lastRollback:0;t->lastRollback=g_h538GuardRollbacks[h];
        S26ACFrame* prior=&t->ring[(t->cursor+S26AC_RING-1u)%S26AC_RING];
        i32 reversed=t->count&&prior->points&&f->points&&prior->other==f->other&&prior->normal[0]*f->normal[0]+prior->normal[1]*f->normal[1]+prior->normal[2]*f->normal[2]<-0.5f;
        s26ac_copy(&t->ring[t->cursor],f);t->cursor=(t->cursor+1u)%S26AC_RING;if(t->count<S26AC_RING)t->count++;
        u32 reason=0;
        if(t->events<10u){
            if(f->rollback&&t->severeEvents<4u){reason=1;t->severeEvents++;}
            else if(!t->remaining&&(u32)(f->step-t->lastEventStep)>=120u){
                if(reversed&&t->normalEvents<2u){reason=5;t->normalEvents++;}
                else if(f->contacts&&f->pending&&f->applied!=f->requested&&t->gestureEvents<2u){reason=2;t->gestureEvents++;}
                else if(f->contacts&&f->lag>0.08f&&t->lagEvents<2u){reason=3;t->lagEvents++;}
                else if(f->contacts&&!t->priorContact&&t->onsetEvents<2u){reason=4;t->onsetEvents++;}
            }
        }
        if(reason){t->events++;t->lastEventStep=f->step;t->remaining=t->count;t->outputIndex=0;
            for(u32 i=0;i<t->count;++i){s26ac_copy(&t->output[i],&t->ring[(t->cursor+S26AC_RING-t->count+i)%S26AC_RING]);t->output[i].reason=reason;}
        }
        t->priorContact=f->contacts;
    }
    s26ac_emit(h,t);t->enabled=0;
}

#else
static void s26ac_post_before_guard(void){}
static void s26ac_begin(i32 h){(void)h;}
static void s26ac_contact(i32 h,const void* b,const void* other,const void* joint,i32 n){(void)h;(void)b;(void)other;(void)joint;(void)n;}
static void s26ac_finish(i32 h){(void)h;}
#endif
