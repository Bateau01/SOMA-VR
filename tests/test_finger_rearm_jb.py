"""Extracted registered-control rearm logic; mocked contact queries, no native callbacks."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
s=(r/'source/rocker_y.inc').read_text()
a=s.index('static void s26y_rearm(void)');b=s.index('static i32 s26y_near_gate',a)
code=r'''
#include <cstring>
#include <cstdio>
using i32=int;using u32=unsigned;using u8=unsigned char;
struct S26YRocker {int used,blocked;const void* raw;void* wrapper;u32 id;int handMask;} g_s26yRocker[2];
int g_s26yCount=1,g_lastSyncResult=0,gate=1,pause=0;
float gap[2][5],palms[2],scale=1;int tracking[2],queries;
unsigned char wrapper[0x300];int body;
int s26y_gate(){return gate;}int h5754h_pause_active(){return pause;}
int visual_pose_valid(int h){return tracking[h];}
int h14_hand_pose_raw(int h,float*,float*m){m[0]=(float)h;return tracking[h];}
int s26jb_raw_finger(int h,int f,const float*,float p[5][3],int*l){*l=4;p[4][0]=(float)h;p[4][1]=(float)f;return 1;}
int s26eq_return_point(const void*,const float*p,float*g,float*){queries++;int h=(int)p[0],f=(int)p[1];*g=f==5?palms[h]:gap[h][f];return 1;}
int h20_mem_readable(void*p,unsigned){return p!=nullptr;}
float s26jb_finger_skin_radius(int,int,int){return .008f*scale;}
float h5755ea_world_units_per_meter(){return scale;}
int s26hr_control_palm(int h,float*p,float*){p[0]=(float)h;p[1]=5;return tracking[h];}
'''+s[a:b]+r'''
void reset(){gate=1;pause=0;g_lastSyncResult=0;scale=1;queries=0;
 memset(wrapper,0,sizeof wrapper);*(const void**)(wrapper+0x2e8)=&body;*(u32*)(wrapper+0x3c)=42;
 g_s26yRocker[0]={1,1,&body,wrapper,42,1};
 for(int h=0;h<2;h++){tracking[h]=1;palms[h]=.2f;for(int f=0;f<5;f++)gap[h][f]=.2f;}}
int main(){
 for(int h=0;h<2;h++)for(int f=0;f<5;f++){reset();gap[h][f]=0;s26y_rearm();if(!g_s26yRocker[0].blocked)return 1;gap[h][f]=.2f;s26y_rearm();if(g_s26yRocker[0].blocked||g_s26yRocker[0].handMask)return 2;}
 reset();palms[1]=.04f;s26y_rearm();if(!g_s26yRocker[0].blocked)return 3;
 reset();tracking[1]=0;s26y_rearm();if(!g_s26yRocker[0].blocked)return 4;
 reset();*(u32*)(wrapper+0x3c)=43;s26y_rearm();if(!g_s26yRocker[0].blocked||queries)return 5;
 reset();g_lastSyncResult=1;s26y_rearm();if(queries||!g_s26yRocker[0].blocked)return 6;
 reset();scale=2;gap[0][4]=.07f;s26y_rearm();if(!g_s26yRocker[0].blocked)return 7;
 reset();pause=1;s26y_rearm();if(queries)return 8;
 puts("PASS: all ten fingertips retain latch, complete withdrawal rearms, palm/tracking/lifetime/pause/scale exclusions");
}
'''
f=r/'build/jb_finger_rearm.cpp';f.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(f),'-o',str(f.with_suffix('.exe'))],check=True)
v=subprocess.run([str(f.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-finger-rearm.json').write_text(json.dumps(dict(scope=__doc__,exit=v.returncode,output=v.stdout),indent=2))
print(v.stdout);raise SystemExit(v.returncode)

