static u32 g_s26jbPokeStep[2],g_s26jbPokeFrame[2];
static i32 s26jb_poke_contiguous(i32 hand,i32 valid){
 i32 result=valid&&(u32)(g_h14PhysicsSteps-g_s26jbPokeStep[hand])==1u&&
     (u32)(g_frameCounter-g_s26jbPokeFrame[hand])<=2u;
 g_s26jbPokeStep[hand]=g_h14PhysicsSteps;g_s26jbPokeFrame[hand]=g_frameCounter;
 return result;
}
/* Registered world-button crossing only. No controller interpolation or body
   mutation. First ray hit must still be the exact registered native control;
   s26hr_control_contact remains the sole permission/debounce dispatcher. */
static i32 s26jb_world_sweep(i32 hand,i32 finger,i32 len,const float* tip,const float* delta,const float* dir){
 if(!g_s26yCount||!s26y_gate()||ni_native_input()||g_s26CutsceneHandsHidden||h5754h_pause_active()||g_lastSyncResult!=0)return 0;
 float metric=h5755ea_world_units_per_meter(),length2=h10_dot(delta,delta);
 if(!h9_good(metric,10)||metric<=0||!h9_good(length2,1)||length2<(.015f*metric)*(.015f*metric)||length2>(.15f*metric)*(.15f*metric))return 0;
 float length=ext_Sqrtf(length2),travel[3],start[4],end[4];
 for(i32 a=0;a<3;a++){travel[a]=delta[a]/length;start[a]=tip[a]-delta[a];end[a]=tip[a];}start[3]=end[3]=0;
 if(h10_dot(travel,dir)<.5f)return 0; // withdrawal and sideways swipes do not click
 S26HDHit hit=s26hd_ray(start,end);
 if(!hit.body||!h9_good(hit.t,1)||hit.t<=0||hit.t>=1)return 0;
 i32 slot=s26y_body_slot(hit.body);
 // The registry also contains non-pressable housings (R), to keep them from
 // being mistaken for paddles. End this finger's ray; never cast through it.
 if(slot<0||!g_s26yRocker[slot].active)return 0;
 void* wrapper=p_h14GetUserData(hit.body);if(!wrapper||!h20_mem_readable(wrapper,0x2f0u))return 0;
 void* owner=*(void**)((u8*)wrapper+0x2c0);if(!h37_native_wrapper_matches_entity(wrapper,owner))return 0;
 float radius=s26jb_finger_skin_radius(hand,finger,len),offset=length*hit.t-radius-.001f*metric;
 if(offset<0)return 0;
 float sample[3];for(i32 a=0;a<3;a++)sample[a]=start[a]+travel[a]*offset;
 i32 result=s26hr_control_contact(hand,wrapper,owner,sample,dir,len,radius);
 return result==2?0:result;
}

/* Store each eligible fingertip, since endpoint selection may fall back to the
   index after another fingertip has already crossed a thin switch. These are
   coordinates only, no cached engine identities. The caller's existing sample
   validity also fences world resets and changes of selected contact finger. */
static float g_s26jbCrossTip[2][5][3];
static u8 g_s26jbCrossValid[2][5];
static i32 s26jb_cross_fingers(i32 hand,i32 contiguous){
 float tip[5][3],delta[5][3],dir[5][3];i32 lengths[5],ready[5]={0};
 if(!g_s26yCount){for(i32 f=0;f<5;f++)g_s26jbCrossValid[hand][f]=0;return 0;}
 for(i32 f=0;f<5;f++){
  float (*pts)[3]=g_s26jbTouchPoints[hand][f];i32 len=g_s26jbTouchLengths[hand][f];
  if(!g_s26jbTouchValid[hand][f]||len<1||len>4||h10_raw_finger_input(hand,f)>H48_POKE_INDEX_CURL_MAX){g_s26jbCrossValid[hand][f]=0;continue;}
  lengths[f]=len;ready[f]=contiguous&&g_s26jbCrossValid[hand][f];
  for(i32 a=0;a<3;a++){
   tip[f][a]=pts[len][a];delta[f][a]=tip[f][a]-g_s26jbCrossTip[hand][f][a];
   dir[f][a]=pts[len][a]-pts[len-1][a];g_s26jbCrossTip[hand][f][a]=tip[f][a];
  }
  g_s26jbCrossValid[hand][f]=1;if(!h10_norm3(dir[f]))ready[f]=0;
 }
 const i32 order[5]={1,0,2,3,4};
 for(i32 k=0;k<5;k++){i32 f=order[k];if(ready[f]&&s26jb_world_sweep(hand,f,lengths[f],tip[f],delta[f],dir[f]))return 1;}
 return 0;
}
