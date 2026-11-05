"""Guard/lifetime contract tests, synthetic structures; not gameplay certification."""
from pathlib import Path
import subprocess,json,sys
r=Path(__file__).resolve().parents[1];b=r/'build/cpu56-guards';b.mkdir(parents=True,exist_ok=True)
core='#define CPU_LEAF_FILTER 1\n'+(r/'source/cpu_leaf_filter.inc').read_text().split('/* Redirect only')[0]+'\n#endif\n'
s=r'''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <assert.h>
typedef unsigned char u8;typedef unsigned u32;typedef uint64_t u64;
static int owner=1;static u32 c43Epoch=1,c43Active=1;
#define C43_MAIN() (owner)
#define cpu14_event(a,b,c,d,e) ((void)0)
static u64 c44_now(void){return 1;}
static void c43_copy(void*d,const void*s,unsigned n){memcpy(d,s,n);}
static int c43_equal(const void*a,const void*b,unsigned n){return !memcmp(a,b,n);}
static int h9_good(float v,float l){return isfinite(v)&&fabsf(v)<=l;}
'''+core+r'''
static unsigned expectedDepth,pairCalls,leafCalls;
static int pair(void*a,void*b,void*c,int d){assert(c56Depth==expectedDepth);pairCalls++;return 19;}
static int leaf(void*w,void*p){leafCalls++;return 23;}
static unsigned motionCalls;
static void motion(const void*b,float dt,float*v,float*o){motionCalls++;for(int i=0;i<4;i++){v[i]=dt;o[i]=2*dt;}}
static void com(const void*b,float*v){for(int i=0;i<4;i++)v[i]=0;}
int main(void){
 c56Pair=pair;c56Leaf=leaf;c56Ready=1;
 // Foreign thread and inactive job must not dereference even a poison proxy.
 owner=0;assert(c56_pair(0,(void*)1,0,0)==19);assert(c56_leaf(0,(void*)1)==23);
 owner=1;c43Active=0;assert(c56_pair(0,(void*)1,0,0)==19);assert(c56_leaf(0,(void*)1)==23);c43Active=1;
 u8 proxy[256]={0},material[256]={0};*(void**)(proxy+0x18)=material;
 expectedDepth=1;assert(c56_pair(0,proxy,0,0)==19);assert(!c56Depth);
 expectedDepth=0;*(void**)(material+0xb8)=(void*)1;assert(c56_pair(0,proxy,0,0)==19);assert(!c56Depth);
 *(void**)(proxy+0x18)=0;assert(c56_pair(0,proxy,0,0)==19);
 expectedDepth=c56Depth=1;assert(c56_pair(0,(void*)1,0,0)==19);c56Depth=0;
 // Immutable bounds refresh on a new job, including epoch wrap/address reuse.
 u8 shape[512]={0};void*vt[8]={0};*(void***)shape=vt;c56Module=0x100000;
 vt[4]=(void*)(uintptr_t)(c56Module+0x6e470);*(u32*)(shape+0x68)=0;
 float*extent=(float*)(shape+0x140);extent[0]=1;extent[1]=2;extent[2]=3;float lo[3],hi[3];
 assert(c56_bound(shape,lo,hi)&&hi[0]==1&&lo[2]==-3);
 c43Epoch=2;extent[0]=4;assert(c56_bound(shape,lo,hi)&&hi[0]==4);
 c43Epoch=0xffffffffu;assert(c56_bound(shape,lo,hi));c43Epoch=1;extent[0]=5;assert(c56_bound(shape,lo,hi)&&hi[0]==5);
 c43Epoch++;vt[4]=(void*)1;assert(!c56_bound(shape,lo,hi));
 c43Epoch++;vt[4]=(void*)(uintptr_t)(c56Module+0x6e470);*(u32*)(shape+0x68)=5;assert(!c56_bound(shape,lo,hi));
 c43Epoch++;*(u32*)(shape+0x68)=0;extent[0]=NAN;assert(!c56_bound(shape,lo,hi));
 assert(pairCalls==6&&leafCalls==2);c56Motion=motion;c56Com=com;c56MotionCount=0;float v[4],o[4],c[4];c56_motion((void*)1,.1f,v,o,c);c56_motion((void*)1,.1f,v,o,c);assert(motionCalls==1&&v[0]==.1f&&o[0]==.2f);c56_motion((void*)2,.1f,v,o,c);c56_motion((void*)3,.1f,v,o,c);assert(motionCalls==3);c56Depth=0;expectedDepth=1;*(void**)(proxy+0x18)=material;*(void**)(material+0xb8)=0;c56_pair(0,proxy,0,0);assert(!c56MotionCount);puts("PASS owner, inactive, callback, nested, missing material, unsupported, epoch and address reuse guards");
}
'''
(b/'test.c').write_text(s);zig=Path(sys.argv[1]) if len(sys.argv)>1 else r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);(r/'audit/cpu56-guards.json').write_text(json.dumps(dict(exit=x.returncode,output=x.stdout+x.stderr),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
