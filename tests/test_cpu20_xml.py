from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1]
s=(r/'tests/cpu20_xml.inc').read_text().split('static void cpu20_init')[0]
pre=r'''
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x)){printf("FAIL line %d\n",__LINE__);exit(1);}}while(0)
#define ext_Log(...) ((void)0)
static u64 ticks,cpuFreq=1000000;static u32 g_frameCounter=1,cpuMainThread=5,thread=5;
static u32 tid(void){return thread;}static u32(*cpuThreadId)(void)=tid;
static i32 clockfn(u64*p){*p=(ticks+=100);return 1;}static i32(*cpuCounter)(u64*)=clockfn;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 id){C(k==26&&b>=a);}
'''
post=r'''
typedef struct O{void**vt;u8 pad[0x40];void**head;u64 count;int id;}O;
static int allocations,frees,destroyed,order[2000];
static void*alloc(size_t n){allocations++;return calloc(1,n);}
static void __attribute__((ms_abi)) del(void*p){C(p);frees++;free(p);}
static void* __attribute__((ms_abi)) destroy(void*p,u32 flags){
 O*o=p;C(flags==1);void**h=o->head;void**n=h[0];
 while(n!=h){void**next=n[0];O*c=n[2];if(c)destroy(c,1);del(n);n=next;}
 order[destroyed++]=o->id;del(h);del(o);return p;
}
static void*vt[1]={(void*)destroy},*unknown[1]={(void*)destroy};
static O*make(int id){O*o=alloc(sizeof(*o));o->vt=vt;o->id=id;o->head=alloc(3*sizeof(void*));o->head[0]=o->head;o->head[1]=o->head;return o;}
static void add(O*p,O*c){void**h=p->head;void**last=h[1];void**n=alloc(3*sizeof(void*));n[0]=h;n[1]=last;n[2]=c;last[0]=n;h[1]=n;p->count++;}
static void finish(void){int guard=0;while(cpu20Count){cpu20_one();C(++guard<10000);}C(!cpu20Depth);}
static void* __attribute__((ms_abi)) shutdownfn(void*p,u32 flags){C(flags==7&&!cpu20Count&&cpu20ShuttingDown);return p;}
int main(){
 C(offsetof(O,head)==0x48&&offsetof(O,count)==0x50);
 cpu20Delete=del;cpu20ElementVT=vt;cpu20DocumentVT=vt;cpu20TextVT=vt;cpu20ShutdownOriginal=shutdownfn;
 O*r=make(0),*a=make(1);add(a,make(2));add(r,a);add(r,make(3));
 cpu20Eligible[0]=r;thread=6;C(!cpu20_retire(r,1));thread=5;C(!cpu20_retire(r,0));C(cpu20_retire(r,1));cpu20Eligible[0]=0;
 cpu20_one();C(!destroyed&&r->count==1);finish();C(destroyed==4&&order[0]==2&&order[1]==1&&order[2]==3&&order[3]==0);C(frees==allocations);
 for(int i=0;i<8;i++)C(cpu20_enqueue(make(10+i)));r=make(20);C(!cpu20_enqueue(r));destroy(r,1);finish();C(frees==allocations);
 r=make(30);r->vt=unknown;add(r,make(31));C(cpu20_enqueue(r));finish();C(cpu20Fallback==1&&frees==allocations);
 r=make(40);a=r;for(int i=0;i<300;i++){O*c=make(41+i);add(a,c);a=c;}C(cpu20_enqueue(r));finish();C(cpu20Fallback==2&&frees==allocations);
 r=make(500);for(int i=0;i<100;i++)add(r,make(501+i));C(cpu20_enqueue(r));cpu20_drain();C(cpu20Count&&cpu20Slices==1);u64 old=cpu20Nodes;cpu20_drain();C(cpu20Nodes==old);while(cpu20Count){g_frameCounter++;cpu20_drain();}C(frees==allocations);
 r=make(800);add(r,make(801));C(cpu20_enqueue(r));cpu20_one();cpu20ShutdownOriginal=shutdownfn;int token;C(cpu20_shutdown(&token,7)==&token);C(!cpu20Depth&&frees==allocations);C(!cpu20_retire(&token,1));
 puts("PASS native-style layout, ordered leaf ownership, exact frees, bounded queue, deep/unknown fallback, thread/flags rejection, per-frame budget, shutdown drain/forwarding");
}
'''
b=r/'build/cpu20-unit';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu20-unit.json').write_text(json.dumps(dict(scope='Compiled scheduler against synthetic XML layout, not native runtime proof',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256((r/'tests/cpu20_xml.inc').read_bytes()).hexdigest()),indent=2))
raise SystemExit(x.returncode)
