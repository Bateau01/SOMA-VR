"""Exercise the production hand tick, including the previously missed touch override.

The runtime and retargeting endpoints are mocked; geometric retargeting is tested
separately by test_frame_mapping.py. This test is not headset validation.
"""
from pathlib import Path
import subprocess, sys
R=Path(__file__).resolve().parents[1]; B=R/'build'; B.mkdir(exist_ok=True)
s=(R/'source/skeletal_q.inc').read_text()
def function(name):
    a=s.index('static ',s.index(name)-20); start=s.index('{',a); depth=0
    for i in range(start,len(s)):
        depth+=(s[i]=='{')-(s[i]=='}')
        if depth==0:return s[a:i+1]
types=s[s.index('typedef struct'):s.index('static S26QCreateHand')]
header=r'''
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef int i32;typedef unsigned u32;
typedef unsigned long long u64;typedef long long i64;typedef void* Handle;
typedef struct{float x,y,z,w;} Quat;typedef struct{float x,y,z;} Vec;
typedef struct{Quat orientation;Vec position;} XrPosef;
static float clamp01(float v){return v<0?0:v>1?1:v;}
static void zero_bytes(void*p,u64 n){memset(p,0,n);}static void ext_Log(const char*s,...){(void)s;}
#define H5755BH_GAMEPLAY_VR 1
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
'''
mock=r'''
static u8 g_s26ebProfileChanged[2];
static u8 g_s26dnMotionRangeEnabled=1,g_s26diFrameHand[2],g_s26qHandReported[2];
static u32 g_s26qHandLogs,g_h5755bhPresentationState,g_s26djFingerTracking=1;
static u32 g_s26dlTouchKnown[2],g_s26dlTouched[2],g_s26dmReleasedMask[2];
static float g_lastSqueeze[2],g_lastTrigger[2],input[2][5];
static u64 g_s26qFingerInput[2][5],g_s26qRootInput[2][5];
static Handle g_s26qHandSession=(Handle)10,g_s26qHandTracker[2]={(Handle)1,(Handle)2};
static int frameProfile=1,locateResult,active=1,count=26,chains[2],calls,checks;
static int s26u_controller_fingers_allowed(Handle s,int h){g_s26diFrameHand[h]=g_s26djFingerTracking&&frameProfile>=0?frameProfile:0;return g_s26djFingerTracking&&frameProfile>=0;}
static void s26q_clear_finger_input(void){memset(g_s26qFingerInput,0,sizeof(g_s26qFingerInput));memset(g_s26qRootInput,0,sizeof(g_s26qRootInput));}
static i32 __attribute__((ms_abi)) locate(Handle hand,const S26QHandLocate*li,S26QJoints*out){
 int h=(int)(u64)hand-1;++calls;chains[h]=0;
 if(li->next){const S26DNMotionRange*r=li->next;chains[h]=(r->type==1000080000&&r->range==1&&!r->next)?1:-1;}
 out->active=active;out->count=count;out->joints[0].radius=(float)h;return locateResult;
}
static S26QLocateHand p_s26qLocateHand=locate;
static int s26di_frame_curl(const S26QJoint*j,int h,int f,float*v){for(int d=0;d<4;d++)v[d]=input[h][f];return 1;}
static int s26q_retarget_finger(const S26QJoint*j,int f,float*v){return s26di_frame_curl(j,(int)j[0].radius,f,v);}
static u64 s26q_root_from_joints(const S26QJoint*j,int f){return 23+f;}
'''
main=r'''
int main(void){
 // Every combination of touch observations must leave valid finger data intact.
 for(int mask=0;mask<32;mask++)for(int step=0;step<11;step++){
  for(int h=0;h<2;h++){
   g_s26dlTouchKnown[h]=31;g_s26dlTouched[h]=mask;g_s26dmReleasedMask[h]=31^mask;
   for(int f=0;f<5;f++)input[h][f]=(float)(step+f+h)/16;
  }
  s26q_hands_tick((Handle)10,(Handle)20,100,1);
  for(int h=0;h<2;h++){
   CHECK(chains[h]==1);
   for(int f=0;f<5;f++){float v[4]={input[h][f],input[h][f],input[h][f],input[h][f]};CHECK(g_s26qFingerInput[h][f]==s26q_pack_finger(v));CHECK(g_s26qRootInput[h][f]==0);}
  }
 }
 // All eligible profiles request full motion when the extension is enabled.
 frameProfile=0;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 for(int h=0;h<2;h++){CHECK(chains[h]==1);for(int f=0;f<5;f++)CHECK(g_s26qRootInput[h][f]==0);}
 frameProfile=1;g_s26dnMotionRangeEnabled=0;s26q_hands_tick((Handle)10,(Handle)20,100,1);CHECK(!chains[0]&&!chains[1]);
 g_s26dnMotionRangeEnabled=1;
 // Off, inactive, errors, bad joint count, loss of focus/session/space/time clear data.
 for(int fault=0;fault<8;fault++){
  s26q_hands_tick((Handle)10,(Handle)20,100,1);CHECK(g_s26qFingerInput[0][0]);
  if(fault==0)g_s26djFingerTracking=0;if(fault==1)active=0;if(fault==2)locateResult=-1;if(fault==3)count=25;
  s26q_hands_tick(fault==4?(Handle)99:(Handle)10,fault==5?0:(Handle)20,fault==6?0:100,fault==7?0:1);
  for(int h=0;h<2;h++)for(int f=0;f<5;f++){CHECK(!g_s26qFingerInput[h][f]);CHECK(!g_s26qRootInput[h][f]);}
  g_s26djFingerTracking=1;active=1;locateResult=0;count=26;
 }
 // The real profile gate clears Frame eligibility when disabled; retain the
 // explicit rest reference across an off/on toggle nevertheless.
 g_s26dzRest[0][4].reference=.3f;g_s26dzRest[0][4].manual=1;g_s26dzRest[0][4].learned=1;
 g_s26djFingerTracking=0;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(g_s26dzRest[0][4].manual&&g_s26dzRest[0][4].reference==.3f);
 g_s26djFingerTracking=1;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(g_s26dzRest[0][4].manual&&g_s26dzRest[0][4].reference==.3f);
 frameProfile=-1;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(!g_s26qFingerInput[0][4]&&g_s26dzRest[0][4].manual);
 frameProfile=1;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(g_s26dzRest[0][4].manual&&g_s26dzRest[0][4].reference==.3f);
 // Explicit reference is retained on non-Frame controllers too.
 frameProfile=0;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(g_s26dzRest[0][4].manual);
 g_s26ebProfileChanged[0]=1;s26q_hands_tick((Handle)10,(Handle)20,100,1);
 CHECK(!g_s26dzRest[0][4].manual&&!g_s26ebProfileChanged[0]);
 // Preserve an existing locate-next chain when the extension is unavailable.
 S26QHandLocate li={0};S26DNMotionRange range;int tail=42;li.next=&tail;
 s26dn_motion_range(&li,&range,0);CHECK(li.next==&tail);
 s26dn_motion_range(&li,&range,1);CHECK(li.next==&range&&range.next==&tail);
 printf("PASS %d production skeletal publication checks\n",checks);return 0;
}
'''
code=header+types+'\n'+(R/'source/motion_range_dn.inc').read_text()+mock+(R/'source/frame_rest_dz.inc').read_text()+(R/'source/finger_reset_ea.inc').read_text()+function('s26q_pack_finger')+'\n'+function('s26q_hands_tick')+main
c=B/'skeletal_publish_test.c';c.write_text(code);exe=B/'skeletal_publish_test.exe'
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
# Demonstrate that the old production group override is rejected by this test.
old=code.replace('// A learned resting reference does not replace runtime motion.', 'if(valid&&g_s26diFrameHand[h]&&(g_s26dmReleasedMask[h]&(1u<<f)))packed=1ULL<<63;')
assert old!=code
c.write_text(old);bad=B/'skeletal_publish_old.exe'
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(bad)],check=True)
result=subprocess.run([str(bad)],capture_output=True,text=True)
assert result.returncode!=0, 'Regression test failed to detect old suppression'
c.write_text(code)
print('PASS: the previous touch-mask suppression fails the same publication test')
