from pathlib import Path
import subprocess, sys, json
r=Path(__file__).resolve().parents[1]
pre=r'''
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;
static u64 got[4];
static void ext_Log(const char*f,...){va_list a;va_start(a,f);if(strstr(f,"members %"))for(int i=0;i<4;i++)got[i]=va_arg(a,u64);va_end(a);}
#define ext_malloc malloc
#define ext_free free
#define zero_bytes(p,n) memset(p,0,n)
#define C(x) do{if(!(x))return __LINE__;}while(0)
'''
post=r'''
int main(){
 u64 world[128]={0},manager[128]={0},mesh[128]={0},sub[128]={0},mat[128]={0},entries[8]={0};
 void*head[3]={0},*head2[3]={0},*node[3]={0},*subs[1]={sub};
 head[0]=node;head[1]=node;node[0]=head;node[1]=head;node[2]=mesh;head2[0]=head2;head2[1]=head2;
 *(void**)((u8*)world+0x180)=manager;*(void**)((u8*)world+0x310)=head;*(u64*)((u8*)world+0x318)=1;
 *(void**)((u8*)world+0x328)=head2;
 *(void**)((u8*)mesh+0x1f0)=subs;*(void**)((u8*)mesh+0x1f8)=subs+1;
 *(void**)((u8*)sub+0x1c0)=mat;
 u64*s=(u64*)((u8*)manager+0x118);s[9]=8;s[11]=(u64)entries;
 entries[2]=(u64)sub;cpu29_membership(world);C(got[0]==1&&got[1]==1&&!got[2]&&!got[3]);
 entries[2]=0;cpu29_membership(world);C(got[1]==1&&got[2]==1);
 entries[2]=123;s[6]=123;s[7]=1;cpu29_membership(world);C(!got[0]&&got[2]==1);
 ((u8*)mat)[0x174]=1;cpu29_membership(world);C(!got[1]&&!got[2]);
 ((u8*)mat)[0x174]=0;entries[2]=(u64)sub;
 *(void**)((u8*)world+0x310)=head2;*(u64*)((u8*)world+0x318)=0;
 *(void**)((u8*)world+0x328)=head;*(u64*)((u8*)world+0x330)=1;
 cpu29_membership(world);C(got[1]==1&&!got[2]&&!got[3]);
 puts("PASS membership oracle detects absent/deleted meshes and covers both lists; mock only");return 0;
}
'''
b=r/'build/cpu29-unit';b.mkdir(exist_ok=True)
code=(r/'tests/cpu29_membership.inc').read_text().split('static void __attribute__((ms_abi)) cpu29_compile')[0]
(b/'test.c').write_text(pre+code+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
p=subprocess.run([str(b/'test.exe')],capture_output=True,text=True)
print(p.stdout+p.stderr)
(r/'audit/cpu29-unit.json').write_text(json.dumps({'scope':'compiled oracle mock, not native membership proof','exit':p.returncode,'output':p.stdout+p.stderr},indent=2))
raise SystemExit(p.returncode)
