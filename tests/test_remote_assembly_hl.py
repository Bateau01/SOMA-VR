"""Production graph proof with explicit Newton/owner boundary doubles."""
from pathlib import Path
import re,subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/accessibility_hd.inc').read_text()
def fn(n):
 a=re.search(r'static [^\n{};]+\b'+n+r'\([^;{}]*\)\s*\{',s).start();i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
code=r'''
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
using i32=int;using u32=unsigned;
int checks;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
struct B;struct J{B*a,*b;const char*type;};struct B{float mass=1;void*owner=(void*)1;std::vector<J*>j;};
const void*g_h14GripBody[2];
void zero_bytes(void*p,size_t n){memset(p,0,n);}
void* h482_body_owner(const void*b,void*){return ((B*)b)->owner;}
void mass(const void*b,float*m,float*,float*,float*){*m=((B*)b)->mass;}auto p_h14GetMass=mass;
const void* first(const void*b){auto&v=((B*)b)->j;return v.empty()?nullptr:v[0];}auto p_h14GetFirstJoint=first;
const void* next(const void*b,const void*j){auto&v=((B*)b)->j;for(size_t i=0;i<v.size();i++)if(v[i]==j)return i+1<v.size()?v[i+1]:nullptr;return nullptr;}auto p_h14GetNextJoint=next;
const void* b0(const void*j){return ((J*)j)->a;}auto p_h15JointGetBody0=b0;
const void* b1(const void*j){return ((J*)j)->b;}auto p_h15JointGetBody1=b1;
void* ud(const void*j){return (void*)((J*)j)->type;}auto p_h21JointGetUserData=ud;
int h22_rtti_name(void*p,char*o,u32){if(!p)return 0;strcpy(o,(const char*)p);return 1;}
bool h25_str_contains(const char*a,const char*b){return strstr(a,b);}
struct S26HLAssembly{const void*body[32];u32 count;float mass;};
'''+fn('s26hl_assembly')+fn('s26hl_same_free_prop')+r'''
int main(){
 for(int count=1;count<=34;count++)for(int failure=0;failure<8;failure++){
  B b[35];J j[35];for(int i=0;i<count-1;i++){j[i]={&b[i],&b[i+1],i%2?"JointHinge":"JointBall"};b[i].j.push_back(&j[i]);b[i+1].j.push_back(&j[i]);}
  for(int i=0;i<count;i++)b[i].mass=.5f;
  g_h14GripBody[0]=g_h14GripBody[1]=nullptr;
  if(failure==1)b[count-1].mass=0;
  if(failure==2)b[count-1].owner=(void*)2;
  if(failure==3)g_h14GripBody[0]=&b[count-1];
  if(failure==4)g_h14GripBody[1]=&b[count-1];
  if(failure==5)b[count-1].mass=26;
  if(failure==6&&count>1)j[0].type="JointSlider";
  if(failure==7&&count>1)j[0].b=nullptr;
  S26HLAssembly a;bool expected=count<=32&&(failure==0||(count==1&&failure>=6));
  CHECK(bool(s26hl_assembly(&b[0],(void*)1,&a))==expected);
  if(expected){CHECK(a.count==count);CHECK(s26hl_same_free_prop(&b[0],&b[count-1],(void*)1));B other;CHECK(!s26hl_same_free_prop(&b[0],&other,(void*)1));}
 }
 // Cycles are bounded and visited once; malformed ownerless/world joints fail.
 B b[3];J j[3];for(int i=0;i<3;i++){j[i]={&b[i],&b[(i+1)%3],"JointBall"};b[i].j.push_back(&j[i]);b[(i+1)%3].j.push_back(&j[i]);}
 g_h14GripBody[0]=g_h14GripBody[1]=nullptr;S26HLAssembly a;CHECK(s26hl_assembly(b,(void*)1,&a));CHECK(a.count==3&&a.mass==3);
 printf("PASS %d production assembly guards\n",checks);
}
'''
p=R/'build/remote_assembly_hl.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
