from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
s=(R/'source/accessibility_hd.inc').read_text();a=s.index('static u32 __attribute__((ms_abi)) s26hd_ray_pre');b=s.index('\nstatic float ',a)
code=r'''
#include <cstring>
#include <cassert>
#include <cstdio>
using u32=unsigned;using u8=unsigned char;
const void* g_h34HandNewton[2]={(void*)1,(void*)2};
alignas(8) u8 wrapper[0x300];void* userdata;int trigger;bool readable=true,typed=true,area=true;
int trig(const void*){return trigger;}auto p_h14IsTrigger=trig;
void* ud(const void*){return userdata;}auto p_h14GetUserData=ud;
bool h20_mem_readable(const void*,u32){return readable;}
int h22_rtti_name(const void* p,char* out,u32){if(!typed)return 0;strcpy(out,p==wrapper?"cPhysicsBodyNewton":area?"cLuxArea":"cLuxProp");return 1;}
bool h25_str_contains(const char*a,const char*b){return strstr(a,b)!=nullptr;}
'''+s[a:b]+r'''
int main(){const void* body=(void*)3;userdata=wrapper;
 *(const void**)(wrapper+0x2e8)=body;wrapper[0xe4]=1;*(void**)(wrapper+0x2c0)=(void*)4;
 assert(!s26hd_ray_pre(body,nullptr,nullptr)); // actual reported non-colliding area
 area=false;assert(s26hd_ray_pre(body,nullptr,nullptr)); // prop screens still available
 area=true;wrapper[0x2e0]=1;assert(s26hd_ray_pre(body,nullptr,nullptr)); // solid area blocks
 wrapper[0xe4]=0;assert(!s26hd_ray_pre(body,nullptr,nullptr));
 typed=false;assert(s26hd_ray_pre(body,nullptr,nullptr));
 typed=true;readable=false;assert(s26hd_ray_pre(body,nullptr,nullptr));
 readable=true;*(const void**)(wrapper+0x2e8)=(void*)5;assert(s26hd_ray_pre(body,nullptr,nullptr));
 userdata=nullptr;assert(s26hd_ray_pre(body,nullptr,nullptr)); // raw world geometry
 assert(!s26hd_ray_pre((void*)1,nullptr,nullptr));assert(!s26hd_ray_pre((void*)2,nullptr,nullptr));
 trigger=1;assert(!s26hd_ray_pre(body,nullptr,nullptr));
 puts("PASS 11 production ray-filter cases: area/solid/prop/inactive/unknown/hands/trigger");
}
'''
p=R/'build/access_ray_filter_hf.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
