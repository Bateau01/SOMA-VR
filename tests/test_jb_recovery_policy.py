"""Extracted detector only: no collision clearance or automatic recovery proof."""
from pathlib import Path
import json,subprocess,sys
r=Path(__file__).resolve().parents[1]
code='#include <cstdio>\n#include <cmath>\n#include <initializer_list>\n'+(r/'tests/jb_recovery_policy.inc').read_text()+r'''
int checks;
#define C(x) do{++checks;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
int main(){
 for(int hz:{60,120})for(int held:{0,1}){
  JBRecoveryWatch w={};int requests=0;float dt=1.f/hz;
  for(unsigned s=1;s<=unsigned(hz*2);++s){int q=jb_recovery_observe(&w,s,dt,1,.4f,0,.1f*dt,held);if(q){C(q==(held?2:1));++requests;C(s>=unsigned(.8f*hz));}}
  C(requests==1);
  for(int scenario=0;scenario<7;++scenario){
   w={};
   for(unsigned s=1;s<=unsigned(hz*3);++s){
    int eligible=scenario!=0;float lag=scenario==1?.1f:.4f,root=scenario==2?.01f:0,effort=scenario==3?0:.1f*dt;
    unsigned step=scenario==4?s*2:s;if(scenario==5)lag=NAN;if(scenario==6)root=NAN;
    C(!jb_recovery_observe(&w,step,dt,eligible,lag,root,effort,held));
   }
  }
  w={};for(unsigned s=1;s< unsigned(hz/2);++s)jb_recovery_observe(&w,s,dt,1,.4f,0,.1f*dt,held);
  jb_recovery_reset(&w);C(!w.valid&&w.stalled==0&&w.effort==0);
 }
 printf("PASS %d stalled-root policy assertions\n",checks);
}
'''
p=r/'build/jb_recovery_policy.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-recovery-policy.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
