"""Production hint transform and native GUI setters; no rendered/headset claim."""
from pathlib import Path
import re,sys,subprocess,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
a=s.index('static i32 s26hr_hint_matrix(');i=s.index('{',a)+1;d=1
while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
code=r"""
#include <windows.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
using i32=int;
bool h9_good(float v,float limit){return std::isfinite(v)&&fabsf(v)<limit;}
void h10_identity(float*m){for(int i=0;i<16;i++)m[i]=(i%5==0)?1:0;}
int checks;
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
"""+s[a:i]+r"""
int main(int argc,char**argv){
 CHECK(argc==2);auto module=(unsigned char*)LoadLibraryExA(argv[1],0,DONT_RESOLVE_DLL_REFERENCES);CHECK(module);
 using SetVirtual=void(*)(void*,const float*,float,float,const float*);
 using SetSize=void(*)(void*,const float*);using SetMatrix=void(*)(void*,const float*);
 auto vset=(SetVirtual)(module+0x213400);auto size=(SetSize)(module+0x213440);
 for(float scale:{.7f,1.f,1.25f})for(float yaw:{-3.f,-1.f,0.f,1.f,3.f})for(float pitch:{-1.2f,-.4f,0.f,.4f,1.2f}){
  float c=cosf(yaw),sn=sinf(yaw),cp=cosf(pitch),sp=sinf(pitch);
  // Orthogonal view basis with nonzero translation; independent assertion
  // multiplies native V*M and checks a fixed camera-space panel origin.
  float V[16]={c,0,-sn,2, sn*sp,cp,c*sp,-4, sn*cp,-sp,c*cp,8, 0,0,0,1},M[16];
  CHECK(s26hr_hint_matrix(V,scale,M));
  float expected[3]={-.9f*scale,.75f*scale,-1.65f*scale};
  for(int row=0;row<3;row++)for(int col=0;col<4;col++){
   float actual=0;for(int k=0;k<4;k++)actual+=V[row*4+k]*M[k*4+col];
   CHECK(fabsf(actual-(col==3?expected[row]:(row==col?1.f:0.f)))<.00001f);
  }
  unsigned char set[0x200]={};float v[2]={1024,768},off[2]={0,0},phys[3]={1.8f*scale,1.35f*scale,scale};
  vset(set,v,-1000,1000,off);size(set,phys);
  CHECK(*(float*)(set+0x100)==1024&&*(float*)(set+0x104)==768);
  CHECK(*(float*)(set+0x108)==0&&*(float*)(set+0x10c)==0);
  CHECK(*(float*)(set+0x110)==-1000&&*(float*)(set+0x114)==1000);
  CHECK(*(float*)(set+0x13c)==phys[0]&&*(float*)(set+0x140)==phys[1]);
  // Header center uses x=512,y=61.44; native scale flips GUI Y.
  CHECK(fabsf(expected[0]+512*phys[0]/1024)<.00001f);
  CHECK(expected[1]-61.44f*phys[1]/768>0);
 }
 float V[16],M[16];h10_identity(V);
 CHECK(!s26hr_hint_matrix(V,0,M));CHECK(!s26hr_hint_matrix(nullptr,1,M));
 V[7]=NAN;CHECK(!s26hr_hint_matrix(V,1,M));
 printf("PASS %d checks: head-relative hint placement and actual native virtual-size/3D-size setters\n",checks);
}
"""
p=R/'build/hint_matrix_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe')),sys.argv[2]],capture_output=True,text=True)
(R/'docs/v109-evidence/hint_matrix_hr.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
