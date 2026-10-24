"""Extracted production phone-screen sampling; geometry/state test, not native phone dialogue."""
from pathlib import Path
import re,sys,subprocess,json
R=Path(__file__).resolve().parents[1];s=(R/'source/phone_x.inc').read_text()
def fn(name):
 m=re.search(r'static i32 '+name+r'\([^;{}]*\)\s*\{',s);a=m.start();i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
baseline='--baseline' in sys.argv
head='''#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
using i32=int;using u32=unsigned;
struct S26HRPhoneSample{float p[3];u32 step;i32 valid;};
bool h9_good(float v,float max){return std::isfinite(v)&&fabsf(v)<max;}
int checks=0;
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL %d: %s\\n",__LINE__,#x);exit(1);}}while(0)
'''
sampler='''static i32 s26hr_phone_sample(float x,float y,float z,float radius,i32*armed,S26HRPhoneSample*prev,u32 step){return s26x_phone_hit(x,y,z,radius,armed);}
''' if baseline else fn('s26hr_phone_sample')
body=r'''
int main(){
 for(int action=1;action<=2;action++){
  float u=action==1?.25f:.75f,x=.68f*.1433988f-.07223097f,z=.04055895f-u*.08111791f,r=.009f;
  S26HRPhoneSample p={};int armed=0;
  CHECK(!s26hr_phone_sample(x,.065f,z,r,&armed,&p,1));
  CHECK(s26hr_phone_sample(x,-.01f,z,r,&armed,&p,2)==action);
  CHECK(!s26hr_phone_sample(x,-.01f,z,r,&armed,&p,3));
  CHECK(!s26hr_phone_sample(x,.065f,z,r,&armed,&p,4));
  CHECK(s26hr_phone_sample(x,.02f,z,r,&armed,&p,5)==action);
  CHECK(!s26hr_phone_sample(x,.02f,z,r,&armed,&p,6));
  p={};armed=0;CHECK(!s26hr_phone_sample(x,-.01f,z,r,&armed,&p,1));
  CHECK(!s26hr_phone_sample(x,.02f,z,r,&armed,&p,2));
  // Missing samples cannot bridge a pause, lost tracking or stale pose.
  p={};armed=0;s26hr_phone_sample(x,.065f,z,r,&armed,&p,1);
  CHECK(!s26hr_phone_sample(x,-.01f,z,r,&armed,&p,4));
  // A large jump is not a valid touch; source point on screen is insufficient.
  p={};armed=0;s26hr_phone_sample(x,.4f,z,r,&armed,&p,1);
  CHECK(!s26hr_phone_sample(x,-.01f,z,r,&armed,&p,2));
  // Both endpoints outside the GUI cannot activate a button.
  p={};armed=0;s26hr_phone_sample(-.07f,.065f,z,r,&armed,&p,1);
  CHECK(!s26hr_phone_sample(-.07f,-.01f,z,r,&armed,&p,2));
  for(int hz:{60,120})for(float speed:{.5f,1.f,3.f}){
   p={};armed=0;int hits=0;
   for(u32 step=1;step<=30;step++){
    float y=.065f-speed*(step-1)/hz;
    int hit=s26hr_phone_sample(x,y,z,r,&armed,&p,step);
    if(hit){CHECK(hit==action);hits++;}
   }
   CHECK(hits==1);
  }
  p={};armed=1;
  CHECK(!s26hr_phone_sample(NAN,.02f,z,r,&armed,&p,1)&&!p.valid&&!armed);
  // Different hands have independent sample/rearm histories.
  S26HRPhoneSample other={};int otherArmed=0;
  p={};armed=0;s26hr_phone_sample(x,.065f,z,r,&armed,&p,1);
  CHECK(!s26hr_phone_sample(x,-.01f,z,r,&otherArmed,&other,2));
  CHECK(s26hr_phone_sample(x,-.01f,z,r,&armed,&p,2)==action);
 }
 printf("PASS %d phone sampler checks\n",checks);
}
'''
path=R/'build/phone_tap_hr.cpp';path.write_text(head+fn('s26x_phone_hit')+sampler+body)
subprocess.run([sys.argv[1],'c++','-O2',str(path),'-o',str(path.with_suffix('.exe'))],check=True)
r=subprocess.run([str(path.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence'/('phone_tap_baseline.json' if baseline else 'phone_tap_candidate.json')).write_text(json.dumps({'exit':r.returncode,'output':r.stdout+r.stderr,'scope':__doc__},indent=2))
print(r.stdout+r.stderr);raise SystemExit(r.returncode)
