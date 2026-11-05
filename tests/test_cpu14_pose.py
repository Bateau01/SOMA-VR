from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1];b=r/'build/cpu14';s=(r/'tests/cpu6_movement_replay.inc').read_text();a=s.index('static float cpu6_triangle');z=s.index('static void cpu6_controls');fn=s[a:z]
head=r'''
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
typedef int32_t i32;typedef int64_t i64;typedef uint32_t u32;
typedef struct{float x,y,z;}XrVector3f;typedef struct{float x,y,z,w;}XrQuaternionf;
static struct{XrVector3f position;XrQuaternionf orientation;}g_lastPose[2];
static XrVector3f g_lastLinearVelocity[2],g_lastAngularVelocity[2],cpu6PreviousPosition[2];
static unsigned long long g_lastVelocityFlags[2];static XrQuaternionf cpu6Q[2];
static i64 cpu6Start,cpu6Now,cpu6PreviousPoseTime;static u32 cpu6PoseSeed;
static int g_h5755bhPresentationState=1;
#define H5755BH_GAMEPLAY_VR 1
#define XR_SPACE_VELOCITY_ANGULAR_VALID_BIT 2
#define XR_SPACE_VELOCITY_LINEAR_VALID_BIT 1
#define zero_bytes memset_zero
static void memset_zero(void*p,unsigned n){memset(p,0,n);}
static float origin[3];static int p2_xr_origin_set(void){return 1;}static int visual_pose_valid(int h){return 1;}static volatile float*p2_xr_origin(void){return origin;}
'''
tail=r'''
int main(void){
 g_lastPose[0].orientation.w=g_lastPose[1].orientation.w=1;
 g_lastLinearVelocity[0].x=100;g_lastAngularVelocity[1].z=20;
 cpu6_pose(1000000000);assert(g_lastVelocityFlags[0]==2&&g_lastLinearVelocity[0].x==0&&g_lastAngularVelocity[1].z==0);
 cpu6_pose(1010000000);assert(g_lastVelocityFlags[0]==3&&g_lastLinearVelocity[0].x==0);
 origin[0]=.01f;cpu6_pose(1020000000);assert(g_lastLinearVelocity[0].x>.999&&g_lastLinearVelocity[0].x<1.001);
 cpu6_pose(1020000000);assert(g_lastVelocityFlags[0]==2);cpu6_pose(2020000000);assert(g_lastVelocityFlags[0]==2);
 assert(g_lastPose[1].orientation.w==1&&g_lastAngularVelocity[1].z==0);
 puts("PASS synthetic velocities replace live samples, stationary zero, position derivative, repeated/backlog time invalidation, fixed orientation");
}
'''
p=b/'pose.c';p.write_text(head+fn+tail);zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc',str(p),'-o',str(b/'pose.exe')],check=True);subprocess.run([str(b/'pose.exe')],check=True)
