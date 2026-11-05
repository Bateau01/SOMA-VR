/* PRIVATE candidate: between-sample hit test, not hand interpolation. */
static i32 jb_world_sweep(i32 hand,i32 finger,i32 len,const float* tip,const float* delta,const float* dir){
 if(!g_s26yCount||!s26y_gate()||ni_native_input()||g_s26CutsceneHandsHidden||h5754h_pause_active()||g_lastSyncResult!=0)return 0;
 float metric=h5755ea_world_units_per_meter(),length2=h10_dot(delta,delta);
 if(!h9_good(metric,10)||metric<=0||!h9_good(length2,1)||length2<(.015f*metric)*(.015f*metric)||length2>(.15f*metric)*(.15f*metric))return 0;
 float length=ext_Sqrtf(length2),travel[3],start[4],end[4];
 for(i32 a=0;a<3;a++){travel[a]=delta[a]/length;start[a]=tip[a]-delta[a];end[a]=tip[a];}start[3]=end[3]=0;
 if(h10_dot(travel,dir)<.5f)return 0; // withdrawal and sideways swipes do not click
 S26HDHit hit=s26hd_ray(start,end);
 static i32 logs; if(logs++<24)ext_Log("JB_SWEEP_RAY distance %.6f body %p t %.6f",length,hit.body,hit.t);
 if(!hit.body||!h9_good(hit.t,1)||hit.t<=0||hit.t>=1||s26y_body_slot(hit.body)<0)return 0;
 void* wrapper=p_h14GetUserData(hit.body);if(!wrapper||!h20_mem_readable(wrapper,0x2f0u))return 0;
 void* owner=*(void**)((u8*)wrapper+0x2c0);if(!h37_native_wrapper_matches_entity(wrapper,owner))return 0;
 float radius=s26jb_finger_skin_radius(hand,finger,len),offset=length*hit.t-radius-.001f*metric;
 if(offset<0)return 0;
 float sample[3];for(i32 a=0;a<3;a++)sample[a]=start[a]+travel[a]*offset;
 ext_Log("JB_WORLD_SWEEP hit hand %d distance %.5f fraction %.5f",hand,length,hit.t);
 return s26hr_control_contact(hand,wrapper,owner,sample,dir,len,radius);
}
