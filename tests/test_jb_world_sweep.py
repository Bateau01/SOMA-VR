"""Extracted production sweep dispatch guards; mocked ray/native permission, not gameplay proof."""
from pathlib import Path
import subprocess, sys, json
r=Path(__file__).resolve().parents[1]
helper=(r/'source/world_touch_sweep_jb.inc').read_text().split('/* Store each eligible fingertip')[0]
code=r'''
#include <cmath>
#include <cstdio>
#include <cstring>
typedef int i32; typedef unsigned char u8; typedef unsigned u32;
unsigned g_h14PhysicsSteps,g_frameCounter;
struct Rocker{int active;} g_s26yRocker[1]={{1}};
int g_s26yCount=1,g_s26CutsceneHandsHidden=0,g_lastSyncResult=0;
int gate=1,native=0,pause=0,registered=1,identity=1,readable=1,calls=0,rays=0,permission=1;
float metric=1,lastSample[3]; unsigned char wrapper[0x300];
struct S26HDHit{const void* body;float t;}; S26HDHit answer={(void*)1,.6f};
int s26y_gate(){return gate;} int ni_native_input(){return native;} int h5754h_pause_active(){return pause;}
float h5755ea_world_units_per_meter(){return metric;}
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
int h9_good(float x,float limit){return std::isfinite(x)&&std::fabs(x)<=limit;}
float ext_Sqrtf(float x){return std::sqrt(x);}
S26HDHit s26hd_ray(const float*,const float*){rays++;return answer;}
int s26y_body_slot(const void*){return registered?0:-1;}
void* p_h14GetUserData(const void*){return wrapper;}
int h20_mem_readable(const void*,unsigned){return readable;}
int h37_native_wrapper_matches_entity(void*,void*){return identity;}
float s26jb_finger_skin_radius(int,int,int){return .01f*metric;}
void ext_Log(const char*,...){}
int s26hr_control_contact(int,void*,void*,const float*p,const float*,int,float){calls++;memcpy(lastSample,p,sizeof(lastSample));return permission;}
'''+helper+r'''
int checks=0;
#define C(x) do{checks++;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
int main(){
 g_h14PhysicsSteps=10;g_frameCounter=10;C(!s26jb_poke_contiguous(0,0));
 g_h14PhysicsSteps=11;C(s26jb_poke_contiguous(0,1));
 C(!s26jb_poke_contiguous(0,1)); // duplicate step
 g_h14PhysicsSteps=13;C(!s26jb_poke_contiguous(0,1)); // omitted step
 g_h14PhysicsSteps=14;g_frameCounter=13;C(!s26jb_poke_contiguous(0,1)); // pause/render gap
 g_h14PhysicsSteps=15;C(!s26jb_poke_contiguous(0,0)); // world/finger invalidation
 C(!s26jb_poke_contiguous(1,0)); // independent other hand
 g_h14PhysicsSteps=16;C(s26jb_poke_contiguous(1,1));
 float tip[3]={0,0,-.04f},delta[3]={0,0,-.10f},dir[3]={0,0,-1};
 C(s26jb_world_sweep(1,1,4,tip,delta,dir)==1);C(calls==1);C(std::fabs(lastSample[2]-.011f)<.00001f);
 int old=calls;answer.body=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));C(calls==old);answer.body=(void*)1;
 registered=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));C(calls==old);registered=1;
 g_s26yRocker[0].active=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));C(calls==old);g_s26yRocker[0].active=1;
 answer.t=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));answer.t=1;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));answer.t=.6f;
 answer.t=NAN;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));answer.t=.6f;
 identity=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));identity=1;readable=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));readable=1;
 dir[2]=1;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));dir[2]=-1;
 delta[2]=-.151f;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));delta[2]=-.014f;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));delta[2]=-.10f;
 int* gates[]={&native,&pause,&g_s26CutsceneHandsHidden,&g_lastSyncResult};
 for(int* v:gates){*v=1;int before=rays;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));C(rays==before);*v=0;}
 gate=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));gate=1;g_s26yCount=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));g_s26yCount=1;
 permission=0;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));C(calls==old+1);permission=1;
 permission=2;C(!s26jb_world_sweep(1,1,4,tip,delta,dir));permission=1;
 metric=.5f;delta[2]=-.05f;tip[2]=-.02f;C(s26jb_world_sweep(0,4,3,tip,delta,dir));C(std::fabs(lastSample[2]-.0055f)<.00001f);
 printf("PASS %d sweep guard assertions\n",checks);
}
'''
p=r/'build/jb_world_sweep.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-world-sweep-guards.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
