"""Compiled production contact policy; native widget acceptance is tested separately."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
code='#include <cstdio>\n#include <cstdlib>\n#include <cmath>\nusing i32=int;\n'+(r/'source/terminal_touch_hs.inc').read_text()+r'''
#define C(x) do{if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
int main(){
 for(int hz: {60,120}){
  S26HSTouch s={};float dt=1.0f/hz;
  C(s26hs_touch_edge(&s,1,1,dt)); // first edge unchanged
  s26hs_touch_consumed(&s,0);
  C(s26hs_touch_edge(&s,3,1,dt)); // settling from blank space
  s26hs_touch_consumed(&s,1);
  for(int i=0;i<100;i++)C(!s26hs_touch_edge(&s,3,1,dt)); // no repeat / neighboring button
  C(s26hs_touch_edge(&s,1,1,dt));C(!s26hs_touch_edge(&s,2,1,dt));C(!s26hs_touch_edge(&s,3,1,dt));
  C(s26hs_touch_edge(&s,1,0,dt));C(!s26hs_touch_edge(&s,3,0,dt)); // laser unchanged
  C(s26hs_touch_edge(&s,1,1,dt));for(int i=0;i<hz;i++)s26hs_touch_edge(&s,3,1,dt);C(s.remaining==0);
  C(s26hs_touch_edge(&s,1,1,dt));C(!s26hs_touch_edge(&s,3,1,NAN));
  C(s26hs_touch_edge(&s,1,1,dt));C(!s26hs_touch_edge(&s,0,1,dt));C(s.remaining==0);
 }
 puts("PASS: first contact, blank settling, consumed widget/custom handler, release, laser, timeout, invalid time, cancellation at 60/120Hz");
}
'''
code=code.replace('#include <cstdio>','#include <cstdio>\n#include <initializer_list>')
p=r/'build/terminal_touch_hs.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'docs/v109-evidence/terminal_touch_hs.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
