from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu24-unit';b.mkdir(exist_ok=True)
s=(r/'tests/cpu24_pack.inc').read_text()
pre="""#include <stdlib.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x)){printf("FAIL line %d\\n",__LINE__);exit(1);}}while(0)
"""
post=r'''
int main(){u8 sources[16][4096],out[65540],ref[65540];CPU24Attr a[16];unsigned seed=7;
for(int test=0;test<512;test++){u32 n=1+test%16;u64 vertices=1+(test*17)%200,stride=0;
for(u32 i=0;i<n;i++){seed=seed*1664525+1013904223;u32 scalar=(seed&1)?1:4;u32 width=(1+(seed>>4)%4)*scalar;for(int k=0;k<4096;k++)sources[i][k]=(u8)(k*13+i*71+test);a[i]=(CPU24Attr){sources[i]+1,vertices*width,width};stride+=width;}
u64 size=vertices*stride;memset(out,0xA5,sizeof(out));memset(ref,0xA5,sizeof(ref));
u64 offset=0;for(u32 i=0;i<n;i++){for(u64 v=0;v<vertices;v++)memcpy(ref+2+v*stride+offset,a[i].src+v*a[i].width,a[i].width);offset+=a[i].width;}
C(cpu24_pack(out+2,size,a,n));C(memcmp(out,ref,sizeof(out))==0);
memset(out,0xA5,sizeof(out));memset(ref,0xA5,sizeof(ref));C(!cpu24_pack(out+2,size-1,a,n));C(memcmp(out,ref,sizeof(out))==0);
a[0].src=0;C(!cpu24_pack(out+2,size,a,n));C(memcmp(out,ref,sizeof(out))==0);}
puts("PASS 512 mixed-width, unaligned byte-parity/guard cases and 1024 invalid-layout no-write cases");}
'''
(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu24-unit.json').write_text(json.dumps(dict(scope='Compiled byte parity against attribute-major reference, not native graphics proof',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));raise SystemExit(x.returncode)
