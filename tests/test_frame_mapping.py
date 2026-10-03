from pathlib import Path
import json,subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=(R/'source/skeletal_q.inc').read_text();root=(R/'source/root_input_q.inc').read_text()
helpers=s[s.index('static i32 s26q_joint_position'):s.index('#include "root_input_q.inc"')]+root[root.index('static float s26q_root_dot'):root.index('static i32 s26q_root_angles')]+s[s.index('static i32 s26q_joint_bend'):s.index('#include "frame_curl_di.inc"')]
f=json.loads((R/'tests/fixtures/frame_reference_positions.json').read_text())
rows=[]
for key in ['0','1','2','8','10']:
 p=f['poses'][key];points=[p[2]]+p[2:27];assert len(points)==26
 rows.append('{'+','.join('{'+','.join(f'{x:.10g}f' if '.' in f'{x:.10g}' or 'e' in f'{x:.10g}' else f'{x}.0f' for x in v)+'}' for v in points)+'}')
# Use repr normalization to avoid invalid integer suffixes.
rows=[]
for key in ['0','1','2','8','10']:
 p=f['poses'][key];points=[p[2]]+p[2:27]
 rows.append('{'+','.join('{'+','.join(f'{x:.10e}f' for x in v)+'}' for v in points)+'}')
head=r'''
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
typedef uint64_t u64;typedef uint32_t u32;typedef int32_t i32;
typedef struct {float x,y,z;} V;typedef struct{float x,y,z,w;} Q;
typedef struct{Q orientation;V position;} Pose;
typedef struct{u64 flags;Pose pose;float radius;} S26QJoint;
#define ext_Sqrtf sqrtf
static float (*p_h5755blAtan2f)(float,float)=atan2f;
static int h5755bl_resolve_atan2f(void){return 1;}
static float clamp01(float v){return v<0?0:v>1?1:v;}
'''
main=r'''
static int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);return 1;}}while(0)
static void load(S26QJoint*j,int pose,int hand,float yaw,float pitch,float scale){
 memset(j,0,sizeof(S26QJoint)*26);
 for(int n=0;n<26;n++){float x=fixtures[pose][n][0]*(hand?1:-1)*scale,y=fixtures[pose][n][1]*scale,z=fixtures[pose][n][2]*scale;
 float yy=cosf(pitch)*y-sinf(pitch)*z,zz=sinf(pitch)*y+cosf(pitch)*z;
 j[n].pose.position=(V){cosf(yaw)*x+sinf(yaw)*zz+3,yy-2,-sinf(yaw)*x+cosf(yaw)*zz+1};j[n].flags=2;}
}

static void synth(S26QJoint*j,int h,int f,float total,float splay){
 int start=6+(f-1)*5;float wrist[3],ix[3],mi[3],li[3],a[3],b[3],normal[3],axis[3],u[3];
 s26q_joint_position(j+1,wrist);s26q_joint_position(j+7,ix);s26q_joint_position(j+12,mi);s26q_joint_position(j+22,li);
 for(int k=0;k<3;k++){a[k]=mi[k]-wrist[k];b[k]=ix[k]-li[k];}
 s26q_root_cross(a,b,normal);s26q_root_unit(normal);
 float p0[3],p1[3];s26q_joint_position(j+start,p0);s26q_joint_position(j+start+1,p1);
 for(int k=0;k<3;k++)u[k]=p1[k]-p0[k];s26q_root_unit(u);s26q_root_cross(u,normal,axis);s26q_root_unit(axis);
 for(int d=1;d<4;d++){
  float x[3],out[3],angle=(h?-1:1)*total/3;
  s26q_root_cross(axis,u,x);float dot=s26q_root_dot(axis,u);
  for(int k=0;k<3;k++)out[k]=u[k]*cosf(angle)+x[k]*sinf(angle)+axis[k]*dot*(1-cosf(angle));
  if(d==1&&splay!=0){s26q_root_cross(normal,out,x);dot=s26q_root_dot(normal,out);for(int k=0;k<3;k++)u[k]=out[k]*cosf(splay)+x[k]*sinf(splay)+normal[k]*dot*(1-cosf(splay));}
  else for(int k=0;k<3;k++)u[k]=out[k];
  V prev=j[start+d].pose.position;j[start+d+1].pose.position=(V){prev.x+u[0]*.025f,prev.y+u[1]*.025f,prev.z+u[2]*.025f};
 }
}
int main(void){S26QJoint j[26];float cv[4],old[4];
 for(int h=0;h<2;h++)for(int r=0;r<24;r++)for(int sc=0;sc<3;sc++)for(int f=1;f<5;f++){
  load(j,0,h,r*.27f,r*.13f,.75f+sc*.275f);C(s26di_frame_curl(j,h,f,cv));C(cv[0]==cv[1]);C(cv[1]<.0001f);C(cv[1]==cv[2]&&cv[2]==cv[3]);
  load(j,1,h,r*.27f,r*.13f,.75f+sc*.275f);C(s26di_frame_curl(j,h,f,cv));C(cv[1]>.9999f);C(cv[1]<=1);
  load(j,3,h,r*.27f,r*.13f,.75f+sc*.275f);C(s26di_frame_curl(j,h,f,cv));C(cv[1]>.1f&&cv[1]<.4f);
 }

 const float op[4]={.12683541f,.11057418f,.23616299f,.20579153f},cl[4]={4.82845678f,4.96191741f,4.85911875f,4.38118567f};
 for(int h=0;h<2;h++)for(int f=1;f<5;f++){
  float prev=-1;
  for(int n=0;n<=1000;n++){float t=n*.001f;load(j,0,h,.9f,-.6f,1);synth(j,h,f,op[f-1]+t*(cl[f-1]-op[f-1]),0);C(s26di_frame_curl(j,h,f,cv));C(fabsf(cv[1]-t)<.0001f);C(cv[1]>=prev-.00001f);prev=cv[1];}
  for(int n=-6;n<=6;n++){load(j,0,h,.4f,.9f,1);synth(j,h,f,0,n*.1f);C(s26di_frame_curl(j,h,f,cv));C(cv[1]==0);}
  load(j,0,h,.4f,.9f,1);synth(j,h,f,-.6f,0);C(s26di_frame_curl(j,h,f,cv));C(cv[1]==0);
 }
 for(int h=0;h<2;h++)for(int r=0;r<24;r++){
  load(j,0,h,r*.27f,r*.13f,1);C(s26di_frame_curl(j,h,0,cv));C(cv[0]<.0001f);C(cv[0]==cv[1]&&cv[1]==cv[2]&&cv[2]==cv[3]);
  load(j,1,h,r*.27f,r*.13f,1);C(s26di_frame_curl(j,h,0,cv));C(fabsf(cv[0]-.55f)<.0001f);
 }
 for(int pose=0;pose<5;pose++){load(j,pose,1,0,0,1);printf("reference pose %d:",pose);for(int f=1;f<5;f++){C(s26di_frame_curl(j,1,f,cv));C(s26q_retarget_finger(j,f,old));printf(" f%d old %.3f new %.3f",f,(old[1]+old[2]+old[3])/3,cv[1]);}puts("");}
 load(j,0,1,0,0,1);j[19].flags=0;C(!s26di_frame_curl(j,1,3,cv));
 load(j,0,1,0,0,1);j[19].pose.position.x=NAN;C(!s26di_frame_curl(j,1,3,cv));
 load(j,0,1,0,0,1);j[19].pose.position=j[18].pose.position;C(!s26di_frame_curl(j,1,3,cv));
 C(!s26di_frame_curl(j,-1,3,cv));C(!s26di_frame_curl(j,1,-1,cv));C(!s26di_frame_curl(j,1,5,cv));
 printf("PASS: %d production automatic Frame mapping checks\n",checks);return 0;}
'''
p=B/'test_frame_mapping.c';p.write_text(head+helpers+'\n#include "frame_curl_di.inc"\nstatic const float fixtures[5][26][3]={'+','.join(rows)+'};\n'+main)
exe=B/'test_frame_mapping.exe';subprocess.run([sys.argv[1],'cc','-O2','-I',str(R/'source'),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
assert 's26dh_rest' not in s
menu=(R/'runtime/script/modules/MenuHandler.hps').read_text();assert 'RESET FINGER TRACKING' in menu
print('PASS: no calibration dependency; mapping works before optional reset')
