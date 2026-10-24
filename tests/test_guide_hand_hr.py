"""Extracted guide bone dispatch with mocked native methods; proves scope/ownership, not appearance."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1]
code=r'''
#include <cstdio>
#include <cstdlib>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;using u64=unsigned long long;
struct Joint{int parent;float local[16];};struct H10Skin{int jointCount;Joint joints[32];float pivot[3];};
H10Skin skin[2];int g_s26MeshReady=1,allowed=1,calls,resets,missing=-1,named;int g_chainOf[2][32],g_chainLabel[2][5],g_chainLen[2][5],g_chainDepth[2][32];
struct H5730TString{const char*p;};int ghost,live,bone[32];
H10Skin*p2_skin(){return skin;}int s26_native_hand_allowed(int h){return allowed&&h>=0&&h<2;}
void h5730_literal_string(H5730TString*s,const char*p){s->p=p;}
void* find(void*m,const H5730TString*s){if(m!=&ghost)abort();int j=(s->p[4]-'0')*10+s->p[5]-'0';named++;return j==missing?nullptr:&bone[j];}
auto p_s26BoneNamed=find;
void node(void*p,const float*m,int){if(p<&bone[0]||p>&bone[31])abort();calls++;if(m[15]!=1)abort();}
auto p_s26NodeMatrix=node;
void reset(void*m){if(m!=&ghost)abort();resets++;}auto p_s26MeshReset=reset;
void h10_build_rig(int){}void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
void h10_matmul(const float*a,const float*b,float*c){for(int j=0;j<16;j++)c[j]=b[j];}
int expectedPose;
void s26q_apply_joint_pose(int,int,int finger,int,int,float curl,u64 root,float*){if(root)abort();float expected=(expectedPose==1 || (expectedPose==2&&finger!=1))?1.0f:0.0f;if(curl!=expected)abort();}
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
'''+(R/'source/guide_hand_hr.inc').read_text()+r'''
int main(){for(int h=0;h<2;h++){skin[h].jointCount=4;for(int j=0;j<4;j++){g_chainOf[h][j]=j;g_chainLabel[h][j]=j;skin[h].joints[j].parent=j-1;skin[h].joints[j].local[0]=skin[h].joints[j].local[5]=skin[h].joints[j].local[10]=skin[h].joints[j].local[15]=1;}}
 C(!s26hr_guide_pose(&live));C(calls==0&&resets==0);
 for(int h=0;h<2;h++)for(int fist=0;fist<3;fist++){
 calls=resets=named=0;g_s26hrGuideHand=h;g_s26hrGuideFist=fist;expectedPose=fist;
 C(s26hr_guide_pose(&ghost)==1);C(g_s26hrGuideHand==-1);C(g_s26hrGuideSuccess==1);C(calls==4&&resets==1&&named==4);
 C(s26hr_guide_pose(&live)==0);C(calls==4);
 }
 calls=resets=0;missing=2;g_s26hrGuideHand=0;C(s26hr_guide_pose(&ghost)==1);C(!g_s26hrGuideSuccess&&calls==0&&resets==0);
 missing=-1;allowed=0;g_s26hrGuideHand=1;C(s26hr_guide_pose(&ghost)==1);C(!g_s26hrGuideSuccess&&calls==0&&resets==0);
 printf("PASS %d guide-only bone dispatch assertions\n",checks);
}
'''
p=R/'build/guide_hand_hr.cpp';p.write_text(code);exe=p.with_suffix('.exe');subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True);r=subprocess.run([str(exe)],capture_output=True,text=True);(R/'docs/v109-evidence/guide_hand_dispatch_hr.json').write_text(json.dumps({'scope':__doc__,'exit':r.returncode,'output':r.stdout+r.stderr},indent=2));print(r.stdout+r.stderr);raise SystemExit(r.returncode)
