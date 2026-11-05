"""Private acquisition-window policy; no native gameplay or collision proof."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
code=(r/'tests/jb_closure_policy.inc').read_text()+r'''
#include <cstdio>
#include <cmath>
int checks;
#define C(x) do{++checks;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
int main(){
 for(int hz: {60,120}) {
  float dt=1.f/hz;JBClosureWindow w={};unsigned s=1;
  C(!jb_closure_step(&w,s,dt,1,1,1,0,1,0));
  C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,0));
  C(jb_closure_step(&w,++s,dt,0,1,1,0,1,1));
  for(int i=0;i<hz;++i)C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,1));
  C(!jb_closure_step(&w,++s,dt,1,1,1,0,1,0));
  for(int i=0;i<hz/4;++i)C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,0));
  C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,1));
  // Native rejection consumes the window; another body cannot steal the squeeze.
  C(!jb_closure_step(&w,++s,dt,1,1,1,0,1,0));
  C(!jb_closure_step(&w,++s,dt,0,1,1,1,1,1));
  C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,1));
  for(int kind=0;kind<6;++kind){
   C(!jb_closure_step(&w,++s,dt,1,1,1,0,1,0));
   if(kind==0)C(!jb_closure_step(&w,++s,dt,0,0,1,0,1,1));
   if(kind==1)C(!jb_closure_step(&w,++s,dt,0,1,0,0,1,1));
   if(kind==2)C(!jb_closure_step(&w,++s,dt,0,1,1,0,0,1));
   if(kind==3){s+=2;C(!jb_closure_step(&w,s,dt,0,1,1,0,1,1));}
   if(kind==4)C(!jb_closure_step(&w,++s,.1f,0,1,1,0,1,1));
   if(kind==5)C(!jb_closure_step(&w,++s,NAN,0,1,1,0,1,1));
   C(!jb_closure_step(&w,++s,dt,0,1,1,0,1,1));
  }
 }
 JBClosureWindow a={},b={};
 jb_closure_step(&a,1,.01f,1,1,1,0,1,0);
 jb_closure_step(&b,1,.01f,1,1,1,0,1,0);
 C(jb_closure_step(&a,2,.01f,0,1,1,0,1,1));
 C(b.armed);C(jb_closure_step(&b,2,.01f,0,1,1,0,1,1));
 printf("PASS %d assertions (private policy only)\n",checks);
}
'''
code='#include <initializer_list>\n'+code
p=r/'build/jb_closure_policy.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-closure-policy.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
