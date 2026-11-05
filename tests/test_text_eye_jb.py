from pathlib import Path
import subprocess,sys
r=Path.cwd();s=(r/'source/s26n.c').read_text();a=s.index('static void h5753h_quat_to_rot3(');b=s.index('\n}',a)+2
code=r"""
#include <cmath>
#include <cstring>
#include <cassert>
#include <cstdio>
using i32=int;
struct Q{float x,y,z,w;};struct V{float x,y,z;};struct XrPosef{Q orientation;V position;};
bool h9_good(float x,float l){return std::isfinite(x)&&fabsf(x)<l;}
float ext_Sqrtf(float x){return sqrtf(x);}void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
"""+s[a:b]+(r/'source/text_eye_jb.inc').read_text()+r"""
int main(){int checks=0;
for(float scale: {0.5f,1.f,1.5f})for(int yaw=-150;yaw<=150;yaw+=15)for(int roll=-45;roll<=45;roll+=15){
 float y=yaw*.00872664626f,z=roll*.00872664626f;
 Q q={sinf(y)*sinf(z),sinf(y)*cosf(z),cosf(y)*sinf(z),cosf(y)*cosf(z)};
 float qq[4]={q.x,q.y,q.z,q.w},R[9];h5753h_quat_to_rot3(qq,R);
 V axis={R[0]*.032f,R[3]*.032f,R[6]*.032f};
 XrPosef l={q,{-axis.x,-axis.y,-axis.z}},r={q,axis};
 float m[16]={1,0,0,-.9f,0,1,0,.75f,0,0,1,-1.65f,0,0,0,1},L[16],T[16];
 assert(s26jb_text_eye_model(m,&l,&r,0,scale,L));assert(s26jb_text_eye_model(m,&l,&r,1,scale,T));
 assert(fabsf(L[3]-m[3]-.032f*scale)<1e-6f);assert(fabsf(T[3]-m[3]+.032f*scale)<1e-6f);
 for(int i=0;i<16;i++)if(i!=3)assert(fabsf(L[i]-m[i])<1e-6f&&fabsf(T[i]-m[i])<1e-6f);
 // Eye-to-world reconstruction must return the original common plane.
 assert(fabsf(L[3]-.032f*scale-m[3])<1e-6f&&fabsf(T[3]+.032f*scale-m[3])<1e-6f);checks++;
}
float m[16]={},o[16];XrPosef l={{0,0,0,1},{-.032f,0,0}},r={{0,0,0,1},{.032f,0,0}};
assert(!s26jb_text_eye_model(m,&l,&r,2,1,o));assert(!s26jb_text_eye_model(m,&l,&r,0,0,o));r.position.x=1;assert(!s26jb_text_eye_model(m,&l,&r,0,1,o));
printf("common-plane reconstruction passed %d rotated/scaled eye pairs; invalid inputs rejected\n",checks);}
"""
code=code.replace('#include <cstdio>','#include <cstdio>\n#include <initializer_list>')
p=r/'build/jb_text_eye.cpp';p.write_text(code);subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True);subprocess.run([str(p.with_suffix('.exe'))],check=True)
