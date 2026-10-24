"""Extracted direct-terminal contact sampler; not actual GUI click validation."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];baseline='--baseline' in sys.argv
helper=(R/'source/terminal_sweep_hr.inc').read_text()
if baseline:helper='''static i32 s26hr_terminal_sample(S26HRTerminalSample*,float*u,float*v,float*p,float r,u32,u32,const void*,float){return *u>=0&&*u<=1&&*v>=0&&*v<=1&&fabsf(*p)<=r+H576BP_SURFACE_CAPTURE_M;}'''
code=r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
using i32=int;using u32=unsigned;using u8=unsigned char;
#define H576BP_SURFACE_CAPTURE_M .012f
#define H576BO_FRONT_RELEASE_SKIN_M .024f
struct S26HRTerminalSample{float u,v,p,r;u32 frame,generation;const void*gui;u8 valid;float sweepSide;};
int h9_good(float v,float lim){return std::isfinite(v)&&fabsf(v)<lim;}
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
'''+helper+r'''
int main(){
 for(int h=0;h<2;h++)for(int side=-1;side<=1;side+=2)for(int rate=60;rate<=120;rate+=60){
  S26HRTerminalSample samples[2]={};float u=.4f,v=.6f,p=.021f*side;
  C(!s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,10,1,(void*)1,1));
  p=(.021f-(rate==60?3.f:6.f)/rate)*side;
  C(s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,11,1,(void*)1,1));
  C(fabsf(p)<=.020f);C(u==.4f&&v==.6f);C(!samples[1-h].valid);
  samples[h].valid=0; // Production keep-surface release preserves swept rearm.
  p=-.01f*side;C(s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,12,1,(void*)1,1)<0);
  p=.01f*side;C(s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,13,1,(void*)1,1)<0);
  p=.06f*side;C(s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,14,1,(void*)1,1)==0);
  p=.015f*side;C(s26hr_terminal_sample(&samples[h],&u,&v,&p,.008f,15,1,(void*)1,1)>0);
 }
 for(int fault=0;fault<9;fault++){
  S26HRTerminalSample sample={};float u=.4f,v=.6f,p=.05f;
  C(!s26hr_terminal_sample(&sample,&u,&v,&p,.008f,10,1,(void*)1,1));
  p=-.05f;unsigned frame=11,gen=1;const void*gui=(void*)1;
  if(fault==0)frame=14;if(fault==1)gen=2;if(fault==2)gui=(void*)2;
  if(fault==3)p=-.2f;if(fault==4)u=1.01f;if(fault==5)v=-.01f;
  if(fault==6)u=.99f;if(fault==7)gui=nullptr;if(fault==8)p=NAN;
  C(s26hr_terminal_sample(&sample,&u,&v,&p,.008f,frame,gen,gui,1)<=0);
 }
 S26HRTerminalSample s={};float u=.2f,v=.3f,p=.015f;
 C(s26hr_terminal_sample(&s,&u,&v,&p,.008f,1,1,(void*)1,1));C(p==.015f);
 p=.06f;C(!s26hr_terminal_sample(&s,&u,&v,&p,.008f,2,1,(void*)1,1));
 printf("PASS %d terminal sample assertions\n",checks);
}
'''
p=R/'build/terminal_sweep_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence'/('terminal_sweep_baseline.json' if baseline else 'terminal_sweep_candidate.json')).write_text(json.dumps({'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
