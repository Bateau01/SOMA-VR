"""Compile the combined release core with mock native calls and owned allocations."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'source/cpu_streaming.inc'
core=p.read_text().split('static i32 s29_signature')[0]
core=core.replace('((u64(__attribute__((ms_abi))*)(void*))(s29Base+0x581e00))(a)','mock_count(a)').replace('((const u8*(__attribute__((ms_abi))*)(void*))(s29Base+0x581dc0))(a)','mock_data(a)')
pre=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef long long i64;typedef int i32;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
static void*ctx=(void*)123;
static u32 g_frameCounter=1,thread=1;static u64 ticks;
static u32 __attribute__((ms_abi)) tid(void){return thread;}
static void*__attribute__((ms_abi)) context(void){return ctx;}
static i32 __attribute__((ms_abi)) clockfn(u64*p){*p=(ticks+=100);return 1;}
static u64 mock_count(void*p){return *(u64*)((u8*)p+16);}
static const u8*mock_data(void*p){return *(void**)((u8*)p+24);}
'''
post=r'''
typedef struct O{void**vt;u8 pad[0x40];void**head;u64 count;}O;
static int allocated,freed,destroyed,updates,shutdowns;
static void*alloc(size_t n){allocated++;return calloc(1,n);}
static void __attribute__((ms_abi)) del(void*p){C(p);freed++;free(p);}
static void*__attribute__((ms_abi)) destroy(void*p,u32 flags){C(flags==1);O*o=p;void**h=o->head;void**n=h[0];while(n!=h){void**next=n[0];if(n[2])destroy(n[2],1);del(n);n=next;}destroyed++;del(h);del(p);return p;}
static O*make(void){O*o=alloc(sizeof(O));o->vt=(void**)(s29Base+0x6d4be8);o->head=alloc(3*sizeof(void*));o->head[0]=o->head;o->head[1]=o->head;return o;}
static void add(O*p,O*c){void**h=p->head,**last=h[1],**n=alloc(3*sizeof(void*));n[0]=h;n[1]=last;n[2]=c;last[0]=n;h[1]=n;p->count++;}
static void __attribute__((ms_abi)) update(void*p,u64 a,u64 b){C(a==17&&b==29);updates++;void*x=*(void**)((u8*)p+0xa8);C(s29_xml(x,1)==x);*(void**)((u8*)p+0xa8)=0;}
static void*__attribute__((ms_abi)) shutdownfn(void*p,u32 flags){C(flags==7&&!s29Count&&!s29Depth);shutdowns++;return p;}
static u8 mapped[65536];static int mapfails,mapcalls,datacalls;
static void*__attribute__((ms_abi)) mapfn(u32 target,u32 access){mapcalls++;return mapfails?0:mapped;}
static void __attribute__((ms_abi)) datafn(u32 target,i64 bytes,const void*data,u32 usage){datacalls++;}
int main(){
 s29Base=calloc(1,0x700000);C(s29Base);*(void**)(s29Base+0x6d4be8)=(void*)destroy;
 s29Ready=1;s29Main=1;s29Thread=tid;s29Context=context;s29GL=(void*)123;s29Clock=clockfn;s29Freq=1000000;
 s29Delete=del;s29XmlOriginal=destroy;s29UpdateOriginal=update;s29ShutdownOriginal=shutdownfn;
 C(offsetof(O,head)==0x48);u64 loader[128]={0};*(u32*)((u8*)loader+0x54)=26;
 O*root=make();for(int i=0;i<100;i++)add(root,make());*(void**)((u8*)loader+0xa8)=root;
 s29_update(loader,17,29);C(updates==1&&!destroyed&&s29Count==1&&!s29Eligible[0]);
 s29_drain();C(s29Count);u32 depth=s29Depth;s29_drain();C(s29Depth==depth);
 while(s29Count){g_frameCounter++;s29_drain();}C(allocated==freed&&destroyed==101);
 root=make();*(void**)((u8*)loader+0xa8)=root;thread=2;s29_update(loader,17,29);C(!s29Count&&destroyed==102);thread=1;
 root=make();add(root,make());*(void**)((u8*)loader+0xa8)=root;s29_update(loader,17,29);int token;C(s29_shutdown(&token,7)==&token&&shutdowns==1&&allocated==freed);
 u8 object[256]={0},attribute[32]={0},src[64],out[68],before[68];void*attrs[]={attribute};
 for(int i=0;i<64;i++)src[i]=(u8)(i*17+3);*(u32*)(attribute+8)=2;*(u32*)(attribute+12)=4;*(u64*)(attribute+16)=64;*(void**)(attribute+24)=src;
 object[0xed]=1;*(void**)(object+0x88)=attrs;*(void**)(object+0x90)=attrs+1;s29Object=object;
 memset(out,0xa5,sizeof(out));C(s29_pack(out+1,64));C(!memcmp(out+1,src,64)&&out[0]==0xa5&&out[65]==0xa5);
 memcpy(before,out,sizeof(out));*(u64*)(attribute+16)=63;C(!s29_pack(out+1,64)&&!memcmp(before,out,sizeof(out)));
 s29MapOriginal=mapfn;s29DataOriginal=datafn;
 u8*large=malloc(sizeof(mapped));memset(large,0x73,sizeof(mapped));*(u64*)(attribute+16)=65536;*(void**)(attribute+24)=large;
 s29Expected=object;s29Object=object;s29UploadDepth=1;
 s29_data(0x8892,65536,0,0);C(datacalls==1&&s29Bytes==65536);
 memset(mapped,0xa5,sizeof(mapped));C(!s29_map(0x8892,0x88b9)&&!memcmp(mapped,large,sizeof(mapped)));
 for(int mode=0;mode<7;mode++){
  memset(mapped,0xa5,sizeof(mapped));s29Ready=1;thread=1;ctx=(void*)123;s29UploadDepth=1;s29Expected=object;s29Bytes=65536;mapfails=0;
  if(mode==0)s29Ready=0;if(mode==1)thread=2;if(mode==2)ctx=(void*)456;if(mode==3)s29UploadDepth=2;if(mode==4)s29Expected=0;if(mode==5)s29Bytes=65535;if(mode==6)mapfails=1;
  C(s29_map(0x8892,0x88b9)==(mapfails?0:mapped));for(int i=0;i<65536;i++)C(mapped[i]==0xa5);
 }
 C(mapcalls==8);free(large);
 free(s29Base);puts("PASS combined release core: owned XML exact frees, scoped loader forwarding, wrong-thread native fallback, budget, shutdown packing no-write rejection and exact release GL wrapper readiness/thread/context/nesting/identity/size/map-failure fallbacks; mock only");
}
'''
b=r/'build/cpu29-release-core';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+core+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu29-release-core.json').write_text(json.dumps({'scope':'combined release core against mock native calls; not gameplay proof','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exit':x.returncode,'output':x.stdout+x.stderr},indent=2))
raise SystemExit(x.returncode)
