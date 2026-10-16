from pathlib import Path
import subprocess,sys,json,re
R=Path(__file__).resolve().parents[1];s=(R/'source/accessibility_hd.inc').read_text()
def fn(name):
 a=re.search(r'static [^\n{};]+\b'+name+r'\([^;{}]*\)\s*\{',s).start();b=s.index('{',a);i=b+1;depth=1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
code=r'''
#include <windows.h>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <initializer_list>
using u32=unsigned;using i32=int;using u8=unsigned char;
int checks;#define_unused
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);exit(1);}}while(0)
void zero_bytes(void*p,size_t n){memset(p,0,n);}void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*4);}
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
struct S26HDHit{const void* body;float t;};struct S26HDPull{const void*body;void*wrapper,*owner;float last[3],age;};
struct S26HGQuery{const void*body[8];float score[8],a[3],d[3],range,metric;u32 count;};
S26HDPull g_s26hgFocus[2];float g_s26hgScanAge[2];const void*g_h34HandNewton[2],*g_h14GripBody[2];void*g_h14NewtonWorld;
void(*p_h14GetMass)(const void*,float*,float*,float*,float*);void*(*p_h14GetFirstJoint)(const void*);void(*p_h14GetMatrix)(const void*,float*);
void*(*getCol)(const void*);int(*pointDist)(void*,const float*,const void*,const float*,float*,float*,int);
void(*p_h14WorldAABB)(const void*,const float*,const float*,void(*)(const void*,void*),void*);
void(*castRay)(const void*,const float*,const float*,float(*)(const void*,const float*,int,void*,float),void*,void*);
void(*setForce)(const void*,const float*);
void gravity(const void*b,float,int){float m,x,y,z;p_h14GetMass(b,&m,&x,&y,&z);float f[4]={0,-9.81f*m,0,0};setForce(b,f);}
void(*setVelocity)(const void*,const float*);void(*getVelocity)(const void*,float*);
int h14_point_to_body(const void*b,const float*p,float*gap,float*cp){float m[16],n[4],c[4];p_h14GetMatrix(b,m);if(!pointDist(g_h14NewtonWorld,p,getCol(b),m,c,n,0)){memcpy(cp,p,12);*gap=0;return 1;}memcpy(cp,c,12);*gap=h10_len3(p[0]-c[0],p[1]-c[1],p[2]-c[2]);return 1;}
const void* forbidden;int looseCalls,rayCalls;
int s26hd_loose(const void*b,void**w,void**o,float*mass){looseCalls++;if(!b||b==forbidden||b==g_h14GripBody[0]||b==g_h14GripBody[1])return 0;float x,y,z;p_h14GetMass(b,mass,&x,&y,&z);*w=*o=(void*)b;return *mass>.001f&&*mass<=25&&!p_h14GetFirstJoint(b);}
int s26hd_live(S26HDPull*p,float){return p->body!=forbidden;}
'''.replace('#define_unused','')+fn('s26hd_ray_hit')+r'''
S26HDHit s26hd_ray(const float*a,const float*b){S26HDHit h={nullptr,1};rayCalls++;castRay(g_h14NewtonWorld,a,b,s26hd_ray_hit,&h,nullptr);return h;}
'''+'int s26hl_same_free_prop(const void* b,const void* hit,void*){return !hit||b==hit;}\n'+''.join(fn(n) for n in ['s26hg_candidate','s26hg_visible','s26hg_select','s26hg_pull_velocity'])+r'''
template<class T>T api(HMODULE n,const char*s){auto p=GetProcAddress(n,s);CHECK(p);return(T)p;}
int main(){auto n=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll");CHECK(n);
#define API(v,name) v=api<decltype(v)>(n,name)
 API(p_h14GetMass,"NewtonBodyGetMassMatrix");API(p_h14GetMatrix,"NewtonBodyGetMatrix");API(p_h14GetFirstJoint,"NewtonBodyGetFirstJoint");API(getCol,"NewtonBodyGetCollision");API(pointDist,"NewtonCollisionPointDistance");API(p_h14WorldAABB,"NewtonWorldForEachBodyInAABBDo");API(castRay,"NewtonWorldRayCast");API(setVelocity,"NewtonBodySetVelocity");API(getVelocity,"NewtonBodyGetVelocity");
 API(setForce,"NewtonBodySetForce");auto forceCB=api<void(*)(const void*,void(*)(const void*,float,int))>(n,"NewtonBodySetForceAndTorqueCallback");
 auto create=api<void*(*)()>(n,"NewtonCreate");auto destroy=api<void(*)(void*)>(n,"NewtonDestroy");auto box=api<void*(*)(void*,float,float,float,int,const float*)>(n,"NewtonCreateBox");auto make=api<void*(*)(void*,void*,const float*)>(n,"NewtonCreateBody");auto mass=api<void(*)(const void*,float,float,float,float)>(n,"NewtonBodySetMassMatrix");auto erase=api<void(*)(void*,void*)>(n,"NewtonDestroyBody");auto update=api<void(*)(void*,float)>(n,"NewtonUpdate");auto wake=api<void(*)(const void*,int)>(n,"NewtonBodySetFreezeState");
 auto add=[&](float x,float y,float z,float size,float kg){float m[16]={1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1};auto col=box(g_h14NewtonWorld,size,size,size,0,nullptr);auto b=make(g_h14NewtonWorld,col,m);if(kg)mass(b,kg,.02f,.02f,.02f);return b;};
 g_h14NewtonWorld=create();float a[3]={0},d[3]={1,0,0},p[3];void*w,*o;
 auto pick=[&](){return s26hg_select(0,a,d,2,1,1.f/60,p,&w,&o);};
 auto clear=[&](){memset(g_s26hgFocus,0,sizeof g_s26hgFocus);memset(g_s26hgScanAge,0,sizeof g_s26hgScanAge);};
 auto target=add(1.5f,.13f,0,.06f,1);CHECK(!s26hd_ray(a,(float[3]){2,0,0}).body);CHECK(pick()==target);
 // A small aim perturbation keeps the target and does not repeat the broad scan.
 int calls=looseCalls;d[1]=-.01f;d[0]=sqrtf(1-d[1]*d[1]);CHECK(pick()==target);CHECK(looseCalls-calls==1);
 auto wall=add(.75f,0,0,.5f,0);CHECK(!pick());erase(g_h14NewtonWorld,wall);clear();CHECK(pick()==target);
 forbidden=target;CHECK(!pick());forbidden=nullptr;clear();CHECK(pick()==target);
 // A deliberate turn drops retention immediately.
 d[0]=0;d[1]=1;CHECK(!pick());d[0]=1;d[1]=0;clear();CHECK(pick()==target);
 // Exact aim beats an off-axis candidate on a new selection.
 auto exact=add(1,0,0,.08f,1);clear();CHECK(pick()==exact);g_h14GripBody[1]=exact;clear();CHECK(pick()==target);g_h14GripBody[1]=nullptr;erase(g_h14NewtonWorld,exact);
 erase(g_h14NewtonWorld,target);clear();target=add(2.5f,0,0,.1f,1);CHECK(!pick());erase(g_h14NewtonWorld,target);
 // Relaxed remote cone accepts natural pointing offsets, not side/back targets.
 for(float offset:{.20f,.35f,.42f}){clear();target=add(1.5f,offset,0,.06f,1);CHECK(pick()==target);erase(g_h14NewtonWorld,target);}
 clear();target=add(1.5f,.8f,0,.06f,1);CHECK(!pick());erase(g_h14NewtonWorld,target);
 // Dense candidate list remains bounded, irrespective of enumeration order.
 for(int i=0;i<40;i++)add(1.2f+(i%5)*.08f,.04f+(i/5)*.02f,.03f,.015f,1);
 S26HGQuery q={};q.range=2;q.metric=1;q.d[0]=1;float lo[3]={0,-1,-1},hi[3]={2,1,1};p_h14WorldAABB(g_h14NewtonWorld,lo,hi,s26hg_candidate,&q);CHECK(q.count==8);for(int i=1;i<8;i++)CHECK(q.score[i]>=q.score[i-1]);clear();calls=looseCalls;pick();CHECK(looseCalls-calls<=9);
 destroy(g_h14NewtonWorld);
 // Real Newton flight comparison. Same geometry/velocity model at both rates;
 // no SetMatrix, collision override, or gravity disabling in the pull path.
 for(int hz:{60,120})for(float start:{.5f,1.f,2.f,3.f})for(float kg:{.1f,1.f,6.f,10.1f,20.f,25.f}){
  float arrivals[2]={};
  for(int mode=0;mode<2;mode++){
   g_h14NewtonWorld=create();auto b=add(start,0,0,.1f,kg);wake(b,0);float gc[3]={},cp[3],gap,v[4]={};
   for(int frame=0;frame<hz*4;frame++){
    h14_point_to_body(b,gc,&gap,cp);if(gap<.08f){arrivals[mode]=(float)frame/hz;break;}
    getVelocity(b,v);
    if(mode)s26hg_pull_velocity(v,gc,cp,1,1.f/hz);
    else{float speed=fminf(gap*8,1.5f),want=-speed,dv=want-v[0],cap=12.f/hz;v[0]+=fmaxf(-cap,fminf(cap,dv));}
    setVelocity(b,v);update(g_h14NewtonWorld,1.f/hz);
   }
   CHECK(arrivals[mode]>0);destroy(g_h14NewtonWorld);
  }
  CHECK(arrivals[1]<arrivals[0]);CHECK(arrivals[1]<1.05f);
  if(kg==1)printf("flight %dHz %.1fm old %.3fs new %.3fs\n",hz,start,arrivals[0],arrivals[1]);
 }

 // Moving catch point, gravity, changed world scale and force remain live.
 for(int hz:{60,120})for(float metric:{.7f,1.f,1.3f}){
  g_h14NewtonWorld=create();auto b=add(2*metric,0,0,.1f*metric,1);wake(b,0);forceCB(b,gravity);
  float gc[3]={},cp[3],gap,v[4]={};bool caught=false;
  for(int frame=0;frame<hz*2;frame++){
   gc[2]=.5f*metric*(float)frame/hz;h14_point_to_body(b,gc,&gap,cp);
   if(gap<.08f*metric){caught=true;break;}
   getVelocity(b,v);s26hg_pull_velocity(v,gc,cp,metric,1.f/hz);CHECK(std::isfinite(v[0])&&std::isfinite(v[1])&&std::isfinite(v[2]));
   CHECK(h10_len3(v[0],v[1],v[2])<=4.501f*metric);setVelocity(b,v);update(g_h14NewtonWorld,1.f/hz);
  }
  CHECK(caught);destroy(g_h14NewtonWorld);
 }

 // Actual connected Newton bodies: preserve their internal ball joint while
 // applying the same velocity change to the assembly at 60 and 120 Hz.
 auto userJoint=api<void*(*)(void*,int,void(*)(const void*,float,int),void*,const void*,const void*)>(n,"NewtonConstraintCreateUserJoint");
 static const void* jointBodies[2];
 static auto row=api<void(*)(const void*,const float*,const float*,const float*)>(n,"NewtonUserJointAddLinearRow");
 auto submit=+[](const void*j,float,int){
  float a[16],b[16];p_h14GetMatrix(jointBodies[0],a);p_h14GetMatrix(jointBodies[1],b);
  float p0[4]={a[12]+a[0]*.15f,a[13]+a[1]*.15f,a[14]+a[2]*.15f,0};
  float p1[4]={b[12]-b[0]*.15f,b[13]-b[1]*.15f,b[14]-b[2]*.15f,0};
  for(int i=0;i<3;i++){float axis[4]={};axis[i]=1;row(j,p0,p1,axis);}
 };
 for(int hz:{60,120}){
  g_h14NewtonWorld=create();auto b0=add(1.5f,0,0,.1f,1),b1=add(1.8f,0,0,.1f,1);
  jointBodies[0]=b0;jointBodies[1]=b1;CHECK(userJoint(g_h14NewtonWorld,3,submit,nullptr,b0,b1));wake(b0,0);wake(b1,0);
  bool caught=false;
  for(int frame=0;frame<hz*2;frame++){
   float gc[3]={},cp[3],gap,v[4]={},before[4]={},other[4]={};h14_point_to_body(b0,gc,&gap,cp);
   if(gap<.08f){caught=true;break;}
   getVelocity(b0,before);memcpy(v,before,sizeof v);s26hg_pull_velocity(v,gc,cp,1,1.f/hz);getVelocity(b1,other);
   for(int k=0;k<3;k++)other[k]+=v[k]-before[k];setVelocity(b0,v);setVelocity(b1,other);update(g_h14NewtonWorld,1.f/hz);
   float m0[16],m1[16];p_h14GetMatrix(b0,m0);p_h14GetMatrix(b1,m1);
   CHECK(fabsf(h10_len3(m0[12]-m1[12],m0[13]-m1[13],m0[14]-m1[14])-.3f)<.01f);
   CHECK(p_h14GetFirstJoint(b0)&&p_h14GetFirstJoint(b1));
  }
  CHECK(caught);destroy(g_h14NewtonWorld);
 }
 printf("PASS %d production selector/servo + real Newton checks\n",checks);
}
'''
p=R/'build/remote_hg.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/remote_hg.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production selector and velocity servo in actual Newton.dll isolated world; engine eligibility/lifetime fixtures. Separate suites exercise production eligibility/lifecycle. Not headset validation.'},indent=2))
raise SystemExit(v.returncode)
