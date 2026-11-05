/* Isolated knob acquisition through ordinary grip; joint/body never moved by
   this observer. Synthetic controller samples are not a hardware comfort test. */
static i64 cpu6Start,cpu6Now;static u32 cpu6Phase=99,cpu6Done,cpu6PoseSeed;
static const void* jbMechanism;static XrQuaternionf jbInitialQ;
static float jbPin[3],jbPivot[3],jbContact[3],jbStartBody[16];
static u32 jbAcquired,jbPackets,jbAttached,jbReports;
static void __attribute__((ms_abi)) jb_find(const void*b,void*u){
 (void)u;if(jbMechanism||!b||h35_is_hand_proxy_body(b))return;
 float m=0,x,y,z;p_h14GetMass(b,&m,&x,&y,&z);if(m<=0)return;
 void*w=p_h14GetUserData(b);char name[96];name[0]=0;
 if(w&&h5748n_copy_tstring((u8*)w+0x10,name,sizeof(name))&&h25_str_contains(name,"CPU6Cup")){
  jbMechanism=b;p_h14GetMatrix(b,jbStartBody);jbContact[0]=jbStartBody[12];jbContact[1]=jbStartBody[13];jbContact[2]=jbStartBody[14]+.025f;
  ext_Log("JB_MECHANISM_BODY %s at %.4f %.4f %.4f",name,jbStartBody[12],jbStartBody[13],jbStartBody[14]);
 }
}
static void jb_to_tracking(const float*v,float*out){
 float ex[3],ey[3],ez[3];tracking_vector_to_game_unscaled(1,0,0,&ex[0],&ex[1],&ex[2]);tracking_vector_to_game_unscaled(0,1,0,&ey[0],&ey[1],&ey[2]);tracking_vector_to_game_unscaled(0,0,1,&ez[0],&ez[1],&ez[2]);out[0]=h10_dot(v,ex);out[1]=h10_dot(v,ey);out[2]=h10_dot(v,ez);
}
static void cpu6_pose(i64 now){
 cpu6Now=now;if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!p2_xr_origin_set()||!visual_pose_valid(0)||!visual_pose_valid(1))return;
 if(!cpu6PoseSeed){jbInitialQ=g_lastPose[1].orientation;cpu6PoseSeed=1;}
 volatile float*o=p2_xr_origin();float t=cpu6Start?(float)((double)(now-cpu6Start)*1e-9):0;
 for(int h=0;h<2;h++){g_lastPose[h].position.x=o[0]+(h?.25f:-.3f);g_lastPose[h].position.y=o[1]-.3f;g_lastPose[h].position.z=o[2]-.4f;zero_bytes(&g_lastLinearVelocity[h],sizeof(g_lastLinearVelocity[h]));zero_bytes(&g_lastAngularVelocity[h],sizeof(g_lastAngularVelocity[h]));g_lastVelocityFlags[h]=XR_SPACE_VELOCITY_LINEAR_VALID_BIT|XR_SPACE_VELOCITY_ANGULAR_VALID_BIT;}
 g_lastPose[1].orientation=jbInitialQ;
 if(!jbMechanism)return;
 float angle=0,omega=0;
 if(jbAcquired){if(t>=10&&t<16){angle=(t-10)*.8f;omega=.8f;}else if(t>=16&&t<20){angle=4.8f;omega=0;}else if(t>=20&&t<26){angle=4.8f-(t-20)*.8f;omega=-.8f;}}
 float axis[3];jb_to_tracking(jbPin,axis);if(jbAcquired){XrQuaternionf dq={axis[0]*ext_Sinf(angle*.5f),axis[1]*ext_Sinf(angle*.5f),axis[2]*ext_Sinf(angle*.5f),ext_Cosf(angle*.5f)};g_lastPose[1].orientation=h514_q_mul(dq,jbInitialQ);g_lastAngularVelocity[1].x=axis[0]*omega;g_lastAngularVelocity[1].y=axis[1]*omega;g_lastAngularVelocity[1].z=axis[2]*omega;}
 float pos[3],hm[16],center[3];if(h14_hand_pose_raw(1,pos,hm)&&h15_grip_center_world(1,hm,center)){
  float delta[3]={jbContact[0]-center[0],jbContact[1]-center[1],jbContact[2]-center[2]},tracking[3];jb_to_tracking(delta,tracking);float metric=h5755ea_world_units_per_meter();
  g_lastPose[1].position.x+=tracking[0]/metric;g_lastPose[1].position.y+=tracking[1]/metric;g_lastPose[1].position.z+=tracking[2]/metric;
 }
}
static void cpu6_controls(void){
 if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!cpu6PoseSeed)return;
 if(!cpu6Start){cpu6Start=cpu6Now;ext_Log("CPU6_REPLAY_BEGIN JB native knob acquisition");}
 float t=(float)((double)(cpu6Now-cpu6Start)*1e-9);u32 ph=(u32)(t/5);if(ph>10)ph=10;cpu13Phase=ph;
 for(int h=0;h<2;h++){g_lastStickXActive[h]=g_lastStickYActive[h]=g_lastSqueezeActive[h]=1;g_lastStickX[h]=g_lastStickY[h]=g_lastSqueeze[h]=0;g_h5710StickClickActive[h]=1;g_h5710StickClick[h]=0;}
 if(!jbMechanism&&g_h14NewtonWorld&&p_h14WorldAABB){float lo[4]={-10, .5f,7.5f,0},hi[4]={-8,2,9.2f,0};p_h14WorldAABB(g_h14NewtonWorld,lo,hi,jb_find,0);}
 if(t>=6&&t<28)g_lastSqueeze[1]=1;
 if(jbMechanism&&g_h14GripBody[1]==jbMechanism){
  if(!jbAcquired){const void*j=h576ba_hand_wheel_joint(1);void*w=0;if(j&&h48_hinge_frame(j,jbPin,jbPivot,&w)){jbAcquired=1;ext_Log("JB_MECHANISM_ACQUIRED t %.4f jointed %d",t,g_h15GripJointed[1]);}}
  jbAttached++;
 }
 if(ph!=cpu6Phase){cpu6Phase=ph;float m[16]={0};if(jbMechanism)p_h14GetMatrix(jbMechanism,m);ext_Log("JB_MECHANISM_PHASE %u held %d jointed %d handCollider %p native %d owner %d wheelPackets %u bodyBasis %.4f %.4f %.4f",ph,g_h14GripBody[1]==jbMechanism&&jbMechanism!=0,g_h15GripJointed[1],g_h34HandNewton[1],g_h30NativeMouseDown,g_h30NativeUseHand,g_h576azWheelNativePackets[1],m[0],m[1],m[2]);jbReports++;}
 if(t>=31&&!cpu6Done){cpu6Done=1;void*f=ext_fopen("cpu6_movement.bin","wb");if(f){u32 row[4]={jbAcquired,jbAttached,g_h576azWheelNativePackets[1],jbReports};ext_fwrite(row,sizeof(row),1,f);ext_fclose(f);}ext_Log("CPU6_REPLAY_SAVED JB acquired %u attached %u packets %u released %d",jbAcquired,jbAttached,g_h576azWheelNativePackets[1],g_h14GripBody[1]==0);}
}
