"""Execute production post-physics dispatch with explicit native-script doubles.
Tests callback counts, independent hands, permissions and cancellation, not HPL VM integration.
"""
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
using i32=int;using u32=unsigned;using u8=unsigned char;using u64=unsigned long long;
int checks;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
void zero_bytes(void*p,size_t n){memset(p,0,n);}
struct S26HDPull{const void*body;void*wrapper,*owner;float last[3],age;};
struct S26HDHit{const void*body;float t;};
struct H25TString{char storage[16];u64 size,capacity;};
using PFN_H25_OnInteract=u64(*)(void*,i32,void*,const float*,const H25TString*);
S26HDPull g_s26hdPull[2],g_s26hlInteraction[2];u8 g_s26hlReadStage[2],g_s26hlHeld[2];u32 g_s26hlReadId[2];
float g_s26hlInteractionPoint[2][3];
int g_s26hlInteractionEnabled,g_s26hdRemoteEnabled,g_h30NativeMouseDown,g_h25PendingValid[2],g_s26CutsceneHandsHidden,g_h576bfMapTransitionActive;
const void*g_h14GripBody[2];u32 g_s26hdRemoteRange=2,g_s26hlReadScope;
i32 g_h576avActiveInteractHand=-1;const void*g_h576avActiveInteractBody;
const void*g_s26bvReadableWrapper;
bool freeState=true,remoteState=true,busy=false,paused=false,live=true,target=true,aim=true,visible=true,publish=true,result=true;
int calls,wakes,haptics;unsigned char wrappers[2][0x300];int objects[2],owners[2];
float h5755ea_world_units_per_meter(){return 1;}
int s26hd_free_state(){return freeState;}int s26hk_remote_state(){return remoteState;}int s26hk_remote_native_busy(){return busy;}int h5754h_pause_active(){return paused;}
int s26hd_live(S26HDPull*,float){return live;}int h20_mem_readable(const void*,u32){return true;}
void p_s26hdWake(const void*,int){wakes++;}
int s26hd_aim(int,float*,float*){return aim;}
int s26hg_visible(const void*,const float*,const float*,float,float,float,float*,float*,void**,void**){return visible;}
S26HDHit s26hd_ray(const float*,const float*){return {nullptr,1};}
enum {H576AC_HAPTIC_CONFIRM=2};void h576ac_queue_haptic(int,int){haptics++;}
u64 invoke(void*o,i32,void*w,const float*,const H25TString*){
 calls++;if(g_s26hlReadScope){CHECK(g_h576avActiveInteractHand>=0);CHECK(g_h576avActiveInteractBody);if(publish)g_s26bvReadableWrapper=w;}
 return result;
}
int s26hd_target(const void*b,void**w,void**o,i32*icon,void**on){int h=b==objects?0:1;*w=wrappers[h];*o=&owners[h];*icon=22;*on=(void*)invoke;return target;}
int s26hl_interaction_target(void*,void*,void**on){*on=(void*)invoke;return target;}
'''+fn('s26hl_read_catch')+fn('s26hl_read_inflight')+fn('s26hl_dispatch')+r'''
void setup(){
 memset(g_s26hdPull,0,sizeof g_s26hdPull);memset(g_s26hlInteraction,0,sizeof g_s26hlInteraction);
 memset(g_s26hlReadStage,0,2);memset(g_s26hlReadId,0,sizeof g_s26hlReadId);
 freeState=remoteState=live=target=aim=visible=publish=result=true;busy=paused=false;
 g_s26hlInteractionEnabled=g_s26hdRemoteEnabled=1;g_s26hlReadScope=0;g_h576avActiveInteractHand=-1;g_h576avActiveInteractBody=nullptr;
 g_h30NativeMouseDown=g_s26CutsceneHandsHidden=g_h576bfMapTransitionActive=calls=wakes=haptics=0;
 for(int h=0;h<2;h++){
  g_h14GripBody[h]=nullptr;g_h25PendingValid[h]=0;g_s26hlHeld[h]=1;
  *(const void**)(wrappers[h]+0x2e8)=&objects[h];*(u32*)(wrappers[h]+0x3c)=100+h;
  g_s26hdPull[h].body=&objects[h];g_s26hdPull[h].wrapper=wrappers[h];g_s26hdPull[h].owner=&owners[h];g_s26hlReadStage[h]=1;
 }
}
int main(){
 for(int reason=0;reason<14;reason++){
  setup();if(reason==1)g_s26hdRemoteEnabled=0;if(reason==2)g_s26hlHeld[0]=g_s26hlHeld[1]=0;
  if(reason==3)g_h14GripBody[0]=g_h14GripBody[1]=(void*)9;
  if(reason==4)g_h25PendingValid[0]=g_h25PendingValid[1]=1;
  if(reason==5)remoteState=false;if(reason==6)busy=true;if(reason==7)g_s26CutsceneHandsHidden=1;
  if(reason==8)paused=true;if(reason==9)g_h576bfMapTransitionActive=1;
  if(reason==10)live=false;if(reason==11)target=false;if(reason==12)aim=false;if(reason==13)visible=false;
  s26hl_dispatch();CHECK(calls==(reason?0:2));CHECK(g_s26hlReadScope==0&&g_h576avActiveInteractHand==-1&&!g_h576avActiveInteractBody);
  for(int h=0;h<2;h++){CHECK(bool(g_s26hdPull[h].body)==!reason);CHECK(bool(s26hl_read_inflight(100+h))==!reason);CHECK(bool(s26hl_read_catch(&objects[h]))==!reason);}
  s26hl_dispatch();CHECK(calls==(reason?0:2)); // callback is never replayed while pulling
 }
 setup();publish=false;s26hl_dispatch();CHECK(calls==2&&!g_s26hdPull[0].body&&!g_s26hdPull[1].body);
 setup();result=false;s26hl_dispatch();CHECK(calls==2&&!g_s26hdPull[0].body&&!g_s26hdPull[1].body);
 setup();s26hl_dispatch();g_s26hdPull[0].body=nullptr;CHECK(!s26hl_read_inflight(100)&&s26hl_read_inflight(101));
 for(int reason=0;reason<10;reason++){
  setup();memset(g_s26hlReadStage,0,2);g_s26hlInteraction[0]=g_s26hdPull[0];memset(g_s26hdPull,0,sizeof g_s26hdPull);
  if(reason==1)g_s26hlInteractionEnabled=0;if(reason==2)freeState=false;if(reason==3)g_h30NativeMouseDown=1;
  if(reason==4)g_h14GripBody[0]=(void*)9;if(reason==5)g_h25PendingValid[0]=1;
  if(reason==6)paused=true;if(reason==7)g_h576bfMapTransitionActive=1;if(reason==8)live=false;if(reason==9)target=false;
  s26hl_dispatch();CHECK(calls==(reason?0:1));CHECK(!g_s26hlInteraction[0].body);s26hl_dispatch();CHECK(calls==(reason?0:1));
 }
 printf("PASS %d production readable/interaction dispatch checks\n",checks);
}
'''
p=R/'build/remote_dispatch_hl.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
