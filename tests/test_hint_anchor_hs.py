"""Extracted production hint anchor: mathematical regression, not headset evidence."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
code=r'''
#include <cmath>
#include <cstring>
#include <cstdio>
#include <cstdlib>
using i32=int;using u32=unsigned;
bool h9_good(float x,float lim){return std::isfinite(x)&&fabsf(x)<lim;}
float h9_abs(float x){return fabsf(x);}float ext_Sqrtf(float x){return sqrtf(x);}
auto p_h5755blAtan2f=atan2f;int h5755bl_resolve_atan2f(){return 1;}
void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
float h5755eb_wrap_pi(float x){while(x>3.14159265f)x-=6.2831853f;while(x< -3.14159265f)x+=6.2831853f;return x;}
'''+(r/'source/hint_anchor_hs.inc').read_text()+r'''
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
void view(float yaw,float pitch,float x,float*v){
 float c=cosf(yaw),s=sinf(yaw),cp=cosf(pitch),sp=sinf(pitch);
 float a[16]={c,0,-s,-c*x,s*sp,cp,c*sp,-s*sp*x,s*cp,-sp,c*cp,-s*cp*x,0,0,0,1};memcpy(v,a,64);
}
int main(){
 S26HSHintAnchor a={};float v[16],o[16],first[16];
 view(0,0,0,v);C(s26hs_hint_view(&a,v,first,1,1));
 view(.3f,.1f,2,v);C(s26hs_hint_view(&a,v,o,2,1));
 C(o[0]==first[0]&&o[8]==first[8]);C(fabsf(o[3]+2)<.00001f); // rotation held, position current
 view(.6f,.1f,2,v);C(s26hs_hint_view(&a,v,o,3,1));C(o[8]==v[8]);
 view(.65f,.5f,2,v);C(s26hs_hint_view(&a,v,o,4,1));C(o[9]==v[9]&&o[0]==v[0]);
 view(2.9f,0,0,v);C(s26hs_hint_view(&a,v,o,5,2));
 view(-3.13f,0,0,v);C(s26hs_hint_view(&a,v,o,6,2));C(o[0]==a.rotation[0]&&fabsf(a.yaw+2.9f)<.0001f); // wrap does not spuriously snap
 C(s26hs_hint_view(&a,v,o,12,2));C(o[0]==v[0]); // newly visible hint recentres
 v[0]=NAN;C(!s26hs_hint_view(&a,v,o,13,2));
 printf("PASS %d hint-anchor assertions\n",checks);
}
'''
p=r/'build/hint_anchor_hs.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'docs/v109-evidence/hint_anchor_hs.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2));print(v.stdout+v.stderr);raise SystemExit(v.returncode)
