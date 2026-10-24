"""Standalone compiled regression: stale committed grab metadata, not gameplay validation."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text()
a=s.index('static void s26il_reconcile_grab_shell(');end=s.index('\nstatic void h5729_state_boundary_observe',a)
qa=s.index('static void h5755em_queue_native_grab_semantics_ex(i32 hand,const void* body,const void* semanticBody,const float* contact,i32 late){');qb=s.index('\nstatic void h5755ch_queue_native_grab_semantics(',qa)
head=r"""
#include <assert.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
struct Pending{int valid;u8 late;const void *body,*semanticBody;float contact[3];u32 queuedStep;};
typedef struct Pending H5755CHGrabPending;
static H5755CHGrabPending g_h5755chGrabPending[2];
static int g_h5755chGrabScriptOK=1,g_h30NativeMouseDown;
static u32 g_h5755chGrabSharedAttach[2],g_h5755cjGrabOwnerShares[2],g_h5755chGrabSecondaryDifferent[2],g_h5755chGrabFallback[2],g_h5755chGrabQueued[2],g_h14PhysicsSteps=100;
static int h5755cj_body_matches_grab_owner(const void*b){return b==(void*)1;}
#define ext_Log(...) ((void)0)
static int g_h5755chGrabStateActive,g_h5755chGrabExpected,g_h5755chGrabPrimaryHand,g_h5755chGrabButtonDetached;
static const void *g_h5755chGrabStateBody,*g_h5755chGrabStateWrapper,*g_h5755chGrabStateOwner;
static u32 g_h5755cjGrabExpectedStep;
static void *held[2]={(void*)111,(void*)222};static int nativeUse=1;
static int sameOwnerHeld[2];
static int h5755cj_hand_matches_grab_owner(int hand){return sameOwnerHeld[hand];}
static void seed(void){sameOwnerHeld[0]=sameOwnerHeld[1]=0;g_h5755chGrabStateActive=1;g_h5755chGrabExpected=0;g_h5755chGrabStateBody=(void*)1;g_h5755chGrabStateWrapper=(void*)2;g_h5755chGrabStateOwner=(void*)3;g_h5755chGrabPrimaryHand=0;g_h5755chGrabButtonDetached=1;g_h5755cjGrabExpectedStep=5;}
"""
tail=r"""
int main(void){
float contact[3]={1,2,3};
/* Actual queue code reproduces the failure: stale owner skips new item dispatch. */
seed();h5755em_queue_native_grab_semantics_ex(1,(void*)999,0,contact,0);assert(!g_h5755chGrabPending[1].valid&&g_h5755chGrabSecondaryDifferent[1]==1);
s26il_reconcile_grab_shell(4);h5755em_queue_native_grab_semantics_ex(1,(void*)999,0,contact,0);assert(g_h5755chGrabPending[1].valid&&g_h5755chGrabPending[1].body==(void*)999&&g_h5755chGrabPending[1].queuedStep==100);
g_h5755chGrabPending[1].valid=0;seed();s26il_reconcile_grab_shell(7);h5755em_queue_native_grab_semantics_ex(1,(void*)999,0,contact,0);assert(!g_h5755chGrabPending[1].valid);
/* An adopted Grab can enter and exit entirely between Normal polls. */
seed();assert(g_h5755chGrabStateActive);s26il_reconcile_grab_shell(4);
assert(!g_h5755chGrabStateActive&&!g_h5755chGrabStateBody&&!g_h5755chGrabStateOwner&&!g_h5755chGrabStateWrapper&&g_h5755chGrabPrimaryHand==-1&&!g_h5755chGrabButtonDetached&&!g_h5755cjGrabExpectedStep);
assert(held[0]==(void*)111&&held[1]==(void*)222&&nativeUse==1);
/* Mounted extraction keeps its detached-input/look lifetime while either hand
   really owns the same prop. Release must still recover the next item queue. */
for(int h=0;h<2;h++){seed();sameOwnerHeld[h]=1;s26il_reconcile_grab_shell(4);
assert(g_h5755chGrabStateActive&&g_h5755chGrabButtonDetached&&g_h5755chGrabStateOwner==(void*)3);
sameOwnerHeld[h]=0;s26il_reconcile_grab_shell(4);assert(!g_h5755chGrabStateActive);
g_h5755chGrabPending[1].valid=0;h5755em_queue_native_grab_semantics_ex(1,(void*)999,0,contact,0);assert(g_h5755chGrabPending[1].valid);}
seed();sameOwnerHeld[0]=1;s26il_reconcile_grab_shell(5);assert(!g_h5755chGrabStateActive); // a real terminal transition still wins
/* Active Grab and unresolved classifications cannot be retired. */
int keep[]={-1,0,7};for(int i=0;i<3;i++){seed();s26il_reconcile_grab_shell(keep[i]);assert(g_h5755chGrabStateActive&&g_h5755chGrabStateOwner==(void*)3);}
/* Pending native transition and inactive shell remain untouched. */
seed();g_h5755chGrabExpected=1;s26il_reconcile_grab_shell(4);assert(g_h5755chGrabExpected&&g_h5755chGrabStateActive);
seed();g_h5755chGrabStateActive=0;s26il_reconcile_grab_shell(4);assert(g_h5755chGrabStateOwner==(void*)3);
/* Another known mechanism must not keep an old owner, nor lose input. */
for(int k=1;k<=6;k++){seed();s26il_reconcile_grab_shell(k);assert(!g_h5755chGrabStateActive&&nativeUse==1&&held[1]==(void*)222);}
return 0;
}
"""
b=r/'build/il-probe';c=b/'grab_lifetime_test.c';c.write_text(head+s[a:end]+s[qa:qb]+tail)
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(b/'grab_lifetime_test.exe')],check=True)
subprocess.run([str(b/'grab_lifetime_test.exe')],check=True)
print('PASS: compiled metadata regression; live/pending/unknown guards and independent ownership preserved. Not an in-game pass.')

