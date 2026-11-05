"""Actual hint replay function with mock native setter; not rendered-output proof."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
def fn(s,name):
 a=s.index('static i32 '+name+'(');b=s.index('\n}',a)+2;return s[a:b]
head=r"""
#include <cmath>
#include <cstring>
#include <cstdio>
using u8=unsigned char;using u32=unsigned;using i32=int;
static unsigned char context[0x200],object[8];static void* mainCtx=context;static void*g_s26hrHintSet=object;
static u32 g_frameCounter=1,g_h5748oFrameSyncEpoch=1,g_h5754dEndCalls=1;
static float g_s26jbHintModel[16];static void*g_s26jbHintSet;static u32 g_s26jbHintFrame,g_s26jbHintEpoch;static i32 g_s26jbHintValid;
static float result[16];static int writes;
void setter(void*,const float*m){memcpy(result,m,64);writes++;}
using PFN_H5755DU_Set3DMatrix=void(*)(void*,const float*);
#define H5755DU_SET_3D_TRANSFORM_RVA 0
#define H5755DU_SUBTITLE_DISTANCE_M 1.65f
u8* ext_GetModuleHandleA(int){return (u8*)setter;}
int h20_mem_readable(void*p,unsigned){return p!=nullptr;}int h20_mem_executable(void*p){return p!=nullptr;}
void**p2_main_frustum_ptr(){return &mainCtx;}
float h5755ea_world_units_per_meter(){return 1;}
bool h9_good(float x,float l){return std::isfinite(x)&&fabsf(x)<l;}
float h9_abs(float x){return fabsf(x);}float ext_Sqrtf(float x){return sqrtf(x);}
auto p_h5755blAtan2f=atan2f;int h5755bl_resolve_atan2f(){return 1;}
void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
void h10_identity(float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;}
float h5755eb_wrap_pi(float x){while(x>3.14159265f)x-=6.2831853f;while(x< -3.14159265f)x+=6.2831853f;return x;}
"""
tail=r"""
int main(){float*V=(float*)(context+0x158);h10_identity(V);
V[3]=2;CALL_EARLY; // early preparation cannot freeze the final camera location
V[3]=.032f;CALL_FINAL;float left[16];memcpy(left,result,64);
if(fabsf(left[3]+.932f)>.00001f)return 3;
V[3]=-.032f;CALL_FINAL;bool same=memcmp(left,result,64)==0;
g_h5754dEndCalls++;g_frameCounter++;CALL_FINAL;if(memcmp(left,result,64)==0)return 4;
int old=writes;mainCtx=&object;CALL_FINAL;if(writes!=old)return 5;
printf("same_world_plane=%d\n",same);return same?0:1;}
"""
res=[]
for name,path in [('baseline',r/'audit/jb-baseline-20261104/s26n.c'),('candidate',r/'source/s26n.c')]:
 s=path.read_text();f=fn(s,'s26hr_hint_pose');t=tail.replace('CALL_EARLY','s26hr_hint_pose(object,context'+(',0)' if name=='candidate' else ')')).replace('CALL_FINAL','s26hr_hint_pose(object,context'+(',1)' if name=='candidate' else ')'))
 code=head+fn(s,'s26hr_hint_matrix')+(r/'source/hint_anchor_hs.inc').read_text()+f+t
 out=r/'build'/('jb_hint_'+name);out.with_suffix('.cpp').write_text(code)
 subprocess.run([sys.argv[1],'c++','-O2',str(out.with_suffix('.cpp')),'-o',str(out.with_suffix('.exe'))],check=True)
 v=subprocess.run([str(out.with_suffix('.exe'))],capture_output=True,text=True);res.append(dict(variant=name,exit=v.returncode,output=v.stdout));assert v.returncode==(1 if name=='baseline' else 0),res
(r/'audit/jb-hint-test.json').write_text(json.dumps(res,indent=2));print(res)
