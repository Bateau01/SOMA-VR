from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1];W=R.parent;(R/'build').mkdir(exist_ok=True);(R/'audit').mkdir(exist_ok=True)
def fn(s,name):
 m=re.search(r'(?m)^static [^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s);assert m,name
 start=m.start();a=s.index('{',m.start());depth=0
 for i in range(a,len(s)):
  depth+=(s[i]=='{')-(s[i]=='}')
  if not depth:return s[start:i+1]
header=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
typedef struct{int parent;} Joint;
typedef struct{int jointCount;float pivot[3];Joint joints[32];}H10Skin;
typedef struct{int dummy;}H5730TString;
static float metric=1,submitted[2][16],source[2][16];
static H10Skin skins[2];
static void *g_s26NativeMesh[2],*g_h14GripBody[2],*g_s26NativeBones[2][32];
static i32 g_s26NativeFamily[2],g_h5748Family=0,g_s26MeshCapture,g_s26MeshSuccess,g_s26MeshReady=1,g_s26ManualHeal;
static u8 g_s26NativeHandVisible[2];static u32 g_s26NativeMeshLogs;
static u32 g_h14PhysicsSteps=1000;
static float h18_joint_input(int h,int f,int d){(void)h;(void)d;return f==2?1.0f:0.0f;}
static int calls[2],boneCalls,resetCalls,allowed=1,poseOK=1;
static float h5755ea_world_units_per_meter(void){return metric;}
static H10Skin* p2_skin(void){return skins;}
static int s26_native_hand_allowed(int h){return allowed&&h>=0&&h<2;}
static int h31_virtual_hand_model(int h,float*m){memcpy(m,source[h],64);return poseOK;}
static int h5755cu_render_hand_model(int h,float*m){memcpy(m,source[h],64);return poseOK;}
static void h576bt_probe_rocker_render_tip(int h,float*m){(void)h;(void)m;}
static void h10_build_rig(int h){(void)h;}
static void s26_local_hand_pose(int h,int j,float*m){(void)h;(void)j;memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;m[12]=2;m[13]=3;m[14]=4;}
static void h5730_literal_string(H5730TString*s,const char*n){(void)s;(void)n;}
static void* boneNamed(void*m,const H5730TString*s){(void)s;return m;}
static void nodeMatrix(void*n,const float*m,u8 b){(void)n;(void)b;boneCalls++;if(fabsf(m[3]-.02f)>1e-7f)exit(3);}
static void meshMatrix(void*mesh,const float*m){int h=mesh==(void*)2;memcpy(submitted[h],m,64);calls[h]++;}
static void meshReset(void*m){(void)m;resetCalls++;}
static void coverage(void*m,float c){(void)m;(void)c;}
static void (*o_s26MeshCoverage)(void*,float)=coverage;
static void*(*p_s26BoneNamed)(void*,const H5730TString*)=boneNamed;
static void(*p_s26NodeMatrix)(void*,const float*,u8)=nodeMatrix;
static void(*p_s26MeshMatrix)(void*,const float*)=meshMatrix;
static void(*p_s26MeshReset)(void*)=meshReset;
#define ext_Log(...) ((void)0)
'''
main=r'''
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line %d scale=%f heal=%d held=%d\n",__LINE__,metric,g_s26ManualHeal,g_h14GripBody[0]!=0);return 1;}}while(0)
int main(void){
 for(int h=0;h<2;h++){g_s26NativeMesh[h]=(void*)(size_t)(h+1);g_s26NativeFamily[h]=0;skins[h].jointCount=2;for(int j=0;j<2;j++){skins[h].joints[j].parent=-1;g_s26NativeBones[h][j]=(void*)1;}
  source[h][0]=.6f;source[h][1]=.8f;source[h][4]=-.8f;source[h][5]=.6f;source[h][10]=1;source[h][15]=1;source[h][12]=13+h;source[h][13]=-8;source[h][14]=6;
 }
 for(int family=0;family<4;family++)for(int percent=50;percent<=200;percent+=5){
  metric=100.f/percent;g_h5748Family=family;
  for(int mode=0;mode<6;mode++){
   g_s26ManualHeal=(mode==3);g_h14GripBody[0]=(mode==1||mode==2||mode==3)?(void*)3:0;g_h14GripBody[1]=(mode==2)?(void*)3:0;
   for(int h=0;h<2;h++){g_s26MeshCapture=h;s26_mesh_coverage_detour(g_s26NativeMesh[h],1);CHECK(g_s26MeshSuccess&&g_s26NativeHandVisible[h]);
    for(int r=0;r<4;r++)for(int c=0;c<4;c++){float expected=source[h][c*4+r]*((r<3&&c<3)?metric:1);CHECK(fabsf(submitted[h][r*4+c]-expected)<1e-6f);}
   }
   float before[2][16];memcpy(before,submitted,sizeof(before));s26_refresh_native_held_pose();
   for(int h=0;h<2;h++)for(int k=0;k<16;k++)CHECK(fabsf(submitted[h][k]-before[h][k])<1e-6f);
  }
 }
 allowed=0;int old=calls[0];g_s26MeshCapture=0;s26_mesh_coverage_detour((void*)1,1);CHECK(calls[0]==old);
 allowed=1;poseOK=0;g_s26MeshCapture=0;s26_mesh_coverage_detour((void*)1,1);CHECK(calls[0]==old);
 printf("PASS %u checks: both hands, four families, 31 slider values, free/grab/two-hand/heal/release transitions; native refresh does not double-scale; positions and bone-local units unchanged.\n",checks);return 0;
}
'''
results={}
for label,path in [('before',R/'tests/fixtures/s26bx_before.c'),('after',R/'source/s26n.c')]:
 s=path.read_text(encoding='utf-8');code=header+'\n'.join(fn(s,n) for n in ['s26bb_scale_visual_basis','s26_refresh_native_held_pose','s26_mesh_coverage_detour'])+main
 p=R/'build'/f'test_{label}.c';p.write_text(code);exe=p.with_suffix('.exe')
 subprocess.run([sys.argv[1],'cc','-O2','-Wall','-Wextra','-Werror','-Wno-unused-variable','-Wno-unused-function',str(p),'-o',str(exe)],check=True)
 v=subprocess.run([str(exe)],capture_output=True,text=True);results[label]={'exit':v.returncode,'stdout':v.stdout,'stderr':v.stderr};print(label,v.returncode,v.stdout)
assert results['before']['exit']==1,'Test must reproduce the original missing compensation'
assert results['after']['exit']==0
(R/'audit/native_hand_scale_tests.json').write_text(json.dumps(results,indent=2))
