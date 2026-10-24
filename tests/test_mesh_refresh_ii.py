from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('static void s26_refresh_native_held_pose(void){');b=s.index('\nstatic void __attribute__((ms_abi)) s26_mesh_coverage_detour',a);fn=s[a:b]
head=r"""
#include <cstdio>
#include <cstring>
#undef NDEBUG
#include <cassert>
using i32=int;using u32=unsigned;
int g_s26MeshReady=1,g_s26ManualHeal=0,g_s26NativeHandVisible[2]={1,1};
void*g_h14GripBody[2]={};void*g_s26NativeMesh[2]={(void*)1,(void*)2};
bool allowed[2]={true,true};float body[2][16],mesh[2][16];int reads=0,writes=0;
bool s26_native_hand_allowed(int h){return allowed[h];}
int h31_virtual_hand_model(int h,float*m){reads++;memcpy(m,body[h],64);return 1;}
void s26bb_scale_visual_basis(float*){} void s26ih_hand(u32,const float*){}
void writeMesh(void*p,const float*m){writes++;memcpy(mesh[(size_t)p-1],m,64);}auto p_s26MeshMatrix=writeMesh;
"""
tail=r"""
int main(){
 for(int h=0;h<2;h++)body[h][0]=body[h][5]=body[h][10]=body[h][15]=1;
 // Neither hand held: actual helper intentionally does no work.
 s26_refresh_native_held_pose();assert(reads==0&&writes==0);
 g_h14GripBody[1]=(void*)3;body[1][12]=.5f;
 s26_refresh_native_held_pose();assert(mesh[1][3]==.5f&&writes==1);
 // Rendering twice without another accepted body pose cannot invent motion.
 float saved[16];memcpy(saved,mesh[1],64);s26_refresh_native_held_pose();assert(!memcmp(saved,mesh[1],64));
 // New body pose is copied exactly, no easing or interpolation.
 body[1][12]=.7f;s26_refresh_native_held_pose();assert(mesh[1][3]==.7f);
 // Independent second hand and no writes back to either body.
 g_h14GripBody[0]=(void*)4;body[0][12]=-.2f;s26_refresh_native_held_pose();assert(mesh[0][3]==-.2f&&mesh[1][3]==.7f);assert(body[0][12]==-.2f&&body[1][12]==.7f);
 for(int mode=0;mode<4;mode++){int w=writes;if(mode==0)g_s26MeshReady=0;if(mode==1)g_s26ManualHeal=1;if(mode==2)allowed[0]=allowed[1]=false;if(mode==3)g_s26NativeMesh[0]=g_s26NativeMesh[1]=nullptr;s26_refresh_native_held_pose();assert(writes==w);g_s26MeshReady=1;g_s26ManualHeal=0;allowed[0]=allowed[1]=true;}
 puts("PASS extracted held-mesh refresh: unchanged body yields unchanged mesh, exact new pose, independent hands, hidden/heal/invalid gates. Body-source mocked; not a Newton or headset test.");
}
"""
p=R/'build/test_mesh_refresh_ii.cpp';p.write_text(head+fn+tail);exe=p.with_suffix('.exe');subprocess.run([sys.argv[1],'c++',str(p),'-O2','-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
