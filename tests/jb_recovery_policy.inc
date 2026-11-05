/* Private stalled-root detector. Positions/deltas supplied in physical metres.
   A positive result only requests clearance testing; it never authorizes a
   transform, a release, an inventory change, or bypassing a native restriction. */
typedef struct {float stalled,effort,cooldown;unsigned step;int valid;} JBRecoveryWatch;
static void jb_recovery_reset(JBRecoveryWatch* w){w->stalled=0;w->effort=0;w->valid=0;}
static int jb_recovery_observe(JBRecoveryWatch* w,unsigned step,float dt,int eligible,
                              float lag,float rootTravel,float requestedTravel,int ownsItem){
 if(!(dt>0&&dt<=.05f)||!eligible||!(lag>=0&&lag<2)||
    !(rootTravel>=0&&rootTravel<1)||!(requestedTravel>=0&&requestedTravel<1)){
  jb_recovery_reset(w);return 0;
 }
 if(w->cooldown>0){w->cooldown-=dt;jb_recovery_reset(w);return 0;}
 if(!w->valid||(unsigned)(step-w->step)!=1u){jb_recovery_reset(w);w->valid=1;w->step=step;return 0;}
 w->step=step;
 if(lag<.20f||rootTravel>.004f){w->stalled=0;w->effort=0;return 0;}
 w->stalled+=dt;w->effort+=requestedTravel;
 if(w->stalled<.80f||w->effort<.05f)return 0;
 w->cooldown=2.f;jb_recovery_reset(w);
 // Important held objects are never silently dropped by this policy.
 return ownsItem?2:1;
}
