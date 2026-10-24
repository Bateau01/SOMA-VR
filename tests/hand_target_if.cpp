#include <initializer_list>

#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdlib>
using i32=int;using u32=unsigned;using u8=unsigned char;
struct V{float x,y,z;};struct Pose{V position;};Pose g_lastPose[2];
float origin[3],camera[16],yaw,scale=1,spread=.18f,reach=.40f,drop=-.18f,bob[3];
int valid=1,originValid=1,cameraValid=1;u32 g_frameCounter,g_h14PhysicsSteps,g_s26ieRoomLog=0,g_h5748oFrameSyncOffsetCalls;
float g_h531TrackedTarget[2][16];int g_h531TrackedTargetValid[2];u32 g_h531TargetPublishes[2];
int visual_pose_valid(int){return valid;}int p2_xr_origin_set(){return originValid;}void*p2_camera_obj(){return cameraValid?camera:nullptr;}
float*p2_xr_origin(){return origin;}float*p2_hand_spread(){return &spread;}float*p2_hand_reach(){return &reach;}float*p2_hand_drop(){return &drop;}
void tracking_delta_to_game(float x,float y,float z,float*a,float*b,float*c){*a=scale*(cosf(yaw)*x+sinf(yaw)*z);*b=scale*y;*c=scale*(-sinf(yaw)*x+cosf(yaw)*z);}
void s26ch_bob_apply(void*,float*p){for(int k=0;k<3;k++)p[k]+=bob[k];}
void h5748o_tracking_horizontal_to_game(float x,float z,float*a,float*b){*a=cosf(yaw)*x+sinf(yaw)*z;*b=-sinf(yaw)*x+cosf(yaw)*z;}
int h5748o_yaw_zero_active(){return 0;}
void h10_make_model(int,float*p,float,float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;for(int k=0;k<3;k++)m[12+k]=p[k];}
void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*4);}void ext_Log(const char*,...){}
int checks=0;void check(bool b){checks++;if(!b){printf("FAIL %d\n",checks);exit(1);}}
static i32 h14_hand_pose_raw(i32 hand,float* pos,float* M){
    if(!visual_pose_valid(hand)||!p2_xr_origin_set()||!p2_camera_obj())return 0;
    volatile float* origin=p2_xr_origin();float dx=g_lastPose[hand].position.x-origin[0],dy=g_lastPose[hand].position.y-origin[1],dz=g_lastPose[hand].position.z-origin[2],wx,wy,wz;tracking_delta_to_game(dx,dy,dz,&wx,&wy,&wz);
    float* body=(float*)((u8*)p2_camera_obj()+0x10);pos[0]=body[0]+wx;pos[1]=body[1]+wy;pos[2]=body[2]+wz;
    s26ch_bob_apply(p2_camera_obj(),pos);
    float spread=*p2_hand_spread()-0.18f,reach=*p2_hand_reach()-0.40f,height=*p2_hand_drop()+0.18f,side=(hand==0)?-spread:spread,offx=0.0f,offz=0.0f;
    h5748o_tracking_horizontal_to_game(side,reach,&offx,&offz);if(h5748o_yaw_zero_active())g_h5748oFrameSyncOffsetCalls++;
    pos[0]+=offx;pos[1]+=height;pos[2]+=offz;h10_make_model(hand,pos,1.0f,M);
    h10_copy_f(g_h531TrackedTarget[hand],M,16);g_h531TrackedTargetValid[hand]=1;g_h531TargetPublishes[hand]++;
    static u32 ieStep[2],ieLogs[2];if(g_s26ieRoomLog&&ieLogs[hand]<160u&&ieStep[hand]!=g_h14PhysicsSteps){ieStep[hand]=g_h14PhysicsSteps;ieLogs[hand]++;ext_Log("S26IE HAND frame=%u step=%u hand=%d controller=%.6f,%.6f origin=%.6f,%.6f camera=%.6f,%.6f target=%.6f,%.6f",g_frameCounter,g_h14PhysicsSteps,hand,(double)g_lastPose[hand].position.x,(double)g_lastPose[hand].position.z,(double)origin[0],(double)origin[2],(double)body[0],(double)body[2],(double)pos[0],(double)pos[2]);}
    return 1;
}
int main(){
 for(int h=0;h<2;h++)for(float sc:{.5f,1.f,2.f})for(int angle=0;angle<8;angle++)for(int hz:{60,120}){
  scale=sc;yaw=angle*.785398163f;memset(origin,0,12);memset(camera,0,sizeof(camera));
  g_lastPose[h].position={h?.2f:-.2f,1.2f,-.4f};float p[3],m[16];
  check(h14_hand_pose_raw(h,p,m));float start[3];memcpy(start,p,12);
  for(int tick=0;tick<hz;tick++){
   // Common world displacement (walking, platform travel or camera lowering)
   camera[4]+=.03f;camera[5]-=.001f;camera[6]+=.02f;
   check(h14_hand_pose_raw(h,p,m));
   check(fabsf((p[0]-start[0])-camera[4])<.00001f);
   check(fabsf((p[1]-start[1])-camera[5])<.00001f);
   check(fabsf((p[2]-start[2])-camera[6])<.00001f);
   float old[3];memcpy(old,p,12);float wx,wy,wz;tracking_delta_to_game(.003f,0,-.002f,&wx,&wy,&wz);
   camera[4]+=wx;camera[6]+=wz;origin[0]+=.003f;origin[2]-=.002f;
   check(h14_hand_pose_raw(h,p,m));for(int k=0;k<3;k++)check(fabsf(p[k]-old[k])<.00002f);
   camera[4]-=wx;camera[6]-=wz;origin[0]-=.003f;origin[2]+=.002f;
  }
 }
 for(int gate=0;gate<3;gate++){valid=gate!=0;originValid=gate!=1;cameraValid=gate!=2;float p[3],m[16];check(!h14_hand_pose_raw(0,p,m));}
 printf("PASS %d production raw-target checks; mocked transforms/camera, not physical validation\n",checks);
}
