/* FW: one per-step tracking snapshot for feedback and release. A confirmed
   same-body/same-slot gesture retains the existing 2 cm exit margin, plus
   at most 120 ms inside a 4 cm margin. This is release-time tolerance, never
   post-drop adoption. Ownership and eligibility are rechecked on every call. */
static i32 s26fu_shoulder_stow_ready(i32 hand,const void* body,i32 omni,i32 eligible){
    if(hand<0||hand>1)return 0;
    const void** armed=omni?g_h576aoOmniStowArmedBody:g_h576aoLeftStowArmedBody;
    u32* last=omni?g_h576aoOmniStowLastInsideStep:g_h576aoLeftStowLastInsideStep;
    i32 valid=eligible&&body&&g_h14GripBody[hand]==body&&g_h14GripBody[1-hand]!=body&&
        !g_h15GripJointed[hand]&&!g_h484ClusterGrip[hand];
    S26FWFrame* f=valid?s26fw_frame(hand):0;
    float r=omni?g_h576anOmniShoulderRadius:g_h576aaShoulderRadius;
    i32 inside=f?s26fz_frame_deposit(f,omni,r):0;
    i32 exitMargin=f?s26fz_frame_deposit(f,omni,r+0.02f):0;
    i32 graceMargin=f?s26fz_frame_deposit(f,omni,r+0.04f):0;
    i32 ready=s26fw_stow_update(&g_s26fwStow[hand],body,omni,g_s26fwNow,
        g_h14PhysicsSteps,g_h5745YawCaptures,f!=0,inside,exitMargin,graceMargin);
    armed[hand]=ready?body:0;last[hand]=ready?g_h14PhysicsSteps:0;return ready;
}
