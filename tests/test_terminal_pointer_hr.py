"""Production pointer-step and sampler with mocked tracking/event sink, not native GUI proof."""
from pathlib import Path
import re, subprocess, sys, json
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text()
start=s.index('static void h576bo_terminal_pointer_step(void){')
end=s.index('\n}\n',start)+2
step=s[start:end]
names=set(re.findall(r'\bg_\w+',step))
arrays={'g_s26hrTerminalSamples','g_h576bsTerminalNearStep','g_h576acSpecialPulses'}
names-=arrays|{'g_s26TerminalImGui'}
code=r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;
#define H576BO_EDGE_SLOP_NORM .03f
#define H5755GJ_CONTROL_PRETOUCH_SKIN_M .012f
#define H576BP_SURFACE_CAPTURE_M .012f
#define H576BO_FRONT_RELEASE_SKIN_M .024f
#define H576BO_BACK_PENETRATION_M .06f
#define H576AC_HAPTIC_CONFIRM 1
struct S26HRTerminalSample{float u,v,p,r;u32 frame,generation;const void*gui;u8 valid;float sweepSide;};
S26HRTerminalSample g_s26hrTerminalSamples[2];
unsigned g_h576bsTerminalNearStep[2],g_h576acSpecialPulses[2];
void* g_s26TerminalImGui=(void*)1;
bool paused=false,active=true,accept=true;
float tip[2][4]={{.4,.6,.05,.008},{.4,.6,.05,.008}};int valid[2]={1,0};
int downs,ups,checks;
int h9_good(float v,float lim){return std::isfinite(v)&&fabsf(v)<lim;}
void zero_bytes(void*p,unsigned n){memset(p,0,n);}
int h5754h_pause_active(){return paused;}
int h5730_exact_terminal_state(int,int,int,int){return active;}
float h5755ea_world_units_per_meter(){return 1;}
int h576bo_terminal_tip(int h,float*u,float*v,float*p,float*r){*u=tip[h][0];*v=tip[h][1];*p=tip[h][2];*r=tip[h][3];return valid[h];}
int h576bo_push_motion(float,float){return accept;}
int h576bo_push_button(int down){if(!accept)return 0;if(down)downs++;else ups++;return 1;}
void h576ac_queue_haptic(int,int){}
void ext_Log(const char*,...){}
#define C(x) do{checks++;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
'''
code+='\n'.join('int '+n+';' for n in sorted(names))
code+=r'''
void h576bo_release_pointer(int keep,const char*){
 if(!keep)zero_bytes(g_s26hrTerminalSamples,sizeof(g_s26hrTerminalSamples));
 else for(int h=0;h<2;h++)g_s26hrTerminalSamples[h].valid=0;
 if(g_h576boPointerDown){h576bo_push_button(0);g_h576boPointerDown=0;}
 g_h576boPointerHand=-1;g_h576boPointerSide=1;g_h576boHaveLast=0;
}
'''
code+=(R/'source/terminal_sweep_hr.inc').read_text()+step
code+=r'''
void frame(){++g_frameCounter;h576bo_terminal_pointer_step();}
void reset(){h576bo_release_pointer(0,"");downs=ups=0;active=true;accept=true;g_h576boTerminalSurfaceValid=1;g_s26hdLaserHand=-1;g_h576boEntryHand=-1;}
int main(){
 for(int hand=0;hand<2;hand++){
  reset();valid[hand]=1;valid[1-hand]=0;tip[hand][2]=.05;frame();C(downs==0);
  tip[hand][2]=-.05;frame();C(downs==1&&g_h576boPointerHand==hand);
  tip[hand][2]=-.08;frame();C(ups==1&&!g_h576boPointerDown);
  tip[hand][2]=-.01;frame();tip[hand][2]=.01;frame();C(downs==1);
  tip[hand][2]=.05;frame();tip[hand][2]=.01;frame();C(downs==2);
  active=false;frame();C(ups==2&&!g_h576boPointerDown);
  active=true;tip[hand][2]=.05;frame();tip[hand][2]=.01;frame();C(downs==3);
  valid[hand]=0;frame();C(ups==3&&!g_h576boPointerDown);
 }
 reset();valid[0]=1;valid[1]=0;tip[0][2]=.05;frame();
 accept=false;tip[0][2]=-.05;frame();C(!g_h576boPointerDown&&downs==0);
 accept=true;tip[0][2]=.05;frame();tip[0][2]=.01;frame();C(downs==1);
 printf("PASS %d production pointer assertions\n",checks);
}
'''
p=R/'build/terminal_pointer_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence/terminal_pointer_hr.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
