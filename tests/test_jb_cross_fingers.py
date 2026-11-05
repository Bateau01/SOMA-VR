"""Extracted per-finger crossing sample ownership; mocked ray, no gameplay proof."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
helper=(r/'source/world_touch_sweep_jb.inc').read_text().split('/* Store each eligible fingertip')[1]
helper='/* Store each eligible fingertip'+helper
code=r'''
#include <cmath>
#include <cstdio>
#include <cstring>
using i32=int;using u8=unsigned char;
int g_s26yCount=1;
float g_s26jbTouchPoints[2][5][5][3];
int g_s26jbTouchLengths[2][5],g_s26jbTouchValid[2][5];
float curl[2][5];
#define H48_POKE_INDEX_CURL_MAX .5f
float h10_raw_finger_input(int h,int f){return curl[h][f];}
int h10_norm3(float*v){float d=std::sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);if(d<.00001f)return 0;for(int a=0;a<3;a++)v[a]/=d;return 1;}
int chosen=-1,calls,mask,checks;
int s26jb_world_sweep(int,int f,int,const float*,const float*d,const float*){calls++;if(std::fabs(d[2])<.015f)return 0;if(mask&(1<<f)){chosen=f;return 1;}return 0;}
'''+helper+r'''
#define C(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
void setup(){memset(g_s26jbCrossValid,0,sizeof(g_s26jbCrossValid));memset(g_s26jbTouchPoints,0,sizeof(g_s26jbTouchPoints));memset(curl,0,sizeof(curl));chosen=-1;calls=0;mask=0;g_s26yCount=1;for(int h=0;h<2;h++)for(int f=0;f<5;f++){g_s26jbTouchValid[h][f]=1;g_s26jbTouchLengths[h][f]=1;g_s26jbTouchPoints[h][f][1][2]=-.01f;}}
int main(){
 for(int h=0;h<2;h++)for(int f=0;f<5;f++){
  setup();mask=1<<f;C(!s26jb_cross_fingers(h,0));C(calls==0);
  g_s26jbTouchPoints[h][f][1][2]-=.1f;
  C(s26jb_cross_fingers(h,1));C(chosen==f);
  chosen=-1;C(!s26jb_cross_fingers(h,1));C(chosen==-1);
  C(!s26jb_cross_fingers(1-h,1)); // no other-hand history
 }
 setup();mask=31;C(!s26jb_cross_fingers(0,0));for(int f=0;f<5;f++)g_s26jbTouchPoints[0][f][1][2]-=.1f;
 C(s26jb_cross_fingers(0,1));C(chosen==1);C(calls==1); // one winner, index tie priority
 setup();mask=16;C(!s26jb_cross_fingers(0,0));g_s26jbTouchPoints[0][4][1][2]-=.1f;curl[0][4]=1;C(!s26jb_cross_fingers(0,1));curl[0][4]=0;C(!s26jb_cross_fingers(0,1));
 setup();mask=16;C(!s26jb_cross_fingers(0,0));g_s26jbTouchPoints[0][4][1][2]-=.1f;C(!s26jb_cross_fingers(0,0));C(!s26jb_cross_fingers(0,1));
 setup();mask=16;C(!s26jb_cross_fingers(0,0));g_s26yCount=0;C(!s26jb_cross_fingers(0,1));g_s26yCount=1;g_s26jbTouchPoints[0][4][1][2]-=.1f;C(!s26jb_cross_fingers(0,1));
 printf("PASS %d per-finger history assertions\n",checks);
}
'''
p=r/'build/jb_cross_fingers.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-cross-finger-guards.json').write_text(json.dumps(dict(scope=__doc__,exit=v.returncode,output=v.stdout+v.stderr),indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
