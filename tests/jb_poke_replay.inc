/* Actual saved chip; synthetic open-index approach followed by one grip.
   No target body, permission or callback is changed by the fixture. */
static i64 cpu6Start,cpu6Now;static u32 cpu6Phase=99,cpu6Done,cpu6PoseSeed;
static const void* jbMechanism;static XrQuaternionf jbInitialQ;
static float jbPin[3],jbPivot[3],jbContact[3],jbStartBody[16];
static u32 jbAcquired,jbPackets,jbAttached,jbReports,jbOrientSet;static float jbGripAt=-1;
static void __attribute__((ms_abi)) jb_find(const void*b,void*u){
 (void)u;if(jbMechanism||!b||h35_is_hand_proxy_body(b))return;
 float m=0,x,y,z;p_h14GetMass(b,&m,&x,&y,&z);if(m>.001f)return;
 void*w=p_h14GetUserData(b);char name[96];name[0]=0;
 if(w&&h5748n_copy_tstring((u8*)w+0x10,name,sizeof(name))&&h25_str_contains(name,"CPU6Cup_Body_2")){
  jbMechanism=b;p_h14GetMatrix(b,jbStartBody);jbContact[0]=jbStartBody[12];jbContact[1]=jbStartBody[13];jbContact[2]=jbStartBody[14]+.006f;
  ext_Log("JB_MECHANISM_BODY %s at %.4f %.4f %.4f",name,jbStartBody[12],jbStartBody[13],jbStartBody[14]);
 }
}
static void jb_to_tracking(const float*v,float*out){
 float ex[3],ey[3],ez[3];tracking_vector_to_game_unscaled(1,0,0,&ex[0],&ex[1],&ex[2]);tracking_vector_to_game_unscaled(0,1,0,&ey[0],&ey[1],&ey[2]);tracking_vector_to_game_unscaled(0,0,1,&ez[0],&ez[1],&ez[2]);out[0]=h10_dot(v,ex);out[1]=h10_dot(v,ey);out[2]=h10_dot(v,ez);
}
static void cpu6_pose(i64 now){
 cpu6Now=now;if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!p2_xr_origin_set()||!visual_pose_valid(0)||!visual_pose_valid(1))return;
 if(!cpu6PoseSeed){jbInitialQ=(XrQuaternionf){0,0,0,1};cpu6PoseSeed=1;}
 volatile float*o=p2_xr_origin();float t=cpu6Start?(float)((double)(now-cpu6Start)*1e-9):0;
 for(int h=0;h<2;h++){g_lastPose[h].position.x=o[0]+(h?.25f:-.3f);g_lastPose[h].position.y=o[1]-.3f;g_lastPose[h].position.z=o[2]-.4f;zero_bytes(&g_lastLinearVelocity[h],sizeof(g_lastLinearVelocity[h]));zero_bytes(&g_lastAngularVelocity[h],sizeof(g_lastAngularVelocity[h]));g_lastVelocityFlags[h]=XR_SPACE_VELOCITY_LINEAR_VALID_BIT|XR_SPACE_VELOCITY_ANGULAR_VALID_BIT;}
 g_lastPose[1].orientation=jbInitialQ;
 if(!jbMechanism)return;
 float angle=0,omega=0;
 if(0){if(t>=10&&t<16){angle=(t-10)*.8f;omega=.8f;}else if(t>=16&&t<20){angle=4.8f;omega=0;}else if(t>=20&&t<26){angle=4.8f-(t-20)*.8f;omega=-.8f;}}
 float axis[3];jb_to_tracking(jbPin,axis);if(jbAcquired){XrQuaternionf dq={axis[0]*ext_Sinf(angle*.5f),axis[1]*ext_Sinf(angle*.5f),axis[2]*ext_Sinf(angle*.5f),ext_Cosf(angle*.5f)};g_lastPose[1].orientation=h514_q_mul(dq,jbInitialQ);g_lastAngularVelocity[1].x=axis[0]*omega;g_lastAngularVelocity[1].y=axis[1]*omega;g_lastAngularVelocity[1].z=axis[2]*omega;}
 float pos[3],hm[16],center[3],openCurl[4]={0,0,0,0},finger[5][3];i32 fingerLen=0;
 if(h14_hand_pose_raw(1,pos,hm)&&h18_finger_points_world(1,1,openCurl,hm,finger,&fingerLen)&&fingerLen>=1&&fingerLen<=4){
 if(!jbOrientSet){
  float cur[3]={finger[fingerLen][0]-finger[0][0],finger[fingerLen][1]-finger[0][1],finger[fingerLen][2]-finger[0][2]},desired[3]={0,0,-1},c[3],d[3];
  jb_to_tracking(cur,c);jb_to_tracking(desired,d);
  if(h10_norm3(c)&&h10_norm3(d)){float dot=h10_dot(c,d);if(dot>-.999f){float v[3];h10_cross(c,d,v);float k=ext_Sqrtf(2*(1+dot));XrQuaternionf q={v[0]/k,v[1]/k,v[2]/k,k*.5f};jbInitialQ=h514_q_mul(q,jbInitialQ);jbOrientSet=1;ext_Log("JB_CHIP_POINT_ORIENTATION %.5f %.5f %.5f %.5f",jbInitialQ.x,jbInitialQ.y,jbInitialQ.z,jbInitialQ.w);}}
 }
 for(i32 a=0;a<3;a++)center[a]=finger[fingerLen][a];
  float depth=.12f;
 if(t>=4&&t<5)depth=.12f*(5-t);else if(t>=5&&t<6)depth=0;else if(t>=6&&t<7)depth=.12f*(t-6);
 // Deterministic two-sample crossing: 14cm, within the 15cm rejection bound.
 else if(t>=10&&t<10.12f)depth=-.02f;
 float delta[3]={jbContact[0]-center[0],jbContact[1]-center[1],jbContact[2]+depth-center[2]},tracking[3];jb_to_tracking(delta,tracking);float metric=h5755ea_world_units_per_meter();
  g_lastPose[1].position.x+=tracking[0]/metric;g_lastPose[1].position.y+=tracking[1]/metric;g_lastPose[1].position.z+=tracking[2]/metric;
 }
}
static void cpu6_controls(void){
 if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!cpu6PoseSeed)return;
 if(!jbMechanism&&g_h14NewtonWorld&&p_h14WorldAABB){float lo[4]={-9,.5f,7.5f,0},hi[4]={-7,2,9.2f,0};p_h14WorldAABB(g_h14NewtonWorld,lo,hi,jb_find,0);}
 if(!jbMechanism||!g_h34HandNewton[0]||!g_h34HandNewton[1]||g_h34ControllerStable[0]<H34G_CONTROLLER_STABLE_FRAMES||g_h34ControllerStable[1]<H34G_CONTROLLER_STABLE_FRAMES)return;
 if(!cpu6Start){cpu6Start=cpu6Now;ext_Log("CPU6_REPLAY_BEGIN JB world-control slow and fast poke");}
 float t=(float)((double)(cpu6Now-cpu6Start)*1e-9);u32 ph=(u32)(t/5);if(ph>10)ph=10;cpu13Phase=ph;
 if(t>=9.9f&&t<=10.25f){for(i32 k=0;k<g_s26yCount;k++)if(g_s26yRocker[k].used&&g_s26yRocker[k].raw==jbMechanism)ext_Log("JB_POKE_CROSS t %.6f step %u frame %u blocked %d active %d",t,g_h14PhysicsSteps,g_frameCounter,g_s26yRocker[k].blocked,g_s26yRocker[k].active);}
 for(int h=0;h<2;h++){g_lastStickXActive[h]=g_lastStickYActive[h]=g_lastSqueezeActive[h]=1;g_lastStickX[h]=g_lastStickY[h]=g_lastSqueeze[h]=0;g_lastTriggerActive[h]=g_lastTouchActive[h]=1;g_lastTrigger[h]=0;g_lastTriggerTouch[h]=0;g_h5710StickClickActive[h]=1;g_h5710StickClick[h]=0;}
 if(ph!=cpu6Phase){cpu6Phase=ph;float m[16]={0};if(jbMechanism)p_h14GetMatrix(jbMechanism,m);ext_Log("JB_MECHANISM_PHASE %u held %d jointed %d handCollider %p native %d owner %d wheelPackets %u bodyBasis %.4f %.4f %.4f",ph,g_h14GripBody[1]==jbMechanism&&jbMechanism!=0,g_h15GripJointed[1],g_h34HandNewton[1],g_h30NativeMouseDown,g_h30NativeUseHand,g_h576azWheelNativePackets[1],m[0],m[1],m[2]);jbReports++;}
 if(t>=20&&!cpu6Done){cpu6Done=1;void*f=ext_fopen("cpu6_movement.bin","wb");if(f){u32 row[4]={jbAcquired,jbAttached,g_h576azWheelNativePackets[1],jbReports};ext_fwrite(row,sizeof(row),1,f);ext_fclose(f);}ext_Log("CPU6_REPLAY_SAVED JB acquired %u attached %u packets %u released %d",jbAcquired,jbAttached,g_h576azWheelNativePackets[1],g_h14GripBody[1]==0);}
}

static float jb_poke_time(void){return cpu6Start?(float)((double)(cpu6Now-cpu6Start)*1e-9):0;}
