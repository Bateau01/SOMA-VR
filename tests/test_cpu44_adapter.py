"""Actual Windows module hashing and mocked adapter boundaries, not gameplay."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu44-adapter';b.mkdir(exist_ok=True)
s=r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define ext_GetProcAddress GetProcAddress
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_malloc malloc
#define ext_free free
#define ext_Log(...) ((void)0)
static int hookCalls,failCreate,failEnable;
static int ext_MH_CreateHook(void*a,void*b,void**c){hookCalls++;*c=a;return failCreate;}
static int ext_MH_EnableHook(void*a){return failEnable;}
static void*g_h34HandNewton[2];
#define CPU_HAND_MESH 1
#include "cpu_hand_mesh.inc"
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
static int calls,activeSeen,nest;static void original(void*p){calls++;activeSeen=c43Active;if(nest){nest=0;c44_job(p);}}
int main(int argc,char**argv){
 HMODULE m=LoadLibraryA(argv[1]),k=GetModuleHandleA("kernel32.dll");C(m&&k);C(c44_verify(m,k)==(argc<3));
 if(argc>=3){c44_install(m);C(!c44Ready&&hookCalls==0);puts("PASS mismatched module rejected before hooks");return 0;}
 c44_install(m);C(c44Ready&&hookCalls==2);c44Execute=original;
 C44Job j={0};j.stride=1;j.mode=1;j.world=(void*)123;
 c44_job(&j);C(calls==1&&!activeSeen); /* Outside Newton scope. */
 u32 entered=c44_enter(j.world,1);C(entered&&c44Depth==1);
 c44_job(&j);C(calls==2&&activeSeen&&!c43Active);
 j.world=(void*)456;c44_job(&j);C(calls==3&&!activeSeen);j.world=(void*)123;
 j.stride=2;c44_job(&j);C(calls==4&&!activeSeen);j.stride=1;
 j.mode=0;c44_job(&j);C(calls==5&&!activeSeen);j.mode=1;
 u32 nested=c44_enter(j.world,1);c44_job(&j);C(calls==6&&!activeSeen);c44_leave(nested);C(c44Depth==1);
 nest=1;c44_job(&j);C(calls==8&&!c43Active);
 c44_leave(entered);C(!c44Depth&&!c44World&&!c43Active);
 entered=c44_enter(j.world,0);c44_job(&j);C(!activeSeen);c44_leave(entered);
 puts("PASS actual module hash; scope/world/mode/worker/nesting/cleanup boundaries");return 0;
}
'''
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2','-I',str(r/'source'),str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
nd=Path('D:/SteamLibrary/steamapps/common/SOMA/Newton.dll')
bad=b/'Newton-modified.dll';bad.write_bytes(nd.read_bytes()+b'changed')
results=[]
for args in ([str(nd)],[str(bad),'mismatch']):
 x=subprocess.run([str(b/'test.exe'),*args],capture_output=True,text=True,timeout=30);results.append(dict(args=args,exit=x.returncode,output=x.stdout+x.stderr))
(r/'audit/cpu44-adapter.json').write_text(json.dumps(dict(scope=__doc__,results=results,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(json.dumps(results,indent=2));assert all(x['exit']==0 for x in results)
