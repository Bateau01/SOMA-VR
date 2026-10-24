"""Compiled production branch replay; no native engine/controller proof."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('    // S26IO: exact Lever ownership');b=s.index('    if(!p_h14AddImpulse)return;',a)
old=(R/'tests/fixtures/in_baseline/lever_dispatch.c').read_text()
head=r"""#include <stdio.h>
static int g_h482ArticulatedValid[2],g_h30NativeMouseDown,g_h30NativeUseHand,g_h5755ceSwingDoorPendingNative[2],g_h5755gcLeverJointedBridgeCalls[2],g_h5755gcLeverJointedBridgeLogs[2],g_h5755gbLeverLegacyImpulseSuppress[2];
static const char *g_h5729LastModuleName,*g_h5729LastClassName;
static int exact,packets,fallback;
#define ext_Log(...) ((void)0)
#define h5755fn_exact_lever_names(a,b) exact
static int h5755gb_drive_authored_lever(int h,const float*v,float dt){packets++;return 1;}
"""
for name,code in [('before',old),('after',s[a:b])]:head+='void '+name+'(int hand,float*handV,float dt){'+code+'fallback++;}\n'
head+=r"""int main(){int checks=0;float v[3]={1,0,0};
#define C(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
exact=1;g_h482ArticulatedValid[0]=1;g_h30NativeMouseDown=1;g_h30NativeUseHand=0;before(0,v,1.0f/120);C(packets==0);after(0,v,1.0f/120);C(packets==1);
for(int hz=60;hz<=120;hz+=60)for(int e=0;e<2;e++)for(int graph=0;graph<2;graph++)for(int down=0;down<2;down++)for(int owner=0;owner<2;owner++)for(int hand=0;hand<2;hand++){
exact=e;g_h482ArticulatedValid[hand]=graph;g_h30NativeMouseDown=down;g_h30NativeUseHand=owner;
packets=fallback=0;after(hand,v,1.0f/hz);C(packets==(e&&down&&owner==hand));C(fallback==(!e&&!(graph&&down&&owner==hand)));
if(!e||!graph){int p=packets,f=fallback;packets=fallback=0;before(hand,v,1.0f/hz);C(p==packets&&f==fallback);}}
printf("PASS %d assertions; graph-owned exact Lever blocked before, forwarded after; other routing and initiating hand preserved\n",checks);}
"""
p=R/'build/lever_dispatch_io.c';p.write_text(head);exe=p.with_suffix('.exe');subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
