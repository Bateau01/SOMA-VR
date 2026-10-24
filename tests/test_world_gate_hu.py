"""Production fingertip entry branch, mocked state/ownership; not a tracked-controller test."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];base=r.parent.parent/'SOMA_VR_109_S26HT/repo';results={}
head=r'''
#include <cstdio>
using i32=int;using u32=unsigned;
int terminal;unsigned g_s26huWorldControlAllowed;void*g_h14GripBody[2];int g_h30NativeMouseDown,g_h30NativeUseHand;int g_h5755gjPokeNativeUse[2];
int h5730_exact_terminal_state(int,int,int,int){return terminal;}
'''
for label,root in [('baseline',base),('candidate',r)]:
 s=(root/'source/s26n.c').read_text();a=s.index('static void h48_try_fingertip_poke(i32 hand,const float* handM,i32 gripEdge){');b=s.index('    float rawPos[3]',a)
 f=s[a:b].replace('static void','static int',1).replace('return;','return 0;')+'return 1;}\n'
 tail=r'''
 int main(){float m[16]={0};int err=0;
 terminal=0;if(!h48_try_fingertip_poke(0,m,0))err++;
 terminal=1;g_s26huWorldControlAllowed=0;if(h48_try_fingertip_poke(0,m,0))err++;
 g_s26huWorldControlAllowed=1;if(!h48_try_fingertip_poke(0,m,0))err++;
 g_h30NativeMouseDown=1;if(!h48_try_fingertip_poke(0,m,0))err++;
 terminal=0;if(h48_try_fingertip_poke(0,m,0))err++;
 terminal=1;g_h14GripBody[0]=m;if(h48_try_fingertip_poke(0,m,0))err++;
 if(h48_try_fingertip_poke(1,m,1))err++;
 printf("errors=%d\n",err);return err;
 }
'''
 p=r/f'build/world_gate_{label}.cpp';p.write_text(head+f+tail)
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
 x=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);results[label]={'exit':x.returncode,'output':x.stdout};print(label,x.stdout)
assert results['baseline']['exit']==2 and results['candidate']['exit']==0
(r/'docs/v109-evidence/world_gate_hu.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))

