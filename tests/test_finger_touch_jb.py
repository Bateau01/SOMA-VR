"""Production fingertip selection with mocked geometry; not native callback/collision proof."""
from pathlib import Path
import subprocess, sys, json
r=Path(__file__).resolve().parents[1]
code=r'''
#include <cmath>
#include <cstring>
#include <cstdio>
using i32=int;using u8=unsigned char;
struct Body {float gap[5];int icon,registered;unsigned char wrapper[0x300];} bodies[5];
struct Rocker {int active;} g_s26yRocker[5];
int g_s26yCount=0,calls=0;float curls[5];int hits[5],valids[5];
const void* g_h574RockerLatchBody[2];
#define H574_ROCKER_RELEASE_GAP_M .03f
#define H48_POKE_INDEX_CURL_MAX .6f
#define H485_SWITCH_RAY_M .025f
#define H482_POKE_SWITCH_ICON 13
#define H572_SWITCH_SKIN_TOUCH_M .01f
using PFN_H37_GetClosestEntity=u8(*)(void*,const float*,const float*,float,int,int,float*,void**,void**);
u8 ray(void*,const float* p,const float*,float,int,int,float*d,void**w,void**e){calls++;int f=(int)roundf(p[0]);if(hits[f]<0)return 0;Body*b=&bodies[hits[f]];*d=.001f;*w=b->wrapper;*e=b;return 1;}
void* h37_map_helper(PFN_H37_GetClosestEntity*f){*f=ray;return bodies;}
int s26jb_raw_finger(int,int f,const float*,float p[5][3],int*len){*len=4;memset(p,0,60);for(int j=0;j<5;j++){p[j][0]=(float)f;p[j][2]=.01f*j;}return valids[f];}
float h10_raw_finger_input(int,int f){return curls[f];}
float s26jb_finger_skin_radius(int,int,int){return .008f;}
int h10_norm3(float*d){float n=sqrtf(d[0]*d[0]+d[1]*d[1]+d[2]*d[2]);if(n<1e-6)return 0;for(int a=0;a<3;a++)d[a]/=n;return 1;}
int h37_native_wrapper_matches_entity(void*w,void*e){return w&&e;}
int h20_mem_readable(void*p,unsigned){return p!=nullptr;}
int s26y_body_slot(const void*p){return ((Body*)p)->registered;}
int h483_surface_target_info(void*,void*e,int*icon,const void**b,void**can,void**on){*b=e;*icon=((Body*)e)->icon;return *icon>=0;}
int h14_point_to_body(const void*b,const float*p,float*gap,float*){*gap=((Body*)b)->gap[(int)roundf(p[0])];return 1;}
int s26eq_return_point(const void*b,const float*p,float*g,float*c){return h14_point_to_body(b,p,g,c);}
'''+(r/'source/finger_touch_jb.inc').read_text()+r'''
void reset(){calls=0;g_s26yCount=0;memset(curls,0,sizeof curls);memset(g_h574RockerLatchBody,0,sizeof g_h574RockerLatchBody);
for(int f=0;f<5;f++){valids[f]=1;hits[f]=-1;bodies[f].icon=13;bodies[f].registered=-1;g_s26yRocker[f].active=1;*(void**)(bodies[f].wrapper+0x2e8)=&bodies[f];for(int j=0;j<5;j++)bodies[f].gap[j]=.01f;}}
int choose(int h){float p[5][3],m[16]={0};int len;return s26jb_choose_touch_finger(h,m,p,&len);}
int main(){
 for(int h=0;h<2;h++)for(int f=0;f<5;f++){reset();hits[f]=f;if(choose(h)!=f)return 1;if(calls!=5)return 2;}
 reset();for(int f=0;f<5;f++)hits[f]=0;if(choose(0)!=1)return 3; // one winner, index tie priority
 reset();hits[4]=4;bodies[4].icon=17;if(choose(0)!=1)return 4; // extra finger cannot enter a terminal
 reset();hits[3]=3;bodies[3].gap[3]=.1f;if(choose(0)!=1)return 5; // no remote press
 reset();hits[2]=2;curls[2]=1;if(choose(0)!=1)return 6;
 reset();for(int f=0;f<5;f++)curls[f]=1;if(choose(0)!=-1)return 7;
 reset();g_h574RockerLatchBody[0]=&bodies[0];for(int f=0;f<5;f++){bodies[0].gap[f]=.2f;curls[f]=1;}
 bodies[0].gap[4]=0;if(choose(0)!=4||calls)return 8; // curled/interior contact still retains accepted latch
 reset();hits[0]=0;bodies[0].registered=0;g_s26yCount=1;if(choose(1)!=0)return 9;
 g_s26yRocker[0].active=0;if(choose(1)!=1)return 10;
 reset();hits[3]=3;valids[3]=0;if(choose(0)!=1)return 11;
 puts("PASS: both hands/all fingers, one winner, curl/range/permission exclusions, index fallback, latch retention");
}
'''
b=r/'build/jb_finger_touch.cpp';b.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(b),'-o',str(b.with_suffix('.exe'))],check=True)
v=subprocess.run([str(b.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-finger-touch.json').write_text(json.dumps(dict(scope=__doc__,exit=v.returncode,output=v.stdout),indent=2))
print(v.stdout);raise SystemExit(v.returncode)
