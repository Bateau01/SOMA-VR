"""Production liquid-filter extraction, mocked native callback/wrappers."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
a=s.index('typedef void (__attribute__((ms_abi)) *S26BTForceCallback)');b=s.index('static void s26fo_report_hand_water',a)
code=s[a:b]
head=r'''
#include <cassert>
#include <cstdio>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
void* g_h14GripBody[2];int g_h15GripJointed[2],g_h532Dormant[2],g_h532ArmState[2];
void* g_h34HandNewton[2];void* g_h34HandWrapper[2];int g_h576mScriptRuntimePublished=1;
bool xrOn=true;int p2_xr_on(){return xrOn;}
u8 wrappers[6][1024];void* getUser(const void*b){return (void*)b;}auto p_h14GetUserData=getUser;
int called,inside;void __attribute__((ms_abi)) native(const void*b,float,int){called++;inside=((u8*)b)[0x25c];}
'''
tail=r'''
int main(){o_s26btForceCallback=native;g_s26btBuoyancyReady=1;
 for(int h=0;h<2;h++){g_h34HandNewton[h]=wrappers[h];g_h34HandWrapper[h]=wrappers[h];g_h532ArmState[h]=2;g_h14GripBody[h]=wrappers[2+h];}
 for(auto&w:wrappers)w[0x25c]=1;
 s26bt_prepare_carried_bodies(1);
 for(int i=0;i<6;i++){s26bt_force_callback(wrappers[i],1.f/120,0);assert(inside==(i<4?0:1));assert(wrappers[i][0x25c]==1);}
 // Jointed mechanism, released prop and dormant hand retain native water forces.
 g_h15GripJointed[0]=1;g_h14GripBody[1]=nullptr;g_h532Dormant[0]=1;s26bt_prepare_carried_bodies(1);
 for(int i:{0,2,3}){s26bt_force_callback(wrappers[i],1.f/60,0);assert(inside==1);}
 s26bt_prepare_carried_bodies(0);for(int i=0;i<4;i++){s26bt_force_callback(wrappers[i],1.f/60,0);assert(inside==1);}
 xrOn=false;s26bt_prepare_carried_bodies(1);assert(!g_s26foHandBodies[1]);
 assert(called==13);puts("PASS existing liquid filter: exact hands/carried props, mechanism exclusion, release/dormancy, inactive cleanup, wrapper restoration");
}
'''
B=R/'build';cpp=B/'test_water_ownership_ig.cpp';cpp.write_text('#include <initializer_list>\n'+head+code+tail)
subprocess.run([sys.argv[1],'c++',str(cpp),'-o',str(B/'test_water_ownership_ig.exe')],check=True)
subprocess.run([str(B/'test_water_ownership_ig.exe')],check=True)
