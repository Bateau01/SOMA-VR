"""Production ray callbacks + shipped Newton.dll, isolated real physics world.
HPL metadata is a fixture; no live game or headset is required.
"""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/accessibility_hd.inc').read_text()
a=s.index('static u32 __attribute__((ms_abi)) s26hd_ray_pre');b=s.index('static S26HDHit s26hd_ray(',a)
code=r'''
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cmath>
using u32=unsigned;using i32=int;using u8=unsigned char;
struct S26HDHit{const void* body;float t;};
const void* g_h34HandNewton[2]={};
struct Owner{const char* type;};
struct Wrapper{alignas(8) u8 bytes[0x300];};
Wrapper wrappers[64];int used=0,checks=0;
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
bool h20_mem_readable(const void* w,u32){for(int i=0;i<used;i++)if(w==wrappers[i].bytes)return true;return false;}
int h22_rtti_name(const void*p,char*out,u32){if(!p)return 0;for(int i=0;i<used;i++)if(p==wrappers[i].bytes){strcpy(out,"cPhysicsBodyNewton");return 1;}strcpy(out,((const Owner*)p)->type);return 1;}
bool h25_str_contains(const char*a,const char*b){return strstr(a,b)!=nullptr;}
using GetUD=void*(__attribute__((ms_abi)) *)(const void*);
using IsTrigger=int(__attribute__((ms_abi)) *)(const void*);
GetUD p_h14GetUserData;IsTrigger p_h14IsTrigger;
'''+s[a:b]+r'''
template<class T>T api(HMODULE n,const char*s){auto p=GetProcAddress(n,s);CHECK(p);return (T)p;}
int main(){
 auto n=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll");CHECK(n);
 auto create=api<void*(*)()>(n,"NewtonCreate");auto destroy=api<void(*)(void*)>(n,"NewtonDestroy");
 auto box=api<void*(*)(void*,float,float,float,int,const float*)>(n,"NewtonCreateBox");
 auto body=api<void*(*)(void*,void*,const float*)>(n,"NewtonCreateBody");
 auto setUD=api<void(*)(const void*,void*)>(n,"NewtonBodySetUserData");
 auto destroyBody=api<void(*)(void*,void*)>(n,"NewtonDestroyBody");
 p_h14GetUserData=api<GetUD>(n,"NewtonBodyGetUserData");
 p_h14IsTrigger=api<IsTrigger>(n,"NewtonCollisionIsTriggerVolume");
 using Ray=void(*)(void*,const float*,const float*,decltype(&s26hd_ray_hit),void*,decltype(&s26hd_ray_pre));
 auto ray=api<Ray>(n,"NewtonWorldRayCast");
 auto w=create();Owner area={"cLuxArea"},helper={"cInvisibleHelper"},prop={"cLuxProp"};
 auto add=[&](float x,float size,Owner*owner,bool collide,bool active){
  float m[16]={1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1};
  void*c=box(w,size,size,size,0,nullptr);void*b=body(w,c,m);
  auto&v=wrappers[used++];memset(&v,0,sizeof v);v.bytes[0xe4]=active;v.bytes[0x2e0]=collide;
  *(void**)(v.bytes+0x2c0)=owner;*(void**)(v.bytes+0x2e8)=b;setUD(b,v.bytes);return b;
 };
 auto cast=[&](float end){float a[4]={0,0,0,0},b[4]={end,0,0,0};S26HDHit h={nullptr,1};ray(w,a,b,s26hd_ray_hit,&h,s26hd_ray_pre);return h;};
 void* target=add(2,.2f,&prop,true,true);
 CHECK(cast(3).body==target);CHECK(fabsf(cast(3).t-1.9f/3)<.001f);
 // Both helpers enclose the ray origin; this reproduces the live failure.
 void* a=add(0,10,&area,false,true);void* h=add(0,8,&helper,false,true);
 CHECK(cast(3).body==target);
 // Demonstrate regression: the old trigger-only prefilter reports t=0.
 float start[4]={0},end[4]={3,0,0,0};S26HDHit old={nullptr,1};
 ray(w,start,end,s26hd_ray_hit,&old,nullptr);CHECK(old.body!=target&&old.t==0);
 // Non-colliding prop screen must remain selectable; nearest wins.
 void* screen=add(1,.2f,&prop,false,true);CHECK(cast(3).body==screen);
 void* wall=add(.5f,.1f,nullptr,true,true);CHECK(cast(3).body==wall);
 destroyBody(w,wall);CHECK(cast(3).body==screen);
 // Ignore inactive targets, but no tunnelling through unknown solid geometry.
 auto sw=(u8*)p_h14GetUserData(screen);sw[0xe4]=0;CHECK(cast(3).body==target);
 wall=add(.5f,.1f,nullptr,true,true);setUD(wall,nullptr);CHECK(cast(3).body==wall);destroyBody(w,wall);
 // The two owned hand colliders cannot steal the query.
 g_h34HandNewton[0]=add(.2f,.1f,&prop,true,true);g_h34HandNewton[1]=add(.4f,.1f,&prop,true,true);CHECK(cast(3).body==target);
 CHECK(!cast(1).body);CHECK(!cast(-3).body);
 // A solid area is a blocker even though other areas are ignored.
 wall=add(.8f,.1f,&area,true,true);CHECK(cast(3).body==wall);destroyBody(w,wall);
 // Repeated rays must not mutate world lifetime or selection.
 for(int i=0;i<1000;i++)CHECK(cast(3).body==target);
 destroy(w);printf("PASS %d native Newton + production filter checks; old origin-blocking failure reproduced\n",checks);
}
'''
p=R/'build/access_ray_native_hf.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/access_ray_native_hf.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Real shipped Newton.dll and production prefilter/hit callbacks; HPL metadata fixtures, not a live map.'},indent=2))
raise SystemExit(v.returncode)
