"""Compile actual baseline/candidate adapters with mocked engine geometry; compare 60Hz packets and gap/stop safety. Native game evidence is separate."""
from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1]
def extract(s):
 a=s.index('static i32 s26ip_lever_impl(');b=s.index('\n}',a)+2;return s[a:b]
s=(R/'source/s26n.c').read_text();old=(R/'tests/fixtures/iq_baseline/s26n.c').read_text()
head=r"""
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef unsigned u32;typedef int i32;typedef unsigned long long u64;
#define H5755GF_LEVER_ANGLE_DEADZONE_RAD .004f
#define H5755GF_LEVER_ANGLE_STEP_CAP_RAD .060f
#define H5755GF_LEVER_ANGLE_LOOK_GAIN .85f
#define H5755GF_LEVER_AXIS_CAP .20f
#define H576BD_LEVER_ANALOG_TAG 3.f
#define H34_ANALOG_LOOK 0
static int exact=1,packets;static float packet[4];
static unsigned g_h5755gbLeverNativeFailClosed[2],g_h5755gbLeverNativeWarmup[2],g_h482ArticulatedValid[2],g_h5755geLeverRadialAxialRejects[2],g_h5755gbLeverNativePackets[2],g_h5755geLeverTangentPackets[2],g_h5755gbLeverNativeFallthrough[2],g_h5755geLeverTangentLogs[2];
static unsigned g_s26gdRateMultiplier=1,g_s26iqLeverPoseEpoch[2],g_s26iqPoseEpoch[2],g_lastActive[2]={1,1};static u64 g_lastFlags[2]={3,3};
static int g_h37aAnalogGuardReady=1,g_h576bdLeverScriptOK=1,g_h37aSyntheticAnalogHand,g_h37aSyntheticFellThrough,g_h37aSyntheticAnalogDepth,g_h34AnalogCalls,g_h30NativeMotionEvents;
static void* g_h482DriveBody[2];static void* g_h14GripBody[2]={(void*)1,(void*)2};static void* g_h482DriveJoint[2];static void* g_h15GripJoint[2]={(void*)3,(void*)4};
static float g_h482DriveBodyAnchor[2][3],g_h15GripBodyAnchor[2][3]={{1,0,0},{1,0,0}};
static char *g_h5729LastModuleName,*g_h5729LastClassName;
static struct {int stage;float raw,tan,rad,axis,angle,radius;} g_s26ipLever[2];
static void ext_Log(const char*x,...){ }
static int h5755fn_exact_lever_names(char*a,char*b){return exact;}
static void* h34_player_input_interface(){return (void*)5;}
static int h48_hinge_frame(const void*j,float*p,float*v,void**w){p[0]=p[1]=0;p[2]=1;v[0]=v[1]=v[2]=0;return 1;}
static void matrix(const void*b,float*m){ }
static void (*p_h14GetMatrix)(const void*,float*)=matrix;
static void h14_transform_point(const float*m,const float*a,float*v){memcpy(v,a,12);}
static float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
static void h10_cross(const float*a,const float*b,float*c){c[0]=a[1]*b[2]-a[2]*b[1];c[1]=a[2]*b[0]-a[0]*b[2];c[2]=a[0]*b[1]-a[1]*b[0];}
static int h10_norm3(float*v){float l=sqrtf(h10_dot(v,v));if(l<1e-9f)return 0;for(int i=0;i<3;i++)v[i]/=l;return 1;}
static float h9_abs(float x){return fabsf(x);}
static void analog(void*pi,int id,float*a){packets++;memcpy(packet,a,16);}
static void (*p_h34PlayerAnalog)(void*,int,float*)=analog;
"""
main=r"""
int main(){int n=0;float v[3]={0,0,0};
#define C(x) do{n++;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
for(int hand=0;hand<2;hand++)for(int k=-10000;k<=10000;k++){v[1]=k*.001f;packets=0;baseline(hand,v,1.f/60);int count=packets;float before[4];memcpy(before,packet,16);packets=0;s26ip_lever_impl(hand,v,1.f/60);C(count==packets);if(count)C(memcmp(before,packet,16)==0);}
g_s26gdRateMultiplier=2;v[1]=.5f;g_s26iqPoseEpoch[0]++;packets=0;s26ip_lever_impl(0,v,1.f/120);C(packets==1&&packet[0]>0&&packet[1]==1);
v[1]=0;packets=0;s26ip_lever_impl(0,v,1.f/120);C(packets==0); // repeated pose is no new stop
 g_s26iqPoseEpoch[0]++;s26ip_lever_impl(0,v,1.f/120);C(packets==1&&packet[0]==0&&packet[1]==1); // fresh stop
v[1]=-.5f;packets=0;s26ip_lever_impl(0,v,1.f/120);C(packets==1&&packet[0]<0); // reversal
v[1]=.5f;g_lastActive[0]=0;packets=0;s26ip_lever_impl(0,v,1.f/120);C(packets==1&&packet[0]==0); // lost tracking cannot drive
 g_lastActive[0]=1;exact=0;packets=0;s26ip_lever_impl(0,v,1.f/120);C(packets==0);exact=1;
g_h576bdLeverScriptOK=0;packets=0;s26ip_lever_impl(1,v,1.f/120);C(packets==0&&g_h5755gbLeverNativeFailClosed[1]);
printf("PASS %d actual-adapter assertions; 60Hz equivalence, both hands, fresh-stop, gaps, reversal, tracking loss, identity and stale-script rejection\n",n);}
"""
p=R/'build/lever_gaps_iq.c';p.write_text(head+extract(old).replace('s26ip_lever_impl(','baseline(',1)+extract(s)+main)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout);assert v.returncode==0
(R/'docs/v109-evidence/lever_adapter_iq.json').write_text(json.dumps({'scope':__doc__,'output':v.stdout}))
