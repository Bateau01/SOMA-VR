from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];s=(r/'tests/cpu21_entities.inc').read_text().split('static void cpu21_install')[0]
pre=r'''
#include <stdlib.h>
#include <stdio.h>
typedef int i32;typedef unsigned u32;typedef unsigned long long u64;
#define C(x) do{if(!(x))exit(__LINE__);}while(0)
static int enabled=1,calls,events;static u64 clockv=1,cpuFreq=1000000;static u32 g_frameCounter;
static u64 cpu_detail_begin(void){return enabled?clockv++:0;}
static int clockfn(u64*p){*p=clockv++;return 1;}static int(*cpuCounter)(u64*)=clockfn;
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 i){C(k==27&&d<3&&b>=a);events++;}
static int h5748n_copy_tstring(void*p,char*q,u32 n){q[0]=0;return 0;}
#define ext_Log(...) ((void)0)
'''
post=r'''
static u64 seed=0x123456789abcdef0ULL;
static void __attribute__((ms_abi)) entity(u64 a,u64 b,u64 c,u64 d,u64 e,u64 f,u64 g,u64 h,u64 i,u64 j,u64 k){
 u64 v[]={a,b,c,d,e,f,g,h,i,j,k};for(int n=0;n<11;n++)C(v[n]==seed+n);calls++;
}
static void __attribute__((ms_abi)) area(u64 a,u64 b,u64 c,u64 d,u64 e,u64 f,u64 g,u64 h,u64 i,u64 j){
 u64 v[]={a,b,c,d,e,f,g,h,i,j};for(int n=0;n<10;n++)C(v[n]==seed+n);calls++;
}
static u64 __attribute__((ms_abi)) convert(u64 p){C(p==seed);calls++;return seed+99;}
int main(){cpu21EntityOriginal=entity;cpu21AreaOriginal=area;cpu21ConvertOriginal=convert;
 for(int x=0;x<2;x++){enabled=x;cpu21_entity(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,seed+8,seed+9,seed+10);cpu21_area(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,seed+8,seed+9);}
 C(calls==4&&events==2);for(int x=0;x<2;x++){enabled=x;C(cpu21_convert(seed)==seed+99);}C(calls==6&&events==3);puts("PASS 10/11 register and stack arguments plus converter return forwarded exactly with observation on/off");
}
'''
b=r/'build/cpu21-unit';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu21-unit.json').write_text(json.dumps(dict(scope='Compiled Windows x64 ABI forwarding mock, not native gameplay proof',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256((r/'tests/cpu21_entities.inc').read_bytes()).hexdigest()),indent=2))
raise SystemExit(x.returncode)
