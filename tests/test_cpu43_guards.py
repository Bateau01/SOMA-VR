"""Compiled core boundary tests with simulated native calls; no game proof."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];b=r/'build/cpu43-guards';b.mkdir(exist_ok=True)
s=r'''
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
static unsigned mainThread=1,target=1,calls,positive;static unsigned long long clockValue,clockStep=100;
static unsigned long long tick(void){clockValue+=clockStep;return clockValue;}
#define C43_MAIN() mainThread
#define C43_TARGET(a,b) target
#define C43_NOW() tick()
#define C43_MIN_TICKS 50u
#define C43_SHADOW 0
'''+(r/'tests/cpu43_reuse.inc').read_text()+r'''
static unsigned char ba[0x208],bb[0x208],sa[0x100],sb[0x100],mat[0xa0],pair[48];
static void native(void*w,void*p,float dt,int thread){calls++;*(unsigned*)((char*)p+40)=positive;}
static void setup(void){memset(ba,0,sizeof(ba));memset(bb,0,sizeof(bb));memset(sa,0,sizeof(sa));memset(sb,0,sizeof(sb));memset(mat,0,sizeof(mat));memset(pair,0,sizeof(pair));*(void**)(ba+0x200)=sa;*(void**)(bb+0x200)=sb;*(unsigned*)(sa+0x68)=5;*(unsigned*)(sb+0x68)=9;*(void**)pair=ba;*(void**)(pair+8)=bb;*(void**)(pair+24)=mat;c43Kernel=native;calls=0;positive=0;target=mainThread=1;clockStep=100;c43_begin(1);}
static void run(void){c43_pair(0,pair,1.f/120,0);}
int main(void){
 setup();run();run();C(calls==1&&c43Hits==1);
 c43_begin(1);run();C(calls==2); /* No reuse across steps/worlds. */
 setup();run();ba[0x40]++;run();C(calls==2);
 setup();run();bb[0x1ec]++;run();C(calls==2);
 setup();run();mat[0x94]++;run();C(calls==2);
 setup();run();pair[44]++;run();C(calls==2);
 setup();positive=1;run();run();C(calls==2&&c43Hits==0);
 setup();*(void**)(sb+0x98)=(void*)1;run();run();C(calls==2&&c43Eligible==0);
 setup();*(unsigned*)(sb+0x68)=2;run();run();C(calls==2&&c43Eligible==0);
 setup();*(void**)(pair+16)=(void*)1;run();run();C(calls==2&&c43Eligible==0);
 setup();target=0;run();run();C(calls==2&&c43Eligible==0);
 setup();mainThread=0;run();run();C(calls==2&&c43Eligible==0);
 setup();c43_pair(0,pair,1.f/120,1);c43_pair(0,pair,1.f/120,1);C(calls==2&&c43Eligible==0);
 setup();c43_begin(0);run();run();C(calls==2&&c43Eligible==0);
 setup();clockStep=1;run();run();C(calls==2&&c43Hits==0);
 setup();run();c43Epoch=~0u;c43_begin(1);run();C(calls==2&&c43Epoch==1);
 /* Native scratch address differs per pair; it must remain the new address. */
 setup();*(void**)(pair+32)=(void*)0x1234;run();*(void**)(pair+32)=(void*)0x5678;run();C(calls==1&&*(void**)(pair+32)==(void*)0x5678);
 puts("PASS 17 boundary cases");return 0;
}
'''
(b/'test.c').write_text(s);subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=15)
(r/'audit/cpu43-guards.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
