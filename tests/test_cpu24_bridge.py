from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];s='static u32 cpu23Scope'+(r/'tests/cpu23_buffers.inc').read_text().split('static u32 cpu23Scope')[1].split('static void cpu23_install(void){')[0]
pre=r'''
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define CPU23_STAGING 0
#define CPU24_PACK 1
static void*cpu24Object,*cpu24Expected;
static unsigned cpu23Eligible;
static int failalloc;
static void* testalloc(size_t n){return failalloc?0:malloc(n);}
#define ext_malloc testalloc
#define ext_free free
typedef unsigned char u8;typedef long long i64;typedef int i32;typedef unsigned u32;typedef unsigned long long u64;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static int enabled=1,calls,events;static u64 clockv=1,cpuFreq=1000000;static u32 g_frameCounter;
static u64 cpu_detail_begin(void){return enabled?clockv++:0;}
static int clockfn(u64*p){*p=clockv++;return 1;}static int(*cpuCounter)(u64*)=clockfn;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 i){C((k==29||k==30||k==31)&&d<4&&b>=a);events++;}
static int h5748n_copy_tstring(void*p,char*q,u32 n){q[0]=0;return 0;}
#define ext_Log(...) ((void)0)
'''
post=r'''
static unsigned char object[256],mapped[65536],expected[65536];static int failmap;
static void cpu24_verify_gpu(u32 target,u8 ok){C(target==0x8892&&ok==1);}
static i32 cpu24_native_pack(void*d,u64 n){if(!((u8*)cpu24Object)[0xed])return 0;C(d==mapped&&n==65536);memcpy(d,expected,n);return 1;}
static void* __attribute__((ms_abi)) copy(void*a,const void*b,u64 n){return memcpy(a,b,n);}
static void* __attribute__((ms_abi)) map(u32 a,u32 b){C(a==0x8892&&b==0x88b9);calls++;return failmap?0:mapped;}
static u8 __attribute__((ms_abi)) unmap(u32 a){C(a==0x8892);calls++;return 1;}
static void __attribute__((ms_abi)) data(u32 a,i64 n,const void*p,u32 usage){C(a==0x8892&&n==65536&&p==0&&usage==0x88e4);calls++;}
static void __attribute__((ms_abi)) upload(void*p){C(p==object);cpu23_data(0x8892,65536,0,0x88e4);unsigned char*q=cpu23_map(0x8892,0x88b9);
C((q==0)==(failmap||(enabled&&cpu23Eligible&&object[0xed])));if(q){C(q==mapped);for(int a=0;a<4;a++)for(int i=a;i<65536;i+=4)q[i]=expected[i];}
C(cpu23_unmap(0x8892)==1);calls++;}
int main(){cpu23MapOriginal=map;cpu23UnmapOriginal=unmap;cpu23DataOriginal=data;cpu23UploadOriginal=upload;cpu23Copy=copy;
for(int i=0;i<65536;i++)expected[i]=(unsigned char)(i*17+3);
for(int x=0;x<2;x++)for(int e=0;e<2;e++)for(int v=0;v<2;v++)for(int f=0;f<2;f++){failalloc=0;enabled=x;cpu23Eligible=e;cpu24Expected=e?object:0;object[0xed]=v;failmap=f;memset(mapped,0,65536);cpu23_upload(object);C(cpu23Scope==0&&cpu23Scratch==0&&cpu23Mapped==0&&cpu24Object==0);if(!f)C(memcmp(mapped,expected,65536)==0);}
C(calls==64);puts("PASS bridge 16 cases: completed-copy skip versus native-copy byte parity, interleaved/planar, eligible/ineligible, observer on/off, failed map, exact forwarding and resource cleanup");}
'''
b=r/'build/cpu24-bridge';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu24-bridge.json').write_text(json.dumps(dict(scope='Compiled Windows x64 ABI forwarding mock, not native gameplay proof',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256((r/'tests/cpu23_buffers.inc').read_bytes()).hexdigest()),indent=2))
raise SystemExit(x.returncode)
