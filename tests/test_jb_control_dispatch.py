"""Extracted production registered-control dispatch; mocked geometry/native callbacks."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/rocker_y.inc').read_text();a=s.index('static i32 s26hr_control_contact(');b=s.index('static i32 s26y_near(',a)
code=r'''
#include <cmath>
#include <cstdio>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;using u64=unsigned long long;
struct S26YRocker{int used,blocked,handMask,active,frontAxis;void*owner;const void*raw;void*wrapper;void*mainWrapper;const void*mainRaw;} g_s26yRocker[1];
struct H25TString{unsigned capacity;};
using PFN_H25_OnInteract=u64(*)(void*,int,void*,const float*,H25TString*);
int g_s26yCount=1,g_s26yCalling,g_s26yLogs=48,g_lastSyncResult,g_s26huWorldControlAllowed=1;
int terminal=0,pause=0,blocked=0,hasPoint=1,nearGate=1,permission=1,callbacks=0,haptics=0,checks=0;
unsigned char wrapper[0x300],mainWrapper[0x300];int rawBody,mainBody,ownerObj;
float gapValue=.01f;int zeroNormal=0,zeroFront=0;
#define H482_POKE_SWITCH_ICON 13
#define H576AC_HAPTIC_CONFIRM 1
int h5730_exact_terminal_state(int,int,int,int){return terminal;}
int h20_mem_readable(const void*p,unsigned){return p!=0;}
int s26y_body_slot(const void*b){return b==&rawBody?0:-1;}
int s26hr_control_blocked(void*){return blocked;}
int h5754h_pause_active(){return pause;}
int h14_point_to_body(const void*,const float*p,float*g,float*cp){*g=gapValue;memcpy(cp,p,12);if(!zeroNormal)cp[2]-=gapValue;return hasPoint;}
int h10_norm3(float*v){float d=std::sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);if(d<.00001f)return 0;for(int a=0;a<3;a++)v[a]/=d;return 1;}
void matrix(const void*,float*m){memset(m,0,64);if(!zeroFront)m[10]=1;}
auto p_h14GetMatrix=matrix;
float h572_index_skin_gap(int,int,float g){return g-.005f;}
float h5755ea_world_units_per_meter(){return 1;}
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
int s26y_near_gate(float,float,float){return nearGate;}
void s26fc_hint_near(int){}
u64 on(void*,int,void*,const float*,H25TString*){callbacks++;return 1;}
int h483_surface_target_info(void*,void*,int*i,const void**raw,void**can,void**fn){*i=13;*raw=&mainBody;*can=(void*)1;*fn=(void*)on;return permission;}
void zero_bytes(void*p,unsigned n){memset(p,0,n);}
int s26ah_begin(int,const void*,int){return 0;}
void s26ah_sample(int,const char*){}
void h576ac_queue_haptic(int,int){haptics++;}
void ext_Log(const char*,...){}
'''+s[a:b]+r'''
#define C(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
int main(){
 *(void**)(wrapper+0x2e8)=&rawBody;*(void**)(mainWrapper+0x2e8)=&mainBody;*(void**)(mainWrapper+0x2c0)=&ownerObj;
 auto &r=g_s26yRocker[0];r={1,0,0,1,2,&ownerObj,&rawBody,wrapper,mainWrapper,&mainBody};
 float p[3]={0,0,.01f},d[3]={0,0,-1};
 for(int* bad:{&zeroNormal,&zeroFront}){*bad=1;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==2);C(callbacks==0);*bad=0;}
 hasPoint=0;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==2);hasPoint=1;
 nearGate=0;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==2);nearGate=1;
 permission=0;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==1);C(callbacks==0);permission=1;
 for(int* flag:{&blocked,&pause,&g_lastSyncResult}){*flag=1;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==1);C(callbacks==0);*flag=0;}
 terminal=1;g_s26huWorldControlAllowed=0;C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==1);C(callbacks==0);terminal=0;
 C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==1);C(callbacks==1&&haptics==1&&r.blocked&&r.handMask==1);
 C(s26hr_control_contact(0,wrapper,&ownerObj,p,d,4,.005f)==1);C(callbacks==1&&haptics==1);
 printf("PASS %d dispatch boundary assertions\n",checks);
}
'''
code=code.replace('#include <cmath>','#include <cmath>\n#include <initializer_list>')
p=r/'build/jb_control_dispatch.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-control-dispatch.json').write_text(json.dumps(dict(scope=__doc__,exit=v.returncode,output=v.stdout+v.stderr),indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
