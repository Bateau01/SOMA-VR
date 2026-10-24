"""Extracted registered control dispatcher: mocked geometry, real ownership/latch branch."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/rocker_y.inc').read_text()
a=s.index('static i32 s26y_near_gate');b=s.index('// One first-hit ray',a)
code=r'''
#include <cmath>
#include <cstring>
#include <cstdio>
#include <cstdlib>
using i32=int;using u32=unsigned;using u64=unsigned long long;using u8=unsigned char;
struct S26YRocker{u32 id;i32 used,active,blocked,frontAxis,handMask;void *owner,*mainWrapper,*wrapper;const void *mainRaw,*raw;};
S26YRocker g_s26yRocker[64];int g_s26yCount=3,g_lastSyncResult,g_s26yCalling;unsigned g_s26yLogs;
struct H25TString{char data[16];unsigned size,capacity;};
using PFN_H25_OnInteract=u64(*)(void*,int,void*,const float*,H25TString*);
alignas(16) char mainW[0x300],childW[3][0x300];int owner[3],raw[4],calls;bool permitted=true;
int h20_mem_readable(const void*p,unsigned){return p!=nullptr;}
int s26y_body_slot(const void*p){for(int i=0;i<3;i++)if(p==&raw[i])return i;return -1;}
float h5755ea_world_units_per_meter(){return 1;}
int h5754h_pause_active(){return 0;}
int terminal;unsigned g_s26huWorldControlAllowed;int h5730_exact_terminal_state(int,int,int,int){return terminal;}
int h10_norm3(float*p){float n=sqrtf(p[0]*p[0]+p[1]*p[1]+p[2]*p[2]);if(n<.00001)return 0;for(int i=0;i<3;i++)p[i]/=n;return 1;}
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
int h14_point_to_body(const void*,const float*p,float*g,float*c){*g=.008f;c[0]=p[0];c[1]=p[1]-.008f;c[2]=p[2];return 1;}
void matrix(const void*,float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;}
auto p_h14GetMatrix=matrix;
float h572_index_skin_gap(int,int,float g){return g-.005f;}
void s26fc_hint_near(int){}
u64 on(void*,int,void*w,const float*,H25TString*){if(w!=mainW)abort();calls++;return 1;}
int h483_surface_target_info(void*w,void*,int*i,const void**r,void**c,void**o){if(!g_s26yCalling||w!=mainW)abort();*i=13;*r=&raw[3];*o=(void*)on;return permitted;}
void zero_bytes(void*p,unsigned n){memset(p,0,n);}
int s26ah_begin(int,const void*,int){return 0;}void s26ah_sample(int,const char*){}
void h576ac_queue_haptic(int,int){}void ext_Log(const char*,...){}
#define H482_POKE_SWITCH_ICON 13
#define H576AC_HAPTIC_CONFIRM 1
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
'''+s[a:b]+r'''
int main(){
 *(const void**)(mainW+0x2e8)=&raw[3];*(void**)(mainW+0x2c0)=&owner[0];
 for(int i=0;i<3;i++){*(const void**)(childW[i]+0x2e8)=&raw[i];auto&r=g_s26yRocker[i];r.used=r.active=1;r.owner=&owner[i==1?0:i];r.mainWrapper=mainW;r.mainRaw=&raw[3];r.frontAxis=1;}
 float tip[3]={0,.01,0},dir[3]={0,-1,0};
 for(int h=0;h<2;h++){
  calls=0;for(auto&r:g_s26yRocker)r.blocked=0;
  permitted=false;C(s26y_near(h,childW[0],&owner[0],tip,dir,4)==1);C(calls==0&&!g_s26yRocker[0].blocked);
  permitted=true;C(s26y_near(h,childW[0],&owner[0],tip,dir,4)==1);C(calls==1);
  C(s26y_near(h,childW[1],&owner[0],tip,dir,4)==1);C(calls==1); // same owner, different child
  C(!s26hr_control_blocked(&owner[2])); // neighboring control not globally latched
  g_s26yRocker[0].blocked=0;
  g_s26yRocker[0].frontAxis=2;C(s26y_near(h,childW[0],&owner[0],tip,dir,4)==1);C(calls==1);
  g_s26yRocker[0].frontAxis=1;
 }
 // Explicit palm path preserves permission and rejects back-facing contact.
 for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
 calls=0;float badDir[3]={0,1,0};
 C(s26hr_control_contact(0,childW[0],&owner[0],tip,badDir,0,.005f)==1);C(calls==0);
 C(s26hr_control_contact(0,childW[0],&owner[0],tip,dir,0,.005f)==1);C(calls==1);
 C(s26hr_control_contact(0,childW[1],&owner[0],tip,dir,0,.005f)==1);C(calls==1);

 for(int h=0;h<2;h++){
  terminal=1;g_s26huWorldControlAllowed=0;
  for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
  calls=0;s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==0);
  g_s26huWorldControlAllowed=1;
  s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  for(auto&r:g_s26yRocker){r.blocked=0;r.handMask=0;}
  permitted=false;s26hr_control_contact(h,childW[0],&owner[0],tip,dir,0,.005f);C(calls==1);
  permitted=true;
 }
 printf("PASS %d registered control assertions\n",checks);
}
'''
p=R/'build/registered_controls_hu.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence/registered_controls_hu.json').write_text(json.dumps({'scope':__doc__,'exit':r.returncode,'output':r.stdout+r.stderr},indent=2));print(r.stdout+r.stderr);raise SystemExit(r.returncode)
