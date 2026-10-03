/* S26ED: HEAD TAP FLASHLIGHT. Touching the top of the head with an empty hand
   toggles the native flashlight. The crown zone is measured in the headset's
   own frame (raw OpenXR metres, grip-pose origin), so it follows the head when
   looking down or tilting. Faces, ears, foreheads and reaches in front of the
   visor stay outside it. One toggle per touch: the hand must leave a slightly
   larger zone before it can fire again, and two touches are at least 0.6 s
   apart. Native Player.OnAction keeps its flashlight availability rules. */
#define S26ED_CROWN_UP_MIN    0.08f /* above the eye line */
#define S26ED_CROWN_UP_MAX    0.30f
#define S26ED_CROWN_FRONT_MAX 0.06f /* at most this far in front of the eyes */
#define S26ED_CROWN_BACK_MAX  0.20f
#define S26ED_CROWN_SIDE_MAX  0.13f
#define S26ED_CROWN_EXIT_PAD  0.05f
#define S26ED_TAP_COOLDOWN_NS 600000000LL
/* q: HMD orientation (x,y,z,w); d: hand minus eye midpoint. */
static i32 s26ed_crown_zone(const float q[4],const float d[3],float pad){
    float x=q[0],y=q[1],z=q[2],w=q[3];
    float n=x*x+y*y+z*z+w*w;if(!(n>0.81f&&n<1.21f))return 0;
    for(i32 k=0;k<3;++k)if(!(d[k]>-2.0f&&d[k]<2.0f))return 0;
    float right[3]={1.0f-2.0f*(y*y+z*z),2.0f*(x*y+w*z),2.0f*(x*z-w*y)};
    float up[3]={2.0f*(x*y-w*z),1.0f-2.0f*(x*x+z*z),2.0f*(y*z+w*x)};
    float back[3]={2.0f*(x*z+w*y),2.0f*(y*z-w*x),1.0f-2.0f*(x*x+y*y)};
    float u=d[0]*up[0]+d[1]*up[1]+d[2]*up[2];
    float b=d[0]*back[0]+d[1]*back[1]+d[2]*back[2];
    float s=d[0]*right[0]+d[1]*right[1]+d[2]*right[2];if(s<0.0f)s=-s;
    return u>=S26ED_CROWN_UP_MIN-pad&&u<=S26ED_CROWN_UP_MAX+pad&&
           b>=-S26ED_CROWN_FRONT_MAX-pad&&b<=S26ED_CROWN_BACK_MAX+pad&&
           s<=S26ED_CROWN_SIDE_MAX+pad;
}
typedef struct { u8 armed[2]; i64 lastFire; } S26EDTap;
/* One step for both hands. inside/near: zone tests without/with exit pad.
   eligible: tracked, empty hand. Returns the firing hand or -1. A hand that
   arrives in the zone while ineligible (holding something, untracked) only
   re-arms after leaving it, so dropping an item on your head never toggles. */
static i32 s26ed_tap_step(S26EDTap* t,const i32 inside[2],const i32 near[2],const i32 eligible[2],i64 now){
    i32 fire=-1;
    for(i32 h=0;h<2;++h){
        if(!near[h]){t->armed[h]=1;continue;}
        if(!inside[h]||!t->armed[h])continue;
        t->armed[h]=0;
        if(!eligible[h]||fire>=0)continue;
        if(t->lastFire&&now>0&&now-t->lastFire<S26ED_TAP_COOLDOWN_NS)continue;
        fire=h;
    }
    if(fire>=0)t->lastFire=now>0?now:1;
    return fire;
}
