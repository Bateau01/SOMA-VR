/* Isolated input replay only. Does not force a grab or replace the solver. */
static float izContact[3],izNormal[3];static u32 izLoggedPhase=99;
static i64 cpu6Start,cpu6Now;static u32 cpu6Placed,cpu6Phase=99,cpu6Done;
static const void* cpu6Cup;static XrQuaternionf cpu6Q[2];static u32 cpu6PoseSeed;
static i64 cpu6PreviousPoseTime;static XrVector3f cpu6PreviousPosition[2];
static u64 cpu6LastTick;static u32 cpu6ContactLog,cpu6GripRequested;
typedef struct{u32 phase,frame,held,hands;float interval,x,y,z,cameraY,sceneMs,xrMs,newtonMs,textureMs;}CPU6Record;
static CPU6Record cpu6Rows[12000];static u32 cpu6Count;
static void __attribute__((ms_abi)) cpu6_find(const void*b,void*u){
 (void)u;if(cpu6Cup||!b||h35_is_hand_proxy_body(b))return;float m=0,x,y,z;p_h14GetMass(b,&m,&x,&y,&z);if(m>0){void*w=p_h14GetUserData(b);char name[96];name[0]=0;if(w&&h5748n_copy_tstring((u8*)w+0x10,name,sizeof(name))&&(h25_str_contains(name,"locker_cabin_9")||h25_str_contains(name,"03_02_diving_suit_locker_door_3"))){cpu6Cup=b;ext_Log(">>> CPU12_FIXTURE_BODY %s",name);}}
}
static float cpu6_triangle(float t){i32 k=(i32)(t/4.f);float v=t-4.f*k;return v<2.f?v-1.f:3.f-v;}
static void cpu6_pose(i64 now){
 cpu6Now=now;if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!p2_xr_origin_set()||!visual_pose_valid(0)||!visual_pose_valid(1))return;
 if(!cpu6PoseSeed){cpu6Q[0]=g_lastPose[0].orientation;cpu6Q[1]=g_lastPose[1].orientation;cpu6PoseSeed=1;}
 volatile float*o=p2_xr_origin();float t=cpu6Start?(float)((double)(now-cpu6Start)*1e-9):0;
 double poseDt=cpu6PreviousPoseTime?(double)(now-cpu6PreviousPoseTime)*1e-9:0;
 for(i32 h=0;h<2;h++){
  g_lastPose[h].position.x=o[0]+(h?.25f:-.25f)+(h&&t>=45&&t<50?.10f*cpu6_triangle(t):0);
  g_lastPose[h].position.y=o[1]-.30f;g_lastPose[h].position.z=o[2]-.40f;g_lastPose[h].orientation=cpu6Q[h];
  if(h==1 && cpu6Placed && t>=5){
   float p[3],m[16],gc[3];
   if(h14_hand_pose_raw(h,p,m)&&h15_grip_center_world(h,m,gc)){
    float reach=t<10?0.15f*(10-t)/5.0f:((t>=15&&t<30)||(t>=42&&t<50))?0.20f:0.005f;
    float d[3];for(int k=0;k<3;k++)d[k]=izContact[k]+izNormal[k]*reach-gc[k];
    float x[3],y[3],z[3];tracking_delta_to_game(1,0,0,x,x+1,x+2);tracking_delta_to_game(0,1,0,y,y+1,y+2);tracking_delta_to_game(0,0,1,z,z+1,z+2);
    float xx=h10_dot(x,x),yy=h10_dot(y,y),zz=h10_dot(z,z);
    if(xx>.00001f&&yy>.00001f&&zz>.00001f){g_lastPose[h].position.x+=h10_dot(d,x)/xx;g_lastPose[h].position.y+=h10_dot(d,y)/yy;g_lastPose[h].position.z+=h10_dot(d,z)/zz;}
   }
  }
  /* Test-input derivative only: never retain unrelated live-controller velocity. */
  zero_bytes(&g_lastLinearVelocity[h],sizeof(g_lastLinearVelocity[h]));zero_bytes(&g_lastAngularVelocity[h],sizeof(g_lastAngularVelocity[h]));
  g_lastVelocityFlags[h]=XR_SPACE_VELOCITY_ANGULAR_VALID_BIT;
  if(poseDt>0 && poseDt<.1){
   g_lastLinearVelocity[h].x=(float)((g_lastPose[h].position.x-cpu6PreviousPosition[h].x)/poseDt);
   g_lastLinearVelocity[h].y=(float)((g_lastPose[h].position.y-cpu6PreviousPosition[h].y)/poseDt);
   g_lastLinearVelocity[h].z=(float)((g_lastPose[h].position.z-cpu6PreviousPosition[h].z)/poseDt);
   g_lastVelocityFlags[h]|=XR_SPACE_VELOCITY_LINEAR_VALID_BIT;
  }
  cpu6PreviousPosition[h]=g_lastPose[h].position;
 }
 cpu6PreviousPoseTime=now;
}
static void cpu6_controls(void){
 if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!cpu6PoseSeed)return;
 if(!cpu6Start){cpu6Start=cpu6Now;ext_Log(">>> CPU6_REPLAY_BEGIN actual XR, synthetic controller positions/sticks, native grip edge and solver");}
 float t=(float)((double)(cpu6Now-cpu6Start)*1e-9);u32 phase=(u32)(t/5.f);if(phase>10)phase=10;
 cpu13Phase=phase;if(phase!=cpu6Phase){cpu6Phase=phase;ext_Log(">>> CPU6_REPLAY_PHASE %u held %u",phase,g_h14GripBody[1]==cpu6Cup&&cpu6Cup!=0);}
 for(i32 h=0;h<2;h++){g_lastStickXActive[h]=g_lastStickYActive[h]=g_lastSqueezeActive[h]=1;g_lastStickX[h]=g_lastStickY[h]=g_lastSqueeze[h]=0;g_h5710StickClickActive[h]=1;g_h5710StickClick[h]=0;}



 if(!cpu6Cup&&phase<4&&g_h14NewtonWorld&&p_h14WorldAABB&&p2_camera_obj()){
 float*pos=(float*)((u8*)p2_camera_obj()+0x10);float lo[4]={pos[0]-4,pos[1]-4,pos[2]-4,0},hi[4]={pos[0]+4,pos[1]+4,pos[2]+4,0};p_h14WorldAABB(g_h14NewtonWorld,lo,hi,cpu6_find,0);}
 if(cpu6Cup && !cpu6Placed && p_h14PointDistance){
 float matrix[16],point[4],cp[4],normal[4];p_h14GetMatrix(cpu6Cup,matrix);
 float*cam=(float*)((u8*)p2_camera_obj()+0x10);for(int i=0;i<3;i++)point[i]=cam[i];point[3]=0;
 if(p_h14PointDistance(g_h14NewtonWorld,point,p_h14GetCollision(cpu6Cup),matrix,cp,normal,0)){
  for(int i=0;i<3;i++){izContact[i]=cp[i];izNormal[i]=normal[i];}cpu6Placed=1;
  ext_Log("IZ_TARGET_SURFACE %.4f %.4f %.4f normal %.3f %.3f %.3f",cp[0],cp[1],cp[2],normal[0],normal[1],normal[2]);
 }
 }
 if(cpu6Placed && ((phase>=2&&phase<=5)||(phase>=8&&phase<=9)))g_lastSqueeze[1]=1;
 if(cpu6Phase!=izLoggedPhase){izLoggedPhase=cpu6Phase;ext_Log("IZ_INTERACTION phase %u authored %u swing %u held %p target %p",phase,g_h482AuthoredDragActive[1],g_h5755ceNativeSwingDoorActive[1],g_h14GripBody[1],cpu6Cup);}
 u64 now=0;if(cpuCounter)cpuCounter(&now);
 if(now&&cpu6LastTick&&cpu6Count<12000){CPU6Record*r=cpu6Rows+cpu6Count++;r->phase=phase;r->frame=g_frameCounter;r->held=g_h14GripBody[1]==cpu6Cup&&cpu6Cup!=0;r->hands=(g_h34HandNewton[0]!=0)+(g_h34HandNewton[1]!=0);r->interval=(float)(1000.0*(now-cpu6LastTick)/cpuFreq);float m[16];if(g_h34HandNewton[1])p_h14GetMatrix(g_h34HandNewton[1],m);else zero_bytes(m,sizeof(m));r->x=m[12];r->y=m[13];r->z=m[14];r->cameraY=((float*)((u8*)p2_camera_obj()+0x10))[1];r->sceneMs=(float)cpu6Scene;r->xrMs=(float)cpu6XR;r->newtonMs=(float)cpu6Newton;r->textureMs=(float)cpu6Texture;cpu6Scene=cpu6XR=cpu6Newton=cpu6Texture=0;}
 cpu6LastTick=now;
 if(phase==10&&t>=52.f&&!cpu6Done){cpu6Done=1;for(u32 ph=0;ph<11;ph++){ext_Log(">>> CPU13_PHASE phase %u steps %u native_calls %u dt_sum %.6f",ph,cpu13Steps[ph],cpu13NativeCalls[ph],cpu13Dt[ph]);ext_Log(">>> CPU13_QUERY phase %u calls %llu hits %llu",ph,cpu13Totals[ph][17],cpu13Totals[ph][18]);ext_Log(">>> CPU13_PAIRS phase %u own_calls %llu own_ms %.6f other_calls %llu other_ms %.6f",ph,cpu13Totals[ph][21],1000.0*cpu13Totals[ph][19]/cpuFreq,cpu13Totals[ph][22],1000.0*cpu13Totals[ph][20]/cpuFreq);for(u32 slot=0;slot<17;slot++)ext_Log(">>> CPU13_COST phase %u slot %u total_ms %.6f",ph,slot,1000.0*cpu13Totals[ph][slot]/cpuFreq);}void*f=ext_fopen("cpu6_movement.bin","wb");if(f){u64 written=ext_fwrite(cpu6Rows,sizeof(CPU6Record),cpu6Count,f);ext_Log(">>> CPU6_WRITE records %llu expected %u",written,cpu6Count);ext_fclose(f);}ext_Log(">>> CPU6_REPLAY_SAVED rows %u held %u",cpu6Count,g_h14GripBody[1]==cpu6Cup&&cpu6Cup!=0);}
}
