/* One bounded initial-squeeze contact request, on the physics thread after
   Newton publishes CURRENT contacts. No synthetic input, broad-shell fallback,
   retries, retained body pointer, or solver/shape change. */
static u8 g_s26jbClosureLevel[2];
static void s26jb_closure_contact(const void* world,float dt){
 for(i32 hand=0;hand<2;++hand){
  i32 edge=g_h5755haGripEdgeStep[hand]==g_h14PhysicsSteps;
  if(!edge&&!g_s26jbClosure[hand].armed){g_s26jbClosureLevel[hand]=g_h545AppliedSqueezeLevel[hand];continue;}
  i32 transaction=g_h14GripBody[hand]||g_h25PendingValid[hand]||g_h25AttemptBody[hand]||
   (g_h30NativeMouseDown&&g_h30NativeUseHand==hand)||g_h5755haEdgeNativeActive[hand]||
   g_s26hdPull[hand].body||g_h576avThetaPendingHand==hand||
   (hand==1&&g_s26xPhonePending)||g_s26hdLaserHand==hand;
  i32 eligible=world&&!ni_native_input()&&!g_s26CutsceneHandsHidden&&!h5748_is_stump(hand)&&
   !g_h576bfMapTransitionActive&&!h5754h_pause_active()&&visual_pose_valid(hand)&&
   g_h34HandNewton[hand]&&!g_h532Dormant[hand]&&g_h532ArmState[hand]==2;
  if(eligible&&!transaction)eligible=h5755ha_exact_normal_state_now()||h5755gw_exact_grab_state_now();
  i32 closing=g_h545Pending[hand]||g_h545CandidateStable[hand]||
   g_h545AppliedSqueezeLevel[hand]>g_s26jbClosureLevel[hand]||
   h549_quantize_gesture_level(hand,0,clamp01(g_lastSqueeze[hand]))>g_h545AppliedSqueezeLevel[hand];
  g_s26jbClosureLevel[hand]=g_h545AppliedSqueezeLevel[hand];
  i32 contact=(g_h5755eiContactPropStep[hand]==g_h14PhysicsSteps&&g_h5755eiContactPropAge[hand]==0&&g_h5755eiContactPropCount[hand])||
   (g_h5755hjStaticContactStep[hand]==g_h14PhysicsSteps&&g_h5755hjStaticContactCount[hand]);
  if(!jb_closure_step(&g_s26jbClosure[hand],g_h14PhysicsSteps,dt,edge,eligible,
                     g_lastSqueezeActive[hand]&&g_lastSqueeze[hand]>.55f,transaction,closing,contact))continue;
  // Policy consumed first: denial cannot fall into a later held-grip retry.
  float hp[3],hm[16];if(!h14_hand_pose(hand,hp,hm))continue;
  g_s26jbContactRequestStep[hand]=g_h14PhysicsSteps;
  H14Scan scan;float scanM[16];
  if(!h558_build_authored_scan(hand,world,scanM,&scan))continue;
  if(h5755gz_try_exact_current_loose_contact(hand,&scan,hm,0))continue;
  if(s26db_queue_contact_cable(hand,hm))continue;
  if(s26da_queue_contact_item(hand,hm))continue;
  (void)s26cx_queue_contact_mechanism(hand,hm);
 }
}
