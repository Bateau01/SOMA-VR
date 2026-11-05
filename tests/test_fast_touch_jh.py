"""Extracted contact geometry, not controller/native GUI validation."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];base='--baseline' in sys.argv
helper=(R/('tests/fixtures/jh/terminal_sweep_before.inc' if base else 'source/terminal_sweep_hr.inc')).read_text()
head=r"""
#include <cmath>
#include <cstdio>
#include <initializer_list>
using i32=int;using u32=unsigned;using u8=unsigned char;
#define H576BP_SURFACE_CAPTURE_M .012f
#define H576BO_FRONT_RELEASE_SKIN_M .024f
struct S26HRTerminalSample{float u,v,p,r;u32 frame,generation;const void*gui;u8 valid;float sweepSide;};
struct H576BOTerminalSurface{float uSpan[3],vSpan[3];};
H576BOTerminalSurface g_h576boTerminalSurface={{.1f,0,0},{0,.1f,0}};
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
int h9_good(float v,float lim){return std::isfinite(v)&&fabsf(v)<lim;}
int checks,failures;
#define C(x) do{checks++;if(!(x)){failures++;printf("FAIL %d %s\n",__LINE__,#x);}}while(0)
"""
body=r"""
int main(){
for(int rate:{60,120})for(float scale:{.75f,1.f,1.25f})for(int side:{-1,1}){
 g_h576boTerminalSurface.uSpan[0]=.1f*scale;g_h576boTerminalSurface.vSpan[1]=.1f*scale;
 S26HRTerminalSample s={};float u=-.05f,v=.5f,p=.06f*side*scale;
 C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale)==0);
 u=.2f;p=-.06f*side*scale;
 C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,scale)==2);C(u>=0&&u<=1);
 // End point outside, but contact happened inside the screen.
 s={};u=.8f;p=.06f*side*scale;s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale);
 u=1.1f;p=-.06f*side*scale;C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,scale)==2);C(u<1);
 // Small real-world motion across a small screen, >35% of its width.
 s={};u=.2f;p=.06f*side*scale;s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale);
 u=.7f;p=-.06f*side*scale;C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,scale)==2);
 // First contact coordinates, not the end of an angled stroke.
 s={};u=.2f;p=.06f*side*scale;s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale);
 u=.5f;p=.01f*side*scale;C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,scale)==2);C(u<.5f);
 s.valid=0;p=-.01f*side;C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,3,1,(void*)1,scale)<0);
 // Continuous trajectories at actual 60/120Hz cadence, each with one press.
 for(float speed:{.5f,1.f,3.f,6.f}){
  S26HRTerminalSample path={};int hits=0;
  for(u32 tick=1;tick<=unsigned(rate);tick++){
   float x=.4f,y=.5f,z=(.06f-speed*(tick-1)/rate)*side*scale;
   if(s26hr_terminal_sample(&path,&x,&y,&z,.008f,tick,1,(void*)1,scale)>0)hits++;
  }C(hits==1);
 }
 // No hit when crossing outside actual GUI bounds.
 s={};u=1.1f;p=.06f*side;s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale);
 u=1.2f;p=-.06f*side;C(!s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,scale));
 for(int fault=0;fault<4;fault++){
  s={};u=.2f;p=.06f*side;s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,scale);
  u=.3f;p=-.06f*side;u32 frame=fault==0?5:2,gen=fault==1?2:1;void*gui=fault==2?(void*)2:(void*)1;
  if(fault==3)p=-1.f*side;
  C(!s26hr_terminal_sample(&s,&u,&v,&p,.008f,frame,gen,gui,scale));
 }
}
printf("%d checks; %d failures\n",checks,failures);return failures?1:0;}
"""
p=R/'build/fast_touch_jh.cpp';p.write_text(head+helper+body)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'audit/jh-fast-touch'/('baseline.json' if base else 'candidate.json')).write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout},indent=2))
print(v.stdout);raise SystemExit(v.returncode)
