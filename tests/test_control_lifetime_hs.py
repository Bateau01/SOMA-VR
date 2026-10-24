"""Production palm scan against retired registry: mocked current-world ray, no headset claim."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
baseline=Path(sys.argv[2])
head=r'''
#include <cstdio>
#include <cstring>
using i32=int;using u32=unsigned;using u8=unsigned char;
struct S26YRocker{u32 id;i32 used,active,blocked,frontAxis,handMask;void *owner,*mainWrapper,*wrapper;const void *mainRaw,*raw;};
S26YRocker g_s26yRocker[64];int g_s26yCount=1,g_s26CutsceneHandsHidden,g_lastSyncResult;
void* g_h14GripBody[2];int g_h482AuthoredDragActive[2],queries,rays,contact,worldHit;
int s26y_gate(){return 1;}int h5754h_pause_active(){return 0;}
float h5755ea_world_units_per_meter(){return 1;}
int s26hr_control_palm(int,float*p,float*d){memset(p,0,12);memset(d,0,12);d[2]=-1;return 1;}
int h20_mem_readable(void*p,unsigned){return p!=nullptr;}
void matrix(const void*,float*m){queries++;memset(m,0,64);}auto p_h14GetMatrix=matrix;
using PFN_H37_GetClosestEntity=int(*)(void*,float*,float*,float,int,int,float*,void**,void**);
alignas(16) char wrapper[0x300];int owner;
int ray(void*,float*,float*,float,int,int,float*dist,void**w,void**o){rays++;*dist=.02f;*w=wrapper;*o=&owner;return worldHit;}
void* h37_map_helper(PFN_H37_GetClosestEntity*f){*f=ray;return &owner;}
int h37_native_wrapper_matches_entity(void*,void*){return 1;}
int s26hr_control_contact(int,void*,void*,float*,float*,int,float){contact++;return 1;}
'''
tail=r'''
int main(){
 auto&r=g_s26yRocker[0];r.used=r.active=1;r.mainWrapper=wrapper;r.owner=&owner;r.mainRaw=(void*)0x5a52a280;
 *(const void**)(wrapper+0x2e8)=r.mainRaw;*(void**)(wrapper+0x2c0)=r.owner;
 s26hr_palm_controls();
 if(queries){printf("FAIL: %d stale Newton queries before current-world selection\n",queries);return 1;}
 if(rays!=2||contact)return 2;
 worldHit=1;s26hr_palm_controls();if(contact!=2)return 3;
 g_h14GripBody[0]=&owner;s26hr_palm_controls();if(contact!=3)return 4;
 g_s26yCount=0;s26hr_palm_controls();if(contact!=3)return 5;
 puts("PASS: stale registry never queried; live first hit, either hand, held-hand and empty-registry gates");
}
'''
results={}
for label,root in [('baseline',baseline),('candidate',r)]:
 s=(root/'source/rocker_y.inc').read_text();a=s.index('static void s26hr_palm_controls');b=s.index('static void s26z_retire_rocker_hand',a)
 p=r/f'build/control_lifetime_{label}.cpp';p.write_text(head+s[a:b]+tail)
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
 v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);results[label]={'exit':v.returncode,'output':v.stdout+v.stderr};print(label,v.stdout)
 s=(root/'source/s26n.c').read_text();a=s.index('static void h576bf_detach_world_bound_refs(const char* why){');b=s.index('\n}',a)
 results[label]['normal_transfer_clears_controls']='s26y_reset();' in s[a:b]
assert results['baseline']['exit']==1 and not results['baseline']['normal_transfer_clears_controls']
assert results['candidate']['exit']==0 and results['candidate']['normal_transfer_clears_controls']
(r/'docs/v109-evidence/control_lifetime_hs.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
