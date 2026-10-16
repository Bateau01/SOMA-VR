"""Real eligibility functions; native script and owner lookups are explicit mocks."""
from pathlib import Path
import re,subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/accessibility_hd.inc').read_text()
def fn(n):
 a=re.search(r'static i32 '+n+r'\(',s).start();b=s.index('{',a);i=b+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
code=r'''
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <initializer_list>
using i32=int;using u32=unsigned;using u8=unsigned char;
int checks=0;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
unsigned char wrapperData[0x300];
const void* target=(void*)3;void* wr=wrapperData;void* own=(void*)5;
const void* g_h14GripBody[2],*g_s26ckPadBody,*g_s26xPhoneRaw,*g_h576bOmniBody;
int resolve=1,prop=1,surface=1,rawmatch=1,icon=2,jointed=0,inventory=0,mechanism=0,calls=0;
float mass=1;
u32 g_s26hdRemoteEntry;int g_s26hfTargetResult,g_s26hfIcon;
int h25_resolve_native_target(const void*,void**w,void**o,void**can,void**on,u32*,char*rt,u32){*w=wr;*o=own;*can=(void*)8;*on=(void*)9;strcpy(rt,prop?"cLuxProp":"cLuxArea");return resolve;}
bool h25_str_contains(const char*a,const char*b){return strstr(a,b);}
int h483_surface_target_info(void*,void*,int*i,const void**raw,void**,void**){calls++;CHECK(g_s26hdRemoteEntry==1);*i=icon;*raw=rawmatch?target:(void*)99;return surface;}
void getmass(const void*,float*m,float*,float*,float*){*m=mass;}
void* joint(const void*){return jointed?(void*)1:nullptr;}
struct H576AAInvItem{int stowed,remoteDropped;char logical[96];void* owner;};
H576AAInvItem item;
H576AAInvItem* h576aa_inv_find_body(const void*){return inventory?&item:nullptr;}
int g_h576mScriptRuntimePublished=1,g_h576bfMapTransitionActive,g_s26CutsceneHandsHidden,g_s26ManualHeal;
int g_h576bOmniState,g_h576dDockReleasePending,g_h576dDockReleaseActive,g_h576eBindPending,g_h576bCaptureNextInteract,g_h576aoOmniHidePending;
void* g_h576bOmniOwner;
char g_h576cCanonicalEntityName[96];
enum{H576B_OMNI_LOOSE=4};
int readable=1,ownerMatch=1;
int h20_mem_readable(void*,unsigned){return readable;}
int h37_native_wrapper_matches_entity(void*,void*){return ownerMatch;}

int h553_body_semantic_mechanism(const void*,void**){return mechanism;}
int p_s26hdWake=1,p_h14GetVelocity=1,p_h14SetVelocity=1,p_h14GetMatrix=1,p_h14WorldAABB=1;
auto p_h14GetMass=getmass;auto p_h14GetFirstJoint=joint;
enum{H5755HL_CARRY_ONE_HANDED_ICON=2,H481_MECH_NONE=0};
void reset(){
 memset(wrapperData,0,sizeof(wrapperData));*(const void**)(wrapperData+0x2e8)=target;wrapperData[0xe4]=wrapperData[0x2e0]=1;
 memset(&item,0,sizeof(item));strcpy(item.logical,"chip");item.owner=own;
 g_h576mScriptRuntimePublished=1;g_h576bfMapTransitionActive=g_s26CutsceneHandsHidden=g_s26ManualHeal=0;
 g_h576bOmniState=0;g_h576dDockReleasePending=g_h576dDockReleaseActive=g_h576eBindPending=g_h576bCaptureNextInteract=g_h576aoOmniHidePending=0;
 g_h576bOmniOwner=own;strcpy(g_h576cCanonicalEntityName,"Catherine");readable=ownerMatch=1;
 resolve=prop=surface=rawmatch=1;icon=2;jointed=inventory=mechanism=calls=0;mass=1;g_s26hdRemoteEntry=7;g_h14GripBody[0]=g_h14GripBody[1]=g_s26ckPadBody=g_s26xPhoneRaw=g_h576bOmniBody=nullptr;p_s26hdWake=1;}
struct S26HLAssembly{const void* body[32];u32 count;float mass;};
int s26hl_assembly(const void*,void*,S26HLAssembly*a){a->mass=mass;return !jointed&&mass>.001f&&mass<=25;}
'''+fn('s26hd_target')+fn('s26hj_dropped_owned')+fn('s26hd_loose')+r'''
int main(){void*w,*o;float m;
 for(int reason=0;reason<17;reason++){
  reset();
  if(reason==1)g_h14GripBody[0]=target;if(reason==2)g_h14GripBody[1]=target;
  if(reason==3)g_s26ckPadBody=target;if(reason==4)g_s26xPhoneRaw=target;
  if(reason==5)resolve=0;if(reason==6)prop=0;if(reason==7)surface=0;
  if(reason==8)rawmatch=0;if(reason==9)icon=17;if(reason==10)g_h576bOmniBody=target;
  if(reason==11)inventory=1;if(reason==12)jointed=1;if(reason==13)mechanism=1;
  if(reason==14)mass=0;if(reason==15)mass=25.1f;if(reason==16)p_s26hdWake=0;
  CHECK(bool(s26hd_loose(target,&w,&o,&m))==(reason==0));CHECK(g_s26hdRemoteEntry==7);
 }
 reset();CHECK(!s26hd_loose(nullptr,&w,&o,&m));CHECK(calls==0);
 for(float v:{.001f,.0011f,1.f,6.f,10.1f,20.f,25.f,25.001f}){reset();mass=v;CHECK(bool(s26hd_loose(target,&w,&o,&m))==(v>.001f&&v<=25));}
 // Terminal target remains selectable but never qualifies as a remotely pulled prop.
 reset();icon=17;int i;void*on;CHECK(s26hd_target(target,&w,&o,&i,&on));CHECK(i==17&&!s26hd_loose(target,&w,&o,&m));
 // Owned dropped objects can use their physical carrier even though native
 // desktop CanInteract/icon is not a loose-prop interaction. Never invoke it.
 for(int omni=0;omni<2;omni++)for(int reason=0;reason<22;reason++){
  reset();surface=0;icon=17;
  if(omni){g_h576bOmniBody=target;g_h576bOmniState=H576B_OMNI_LOOSE;}
  else {inventory=1;item.remoteDropped=1;}
  if(reason==1){if(omni)g_h576bOmniState=5;else item.stowed=1;}
  if(reason==2){if(omni)g_h576bOmniState=0;else item.remoteDropped=0;}
  if(reason==3)jointed=1;if(reason==4)mass=0;if(reason==5)mechanism=1;
  if(reason==6)g_h14GripBody[0]=target;if(reason==7)g_h14GripBody[1]=target;
  if(reason==8)g_s26xPhoneRaw=target;if(reason==9)g_s26ckPadBody=target;
  if(reason==10)g_h576mScriptRuntimePublished=0;if(reason==11)g_h576bfMapTransitionActive=1;
  if(reason==12)g_s26CutsceneHandsHidden=1;if(reason==13)g_s26ManualHeal=1;
  if(reason==14)wrapperData[0xe4]=0;if(reason==15)wrapperData[0x2e0]=0;
  if(reason==16)*(const void**)(wrapperData+0x2e8)=(void*)99;
  if(reason==17)ownerMatch=0;if(reason==18)readable=0;if(reason==19)resolve=0;
  if(reason==20){item.owner=(void*)99;g_h576bOmniOwner=(void*)99;}
  if(reason==21){item.logical[0]=0;g_h576cCanonicalEntityName[0]=0;}
  CHECK(bool(s26hd_loose(target,&w,&o,&m))==(reason==0));CHECK(calls==0);
 }
 for(int reason=0;reason<5;reason++){
  reset();g_h576bOmniBody=target;g_h576bOmniState=H576B_OMNI_LOOSE;
  if(reason==0)g_h576dDockReleasePending=1;if(reason==1)g_h576dDockReleaseActive=1;
  if(reason==2)g_h576eBindPending=1;if(reason==3)g_h576bCaptureNextInteract=1;if(reason==4)g_h576aoOmniHidePending=1;
  CHECK(!s26hd_loose(target,&w,&o,&m));
 }
 printf("PASS %d production target/eligibility checks\n",checks);
}
'''
p=R/'build/access_eligibility_hf.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
