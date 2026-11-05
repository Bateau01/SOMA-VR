/* Bounded free-hand recovery. Physics-thread, post-dispatch; no retained engine pointer.
   Only a free, persistently stalled hand can move, and only along a corridor
   clear in BOTH directions with a separately clear destination. Held objects
   and authored mechanisms are deferred, never released or transported.
   This deliberately cannot rescue every embedded/occluded hand. */
#include "hand_recovery_policy_jb.inc"
static i32 h5755ha_exact_normal_state_now(void);
static i32 h5755gw_exact_grab_state_now(void);
typedef struct {float point[4],normal[4],surface[4],depth;i32 id;const void* body;} JBRecoveryHit;
typedef u32 (__attribute__((ms_abi))*JBRecoveryFilter)(const void*,const void*,void*);
typedef i32 (__attribute__((ms_abi))*JBRecoveryCast)(const void*,const float*,const float*,const void*,float*,void*,JBRecoveryFilter,JBRecoveryHit*,i32,i32);
typedef void (__attribute__((ms_abi))*JBRecoveryBounds)(const void*,const float*,float*,float*);
static JBRecoveryCast jbRecoveryCast;
static JBRecoveryBounds jbRecoveryBounds;
typedef i32 (__attribute__((ms_abi))*JBRecoveryFaces)(const void*,const float*,const float*,const float**,i32*,i32*,i32*,i32,i32*);
static JBRecoveryFaces jbRecoveryFaces;
/* Supported Newton 2.x profile: collision kind at +0x68, local offset +0x10,
   tree debug callback +0x98. Already verified by the CPU55 native fixture;
   only exact kind9/identity-offset trees can use the exported empty-leaf test. */
static i32 jb_recovery_tree_empty(const void* body,const float* lo,const float* hi){
 // Broadphase leaves can include nearby bodies outside the query. Refine by
 // their current native collision bounds before considering shape-specific data.
 float bodyM[16],bodyLo[4],bodyHi[4];p_h14GetMatrix(body,bodyM);
 const void* bodyCollision=p_h14GetCollision(body);if(!bodyCollision)return 0;
 jbRecoveryBounds(bodyCollision,bodyM,bodyLo,bodyHi);
 i32 apart=0;for(i32 a=0;a<3;a++){
  if(!h9_good(bodyLo[a],100000)||!h9_good(bodyHi[a],100000)||bodyLo[a]>bodyHi[a])return 0;
  if(bodyHi[a]<lo[a]||bodyLo[a]>hi[a])apart=1;
 }
 if(apart)return 1;

 const u8* c=(const u8*)p_h14GetCollision(body);
 if(!c||!jbRecoveryFaces||!h20_mem_readable((void*)c,0xa0)||*(const u32*)(c+0x68)!=9||*(const void**)(c+0x98))return 0;
 const float* offset=(const float*)(c+0x10);
 for(i32 i=0;i<16;i++)if(!h9_good(offset[i],2)||(offset[i]-(i%5==0?1.f:0.f)>.00001f||offset[i]-(i%5==0?1.f:0.f)<-.00001f))return 0;
 float bm[16],inverse[16];p_h14GetMatrix(body,bm);h14_rigid_inverse(bm,inverse);
 float localLo[3]={1e20f,1e20f,1e20f},localHi[3]={-1e20f,-1e20f,-1e20f};
 for(i32 corner=0;corner<8;corner++){
  float wp[3],lp[3];for(i32 a=0;a<3;a++)wp[a]=(corner&(1<<a))?hi[a]:lo[a];
  h14_transform_point(inverse,wp,lp);
  for(i32 a=0;a<3;a++){if(!h9_good(lp[a],100000))return 0;if(lp[a]<localLo[a])localLo[a]=lp[a];if(lp[a]>localHi[a])localHi[a]=lp[a];}
 }
 const float* vertices=0;i32 count=0,stride=0,indices[96],attributes[96];
 i32 faces=jbRecoveryFaces(c,localLo,localHi,&vertices,&count,&stride,indices,96,attributes);
 if(faces==0)return 1;
 // The API returns triangles from intersected tree leaves, including nearby
 // triangles outside the box. A full output buffer is ambiguous: reject it.
 if(faces<0||faces>=32||!vertices||count<=0||count>1000000||stride!=12)return 0;
 for(i32 face=0;face<faces;face++){
  float a[3]={1e20f,1e20f,1e20f},b[3]={-1e20f,-1e20f,-1e20f};
  for(i32 v=0;v<3;v++){
   i32 index=indices[face*3+v];if(index<0||index>=count)return 0;
   const float* p=(const float*)((const u8*)vertices+(u32)index*(u32)stride);
   for(i32 k=0;k<3;k++){if(!h9_good(p[k],100000))return 0;if(p[k]<a[k])a[k]=p[k];if(p[k]>b[k])b[k]=p[k];}
  }
  i32 apart=0;for(i32 k=0;k<3;k++)if(b[k]<localLo[k]||a[k]>localHi[k])apart=1;
  if(!apart)return 0;
 }
 return 1;
}
static JBRecoveryWatch jbRecoveryWatch[2];
static float jbRecoveryPreviousRoot[2][3],jbRecoveryPreviousTarget[2][3],jbRecoveryScale[2];
static u32 jbRecoverySampleStep[2],jbRecoveryAttempts,jbRecoveryAccepted,jbRecoveryBlocked,jbRecoveryDeferred;
static i32 jb_recovery_reject(i32 stage,const void* body,float fraction,i32 count){return 0;}
static u32 __attribute__((ms_abi)) jb_recovery_filter(const void* body,const void* collision,void* user){
 (void)collision;i32 h=*(i32*)user;
 /* Match the existing hand-pair self registry: 1=camera, 2=character.
    These are already excluded from physical-hand contact, not new exemptions. */
 if(!body||body==g_h34HandNewton[h]||h530_self_body_kind(body)||h540_nonphysical_area_body(body))return 0;
 return 1; /* Other hand, held props and unknown solids remain obstacles. */
}
typedef struct{const void* bodies[256];i32 count,overflow,hand;} JBRecoveryNear;
static void __attribute__((ms_abi)) jb_recovery_near(const void* body,void* user){
 JBRecoveryNear*n=(JBRecoveryNear*)user;
 if(!jb_recovery_filter(body,0,&n->hand))return;
 if(n->count==256){n->overflow=1;return;}
 n->bodies[n->count++]=body;
}
static i32 jb_recovery_clear(i32 hand,const float* current,const float* target){
 if(!g_h14NewtonWorld||!p_h14GetCollision||!p_h14WorldAABB)return 0;
 if(!jbRecoveryCast||!jbRecoveryBounds||!jbRecoveryFaces){void* nd=ext_GetModuleHandleA("Newton.dll");if(!nd)return 0;
  jbRecoveryCast=(JBRecoveryCast)ext_GetProcAddress(nd,"NewtonWorldConvexCast");
  jbRecoveryBounds=(JBRecoveryBounds)ext_GetProcAddress(nd,"NewtonCollisionCalculateAABB");
  jbRecoveryFaces=(JBRecoveryFaces)ext_GetProcAddress(nd,"NewtonTreeCollisionGetVertexListIndexListInAABB");}
 if(!jbRecoveryCast||!jbRecoveryBounds)return 0;
 const void* collision=p_h14GetCollision(g_h34HandNewton[hand]);
 if(!collision)return 0;
 JBRecoveryHit hits[8];float fraction=1;
 i32 count=jbRecoveryCast(g_h14NewtonWorld,current,target+12,collision,&fraction,&hand,jb_recovery_filter,hits,8,0);
 if(count||!h9_good(fraction,2)||fraction<.99999f)return jb_recovery_reject(1,count>0?hits[0].body:0,fraction,count);
 fraction=1;count=jbRecoveryCast(g_h14NewtonWorld,target,current+12,collision,&fraction,&hand,jb_recovery_filter,hits,8,0);
 if(count||!h9_good(fraction,2)||fraction<.99999f)return jb_recovery_reject(2,count>0?hits[0].body:0,fraction,count);
 float lo[4],hi[4],startLo[4],startHi[4];jbRecoveryBounds(collision,target,lo,hi);jbRecoveryBounds(collision,current,startLo,startHi);
 for(i32 a=0;a<3;a++){if(!h9_good(startLo[a],100000)||!h9_good(startHi[a],100000)||startLo[a]>startHi[a])return 0;if(startLo[a]<lo[a])lo[a]=startLo[a];if(startHi[a]>hi[a])hi[a]=startHi[a];}
 for(i32 a=0;a<3;a++){if(!h9_good(lo[a],100000)||!h9_good(hi[a],100000)||lo[a]>hi[a])return 0;lo[a]-=.005f;hi[a]+=.005f;}
 JBRecoveryNear near;zero_bytes(&near,sizeof(near));near.hand=hand;
 p_h14WorldAABB(g_h14NewtonWorld,lo,hi,jb_recovery_near,&near);if(near.overflow)return jb_recovery_reject(3,0,0,near.count);
 /* Recovery is rare and optional. Reject EVERY other-body broadphase overlap
    at the destination, even when Newton reports no narrowphase contact.
    This deliberately sacrifices recovery beside close geometry rather than
    allowing a thin, contained or triangle-mesh obstacle to be missed. */
 for(i32 i=0;i<near.count;i++)if(!jb_recovery_tree_empty(near.bodies[i],lo,hi))return 0;
 return 1;
}
static void jb_recovery_clear_history(i32 h){if(h<0||h>1)return;zero_bytes(&jbRecoveryWatch[h],sizeof(jbRecoveryWatch[h]));jbRecoverySampleStep[h]=0;}
static void jb_recovery_tick(float dt){
 for(i32 h=0;h<2;h++){
  i32 eligible=!ni_native_input()&&g_lastSyncResult==0&&!g_s26CutsceneHandsHidden&&!h5748_is_stump(h)&&
   !g_h576bfMapTransitionActive&&!h5754h_pause_active()&&visual_pose_valid(h)&&
   g_h34HandNewton[h]&&g_h526TargetValid[h]&&g_h532ArmState[h]==2&&!g_h532Dormant[h]&&
   !g_h526CollisionDisabled[h]&&!g_h25PendingValid[h]&&!g_h25AttemptBody[h]&&
   !g_h5755haEdgeNativeActive[h]&&!g_h484CurtainAnchorValid[h]&&!g_s26hdPull[h].body&&
   g_h576avThetaPendingHand!=h&&!(h==1&&g_s26xPhonePending)&&g_s26hdLaserHand!=h&&
   !(g_h30NativeMouseDown&&g_h30NativeUseHand==h)&&!g_h550ReleaseIgnoreTicks[h]&&
   !g_s26bbWorldScalePercent&&!g_h5710ManualRebasePending&&!g_h545Pending[h]&&!g_h548GestureWarmupRootLock[h];
  if(!eligible){jb_recovery_reset(&jbRecoveryWatch[h]);jbRecoverySampleStep[h]=0;continue;}
  float m[16];p_h14GetMatrix(g_h34HandNewton[h],m);const float*t=g_h526Target[h];float scale=h5755ea_world_units_per_meter();
  i32 continuous=(u32)(g_h14PhysicsSteps-jbRecoverySampleStep[h])==1&&jbRecoveryScale[h]==scale;
  float lag=h10_len3(t[12]-m[12],t[13]-m[13],t[14]-m[14])/scale;
  if(lag>=.20f&&!(h5755ha_exact_normal_state_now()||h5755gw_exact_grab_state_now())){
   jb_recovery_reset(&jbRecoveryWatch[h]);jbRecoverySampleStep[h]=0;continue;
  }
  float travel=continuous?h10_len3(m[12]-jbRecoveryPreviousRoot[h][0],m[13]-jbRecoveryPreviousRoot[h][1],m[14]-jbRecoveryPreviousRoot[h][2])/scale:1;
  float effort=continuous?h10_len3(t[12]-jbRecoveryPreviousTarget[h][0],t[13]-jbRecoveryPreviousTarget[h][1],t[14]-jbRecoveryPreviousTarget[h][2])/scale:1;
  for(i32 a=0;a<3;a++){jbRecoveryPreviousRoot[h][a]=m[12+a];jbRecoveryPreviousTarget[h][a]=t[12+a];}
  jbRecoverySampleStep[h]=g_h14PhysicsSteps;jbRecoveryScale[h]=scale;
  /* Normalize detector's per-step root threshold to the native 60Hz rate. */
  i32 request=jb_recovery_observe(&jbRecoveryWatch[h],g_h14PhysicsSteps,dt,continuous,lag,dt>0?travel/(60.f*dt):1,effort,g_h14GripBody[h]!=0);
  if(request==2){jbRecoveryDeferred++;continue;}if(request!=1)continue;
  jbRecoveryAttempts++;
  float target[16];h10_copy_f(target,m,16);for(i32 a=0;a<3;a++)target[12+a]=t[12+a];
  if(!jb_recovery_clear(h,m,target)){jbRecoveryBlocked++;continue;}
  if(!h536_sync_managed_transform(h,target,"bounded free-hand recovery"))continue;
  float zero[4]={0,0,0,0};p_h14SetVelocity(g_h34HandNewton[h],zero);p_h14SetOmega(g_h34HandNewton[h],zero);
  g_h528PrevTargetValid[h]=g_h34PrevTargetValid[h]=g_h34FilterValid[h]=g_h511PrevRawValid[h]=0;
  h10_copy_f(g_h513SafeHand[h],target,16);h10_copy_f(g_h511RootSafeHand[h],target,16);g_h513SafeValid[h]=1;
  __atomic_store_n(&g_h5755deContactVisualActive[h],0u,__ATOMIC_RELEASE);
  jbRecoverySampleStep[h]=0;jbRecoveryAccepted++;
 }
}
