"""Production point-query contracts against the shipped Newton DLL.

No live game: isolated convex bodies, real Newton point queries. This does not
prove a reported control or remote-readable failure in its gameplay sequence.
"""
from pathlib import Path
import subprocess, sys, json, re
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text()
def fn(name):
    m=re.search(r'static i32 '+name+r'\([^;{}]*\)\s*\{',s)
    start=m.start();i=s.index('{',start)+1;depth=1
    while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
    return s[start:i]
code=r'''
#include <windows.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
using i32=int;
void* g_h14NewtonWorld;
const void*(*p_h14GetCollision)(const void*);
void(*p_h14GetMatrix)(const void*,float*);
int(*p_h14PointDistance)(void*,const float*,const void*,const float*,float*,float*,int);
float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
int h9_good(float v,float lim){return std::isfinite(v)&&fabsf(v)<lim;}
#define CHECK(x) do{if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);exit(1);}++checks;}while(0)
int checks;
template<class T>T api(HMODULE n,const char*name){auto p=GetProcAddress(n,name);CHECK(p);return (T)p;}
'''+fn('h14_point_to_body')+fn('s26eq_return_point')+r'''
int main(){
 auto n=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll");CHECK(n);
 auto create=api<void*(*)()>(n,"NewtonCreate");auto destroy=api<void(*)(void*)>(n,"NewtonDestroy");
 auto box=api<void*(*)(void*,float,float,float,int,const float*)>(n,"NewtonCreateBox");
 auto body=api<void*(*)(void*,void*,const float*)>(n,"NewtonCreateBody");
 p_h14GetCollision=api<decltype(p_h14GetCollision)>(n,"NewtonBodyGetCollision");
 p_h14GetMatrix=api<decltype(p_h14GetMatrix)>(n,"NewtonBodyGetMatrix");
 p_h14PointDistance=api<decltype(p_h14PointDistance)>(n,"NewtonCollisionPointDistance");
 g_h14NewtonWorld=create();CHECK(g_h14NewtonWorld);
 for(float scale:{.7f,1.f,1.25f}){
  float m[16]={0,0,-1,0,0,1,0,0,1,0,0,0,2,3,4,1};
  auto b=body(g_h14NewtonWorld,box(g_h14NewtonWorld,.2f*scale,.2f*scale,.2f*scale,0,nullptr),m);
  float inside[3]={2,3,4},outside[3]={2+.15f*scale,3,4},cp[3],gap;
  CHECK(!h14_point_to_body(b,inside,&gap,cp));
  CHECK(s26eq_return_point(b,inside,&gap,cp)&&gap==0);
  CHECK(cp[0]==inside[0]&&cp[1]==inside[1]&&cp[2]==inside[2]);
  CHECK(h14_point_to_body(b,outside,&gap,cp)&&fabsf(gap-.05f*scale)<.0001f);
  CHECK(s26eq_return_point(b,outside,&gap,cp)&&fabsf(gap-.05f*scale)<.0001f);
 }
 CHECK(!s26eq_return_point(nullptr,nullptr,nullptr,nullptr));
 destroy(g_h14NewtonWorld);printf("PASS %d checks: legacy helper rejects interior; validated return helper accepts interior\n",checks);
}
'''
code=code.replace('#include <cstdlib>','#include <cstdlib>\n#include <initializer_list>')
p=R/'build/point_query_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
out={'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__}
(R/'docs/v109-evidence/point_query_hr.json').write_text(json.dumps(out,indent=2))
print(out['output']);raise SystemExit(v.returncode)
