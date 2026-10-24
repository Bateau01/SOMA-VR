"""Source-equivalence and compiled bounded logger tests; mocked driver, no engine claim."""
from pathlib import Path
import re,subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('static i32 s26ip_lever_impl(');b=s.index('\n}',a)+2;body=s[a:b].replace('s26ip_lever_impl(','h5755gb_drive_authored_lever(',1)
body=re.sub(r'    // S26IP_DIAG_BEGIN.*?    // S26IP_DIAG_END\n','',body,flags=re.S);body=re.sub(r'    g_s26ipLever\[hand\]\.stage=\d;\n','',body)
assert body==(R/'tests/fixtures/in_baseline/lever_impl_io.c').read_text()
h=(R/'runtime/script/player/PlayerState_Interact_RotateBase.hps').read_text();h=re.sub(r'(?m)^ +// S26IP_DIAG_BEGIN\n.*?^ +// S26IP_DIAG_END\n','',h,flags=re.S|re.M);assert h==(R/'tests/fixtures/in_baseline/rotate_io.hps').read_text()
a=s.index('typedef struct {u32 lines,calls,packets,fresh,frame;');b=s.index('// S26IP_DIAG_END',a);data=s[a:b]
a=s.index('static i32 h5755gb_drive_authored_lever(i32 hand,const float* handVel,float dt){');b=s.index('\n}',a)+2;fn=s[a:b]
head=r"""#include <stdio.h>
#include <string.h>
typedef unsigned u32;typedef int i32;
static unsigned g_h5755gbLeverNativePackets[2],g_frameCounter,g_h14PhysicsSteps,g_s26gdRateMultiplier;
static int g_h482ArticulatedValid[2],g_h30NativeMouseDown,g_h30NativeUseHand,g_h37aAnalogGuardReady,g_h5755gbLeverNativeFailClosed[2],g_h576bdLeverScriptOK,logs,calls;
static void ext_Log(const char*f,...){logs++;}
static int s26ip_lever_impl(int h,const float*v,float dt){calls++;if(h>=0&&h<2)g_h5755gbLeverNativePackets[h]++;return 7;}
"""
main=r"""int main(){float v[3]={1,0,0};int checks=0;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
for(int hz=60;hz<=120;hz+=60){memset(g_s26ipLever,0,sizeof(g_s26ipLever));logs=calls=0;
for(int i=0;i<hz*100;i++){g_frameCounter=i;g_h14PhysicsSteps=i;for(int h=0;h<2;h++)C(h5755gb_drive_authored_lever(h,v,1.0f/hz)==7);}
C(logs==240);C(calls==hz*200);C(g_s26ipLever[0].lines==120&&g_s26ipLever[1].lines==120);}
C(h5755gb_drive_authored_lever(-1,v,.01f)==7);printf("PASS %d checks; bounded120 rows per hand; every original call and return retained\n",checks);}
"""
p=R/'build/lever_diag_ip.c';p.write_text(head+data+fn+main);subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(r.stdout);assert r.returncode==0
(R/'docs/v109-evidence/lever_diag_ip.json').write_text(json.dumps({'scope':__doc__,'source_equivalence':True,'exit':r.returncode,'output':r.stdout},indent=2))
