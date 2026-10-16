from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];A=R/'audit/movement-unit';A.mkdir(parents=True,exist_ok=True)
s=(R/'source/s26n.c').read_text()
def fun(name):
 start=s.index('static void '+name+'(void){');p=s.index('{',start);depth=1;i=p+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
head=r'''
#include <assert.h>
#include <stdio.h>
#include <math.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
#define __ATOMIC_ACQ_REL 0
#define __atomic_exchange_n(p,v,m) exchange(p,v)
static int exchange(int*p,int v){int old=*p;*p=v;return old;}
static int g_s26SnapPending,g_s26CutsceneHandsHidden,g_h30NativeMouseDown,g_h5755chGrabStateActive,g_h5755chGrabButtonDetached,g_h30NativeUseHand,g_h42LookTailFrames,stateKind;
static int g_h5755ceNativeSwingDoorActive[2],g_h45NativeButtonReleased[2];
static unsigned g_h5747LookSampleActive=1,g_h5747LookWasNonzero,g_h5747LookRejects,g_h5747LookDispatches,g_h5747LookZeroFlushes,g_h16LookFrames;
static float g_h5747LookX,g_h5747NativeLookX,g_h5747RawLookX,g_h5747RawLookY,g_h5747LastYawStep,g_h5747MaxYawStep;
static int g_h5747LookAnalogId=1,snaps;static char*g_h5729LastModuleName,*g_h5729LastClassName;static float yaw;
#define H5747_LOOK_GAIN 0.08f
static int s26n_dispatch_phi_controls(void){return 0;}static void s26n_dispatch_crouch(void){}
static int h5754h_pause_active(void){return 0;}static int p2_xr_on(void){return 1;}static int p2_xr_running(void){return 1;}
static int h5720_streq(const char*a,const char*b){return 1;}static int h5755fm_grab_gameplay_actions_allowed(void){return 1;}static int h576bo_terminal_event_gate(void){return 0;}
static void h5754h_script_method(const char*s){snaps++;}static int h5729_kind_names(const char*a,const char*b){return stateKind;}
static int h5755cj_hand_matches_grab_owner(int h){return 1;}static int h5747_resolve_look_analog_id(void){return 1;}
static void*h34_player_input_interface(void){return (void*)1;}static float p2_player_yaw(void){return yaw;}
static void analog(void*p,int id,float*a){assert(a[1]==0);yaw-=a[0];}
static void(*p_h34PlayerAnalog)(void*,int,float*)=analog;static void(*o_h37aGlobalPlayerAnalog)(void*,int,float*)=analog;
static void ext_Log(const char*f,...){}
'''
tail=r'''
int main(void){
 for(int hz=60;hz<=120;hz+=60)for(int state=0;state<3;state++){
  g_s26gdRateMultiplier=hz/60;yaw=0;g_h5747LookX=.04f;g_h30NativeMouseDown=state!=0;
  stateKind=state==2?6:7;g_h5755chGrabStateActive=g_h5755chGrabButtonDetached=1;
  g_h5755ceNativeSwingDoorActive[0]=g_h45NativeButtonReleased[0]=1;
  for(int i=0;i<hz;i++)h5747_dispatch_native_look();
  assert(fabs(yaw+2.4f)<.00001f);
  g_s26SnapPending=1;g_h5747LookX=0;int before=snaps;h5747_dispatch_native_look();h5747_dispatch_native_look();assert(snaps==before+1);
 }
 puts("PASS: production smooth-look dispatch has equal rotation per second at 60/120, free/held/door routes; snap remains one discrete action");
}
'''
p=A/'test.c';p.write_text(head+(R/'source/simulation_rate_gd.h').read_text()+fun('h5747_dispatch_native_look')+tail)
subprocess.run([sys.argv[1],'cc',str(p),'-O2','-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(r.stdout,r.stderr);assert r.returncode==0
# Guard the other per-tick look producer, without reducing movement-axis amplitudes.
assert 'float packet[4]={s26gd_tick_amount(x),s26gd_tick_amount(y),0,0}' in s
(A/'result.json').write_text(json.dumps({'pass':True,'output':r.stdout,'phi_scope':'source guard for both angular axes'},indent=2))
