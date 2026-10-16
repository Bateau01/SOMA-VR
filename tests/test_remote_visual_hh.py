from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/accessibility_hd.inc').read_text();a=s.index('static void s26hd_draw(');b=s.index('\n/* Native AddEdgeGlowObject',a)
c=r'''
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include <cstring>
using u8=unsigned char;using i32=int;using u32=unsigned;
int checks,draws,meshes,paused,pose[2]={1,1};
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
int g_s26hlInteractionEnabled;int g_s26hdRemoteEnabled,g_s26hdLaserEnabled,g_s26CutsceneHandsHidden,g_h5755bhPresentationState=2;
enum{H5755BH_GAMEPLAY_VR=2};unsigned g_h14PhysicsSteps=10,g_s26hdBeamStep[2]={10,10},g_s26hdBeamKind[2];
float g_s26hdBeamStart[2][3],g_s26hdBeamEnd[2][3];int g_h576apDebugPlaneStart,g_s26fyDebugRearStart=4;
int h5754h_pause_active(){return paused;}int visual_pose_valid(int h){return pose[h];}int s26hi_build_visuals(){meshes++;return 1;}
void h10_identity(float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;}void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*4);}
float h5755ea_world_units_per_meter(){return 1;}void s26hi_solid(const float*m,int first,int count,float,float,float){CHECK((first==0&&count==72)||(first==72&&count==576));for(int i=0;i<16;i++)CHECK(std::isfinite(m[i]));draws++;}
float h9_abs(float x){return fabsf(x);}float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}int h10_norm3(float*d){float n=h10_len3(d[0],d[1],d[2]);for(int i=0;i<3;i++)d[i]/=n;return 1;}
unsigned char ext_glIsEnabled(unsigned){return 1;}void ext_glEnable(unsigned){}void ext_glDisable(unsigned){}
'''+s[a:b]+r'''
int main(){g_s26hdBeamEnd[0][2]=g_s26hdBeamEnd[1][2]=-2;
 for(int remote=0;remote<2;remote++)for(int laser=0;laser<2;laser++)for(int interaction=0;interaction<2;interaction++)for(unsigned left=0;left<4;left++)for(unsigned right=0;right<4;right++){
 g_s26hlInteractionEnabled=interaction;g_s26hdRemoteEnabled=remote;g_s26hdLaserEnabled=laser;g_s26hdBeamKind[0]=left;g_s26hdBeamKind[1]=right;draws=meshes=0;s26hd_draw();
 int targets=(laser?((left==2)+(right==2)):0)+(interaction?((left==3)+(right==3)):0);CHECK(draws==2*targets);CHECK(meshes==targets);}
 g_s26hdLaserEnabled=1;g_s26hdBeamKind[0]=g_s26hdBeamKind[1]=2;
 for(int reason=0;reason<4;reason++){draws=0;if(reason==0)paused=1;if(reason==1)g_s26CutsceneHandsHidden=1;if(reason==2)g_h5755bhPresentationState=0;if(reason==3)pose[0]=pose[1]=0;s26hd_draw();CHECK(!draws);paused=g_s26CutsceneHandsHidden=0;g_h5755bhPresentationState=2;pose[0]=pose[1]=1;}
 g_s26hdBeamStep[0]=g_s26hdBeamStep[1]=9;draws=0;s26hd_draw();CHECK(!draws);
 printf("PASS %d remote/terminal visual separation checks\n",checks);
}
'''
p=r/'build/remote_visual_hh.cpp';p.write_text(c);subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout+v.stderr);(r/'audit/remote_visual_hh.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production draw function with render-call recorder. Verifies beam/dot suppression and terminal preservation; no pixel/headset claim.'},indent=2));raise SystemExit(v.returncode)

