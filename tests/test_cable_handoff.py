"""Execute production accepted-cable handoff with controlled native contracts.
Does not simulate Newton forces or execute AngelScript."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=(R/'source/s26n.c').read_text();a=s.index('static i32 s26dl_latch_accepted_cable(',s.index('static i32 s26db_bind_aux_cable'))
b=s.index('static i32 h481_bind_nearby_mechanism(',a);fn=s[a:b]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
typedef struct {int jointed;const void* newtonBody;u32 physicsStep;float contact[3];float meshGap;}H25PendingInteract;
static void* g_h14GripBody[2];static int g_h576bfMapTransitionActive;
static const void* g_s26dbCableClaim[2];static u32 g_s26dbCableClaimStep[2],g_h5755haGripEdgeStep[2],g_h14PhysicsSteps;
static int g_lastSqueezeActive[2],g_h30NativeMouseDown,g_h30NativeUseHand,g_h31NativeUseJointed;
static float g_lastSqueeze[2];static void* g_h39NativeUseProp[2];
static int g_h5755gwPreserveExistingGrabUse[2],g_h552ContactLatchBypass[2],g_h5755haEdgeNativeActive[2];
static struct {int valid;}g_h5755chGrabPending[2];
static int g_h5755chGrabExpected,g_h5755chGrabStateActive,g_h5755chGrabPrimaryHand;
static const void* g_h5755chGrabStateBody;static void* g_h5755chGrabStateWrapper,*g_h5755chGrabStateOwner;
static u32 g_h5755cjGrabExpectedStep;
#define H481_MECH_NONE 0
static int icon=2;
static int iconfn(void*a,int b,void*c){return icon;}
typedef int (*PFN_H25_GetInteractIconId)(void*,int,void*);
static void* vtable[16];static void** fakeOwner;
static int h20_mem_readable(void*p,unsigned n){return p!=0;}
static int h25_soma_code_ptr(void*p){return p==(void*)iconfn;}
static void* liveOwner,*liveWrapper;static int semantic,compliant=1,pose=1,latchFail,latched,adopted,scopeOK;
static const void* joint=(void*)4;static float mass=5;
static void* h482_body_owner(const void*b,void**w){*w=liveWrapper;return liveOwner;}
static const void* h568_first_external_joint(const void*b){return joint;}
static int h553_body_semantic_mechanism(const void*b,void*w){return semantic;}
static int h484_classify_compliant_cluster(int h,const void*b,void*o){return compliant;}
static float h482_body_mass(const void*b){return mass;}
static int h34_physical_hand_model(int h,float*m){memset(m,0,64);return pose;}
static void h14_latch(int h,const void*b,float gap,float mass,const float*m,const float*p,float rad,const float*c,int i,int j,const void*k){
 latched++;scopeOK=g_h5755gwPreserveExistingGrabUse[h]&&g_h552ContactLatchBypass[h];if(!latchFail)g_h14GripBody[h]=(void*)b;}
static void h5755gw_adopt_existing_same_owner_grab(int h,void*o){adopted++;}
static void ext_Log(const char*f,...){(void)f;}
static int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 H25PendingInteract p={0,(void*)1,30,{1,2,3}};vtable[13]=(void*)iconfn;fakeOwner=vtable;liveOwner=&fakeOwner;liveWrapper=(void*)3;
 for(int h=0;h<2;h++)for(int fault=0;fault<23;fault++){
  memset(g_h14GripBody,0,sizeof(g_h14GripBody));g_h14GripBody[1-h]=(void*)99;
  g_s26dbCableClaim[h]=p.newtonBody;g_s26dbCableClaimStep[h]=g_h5755haGripEdgeStep[h]=g_h14PhysicsSteps=30;
  g_lastSqueezeActive[h]=1;g_lastSqueeze[h]=1;g_h30NativeMouseDown=1;g_h30NativeUseHand=h;g_h31NativeUseJointed=0;
  g_h39NativeUseProp[h]=liveOwner;g_h576bfMapTransitionActive=0;semantic=0;compliant=pose=1;mass=5;joint=(void*)4;
  latched=adopted=scopeOK=latchFail=0;p.jointed=0;p.meshGap=.0065f;icon=2;float preMass=0;
  switch(fault){case 1:g_s26dbCableClaim[h]=(void*)8;break;case 2:g_s26dbCableClaimStep[h]=29;break;
  case 3:g_h5755haGripEdgeStep[h]=29;break;case 4:g_h14PhysicsSteps=32;break;case 5:g_lastSqueezeActive[h]=0;break;
  case 6:g_lastSqueeze[h]=0;break;case 7:g_h30NativeMouseDown=0;break;case 8:g_h30NativeUseHand=1-h;break;
  case 9:g_h39NativeUseProp[h]=(void*)8;break;case 10:g_h576bfMapTransitionActive=1;break;case 11:semantic=1;break;
  case 12:compliant=0;break;case 13:mass=0;break;case 14:joint=0;break;case 15:pose=0;break;case 16:latchFail=1;break;case 17:joint=0;preMass=5;break;case 18:p.meshGap=.1;break;case 19:icon=13;break;
  case 20:g_h14PhysicsSteps=31;joint=0;break;case 21:p.jointed=1;break;case 22:g_h14PhysicsSteps=29;break;}
  int ok=s26dl_latch_accepted_cable(h,&p,liveOwner,liveWrapper,preMass);
  int success=fault==0||fault==1||fault==2||fault==14||fault==20;C(ok==success);C(!g_h5755gwPreserveExistingGrabUse[h]&&!g_h552ContactLatchBypass[h]);C(g_h14GripBody[1-h]==(void*)99);
  if(success){C(latched==1&&adopted==1&&scopeOK);C(g_h5755chGrabStateBody==p.newtonBody);C(g_h5755chGrabStateOwner==liveOwner);C(g_h5755cjGrabExpectedStep==g_h14PhysicsSteps);}
  else {C(!adopted);C(latched==(fault==16));}
 }
 C(!s26dl_latch_accepted_cable(-1,&p,liveOwner,liveWrapper,0));C(!s26dl_latch_accepted_cable(0,0,liveOwner,liveWrapper,0));
 printf("PASS %d accepted cable handoff/rejection/other-hand ownership checks\n",checks);return 0;
}
'''
c=B/'cable_handoff_test.c';c.write_text(head+fn+main);exe=B/'cable_handoff_test.exe'
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
assert s.index('if(orv&0xffu){',s.index('NATIVE OnInteract %s'))<s.index('if(s26dl_latch_accepted_cable(hand,&p,entity,wrapper,h5755haPreMass))')
print('PASS native OnInteract acceptance precedes physical handoff; no script changes')
