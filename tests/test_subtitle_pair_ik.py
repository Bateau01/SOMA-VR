from pathlib import Path
import re,subprocess,sys,zipfile,json
R=Path(__file__).resolve().parents[1]
def fn(s,name):
 start=s.index('static ',s.index(name)-100) if False else re.search(r'static [^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s).start()
 a=s.index('{',start);depth=0
 for i in range(a,len(s)):
  depth+=(s[i]=='{')-(s[i]=='}')
  if depth==0:return s[start:i+1]
header=r"""
#include <cmath>
#include <cstring>
#include <cstdio>
using i32=int;using u32=unsigned;using u8=unsigned char;
#define __ATOMIC_ACQUIRE 0
#define __ATOMIC_RELAXED 0
#define __atomic_load_n(p,o) (*(p))
#define H5755DU_SUBTITLE_DISTANCE_M 1.65f
#define H5755FL_SUBTITLE_X_OFFSET_M .45f
#define H5755FH_VERTICAL_LIFT_M .9f
#define H5755DU_SET_3D_TRANSFORM_RVA 0
float output[16];int writes=0,object;
void __attribute__((ms_abi)) setter(void*,const float*M){memcpy(output,M,64);writes++;}
using PFN_H5755DU_Set3DMatrix=void (__attribute__((ms_abi)) *)(void*,const float*);
void*ext_GetModuleHandleA(int){return (void*)setter;}int h20_mem_executable(void*){return 1;}int h20_mem_readable(void*,unsigned){return 1;}
void ext_Log(const char*,...){}
float ext_Cosf(float x){return cosf(x);}float ext_Sinf(float x){return sinf(x);}float ext_Sqrtf(float x){return sqrtf(x);}
void h10_identity(float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;}
void h10_copy_f(float*d,const float*s,int n){memcpy(d,s,n*4);}
void* g_h5755duSubtitleSet=&object;u8 context[512];void* mainContext=context;void**p2_main_frustum_ptr(){return &mainContext;}
int g_h5755fmSubtitleLatePoseValid=1,g_h5755fmSubtitleLateSyncRejects,g_h5755fmSubtitleLateSyncs,g_h5755fmSubtitleLateSyncLogged;
float g_h5755fmSubtitleAnchorFx=0,g_h5755fmSubtitleAnchorFz=-1,g_h5755fmSubtitleAnchorPitch=.2f;
float h5755ea_world_units_per_meter(){return 1;}
u32 g_frameCounter=1,g_h5755ebSubtitleAnchorEpoch=2;
float g_s26ikSubtitleModel[16];u32 g_s26ikSubtitleFrame,g_s26ikSubtitleEpoch;u8 g_s26ikSubtitleValid;
"""
tail=r"""
int main(){float*V=(float*)(context+0x158);h10_identity(V);V[3]=.032f;
 if(!h5755fm_refresh_subtitle_final_translation(&object,context))return 2;
 float left[16];memcpy(left,output,64);V[3]=-.032f;g_h5755fmSubtitleAnchorFx=.3f;g_h5755fmSubtitleAnchorFz=-.953939f;
 if(!h5755fm_refresh_subtitle_final_translation(&object,context))return 3;
 bool same=memcmp(left,output,64)==0;printf("pair_identical=%d\n",same);
 g_frameCounter++;h5755fm_refresh_subtitle_final_translation(&object,context);if(memcmp(left,output,64)==0)return 4;
 int old=writes;if(h5755fm_refresh_subtitle_final_translation(&object,&object)||writes!=old)return 5;
 return same?0:1;}
"""
with zipfile.ZipFile(R.parent/'release-IJ/SOMA-VR-1.0.9-S26IJ-Source.zip') as z:old=z.read('SOMA-VR-1.0.9-S26IJ/source/s26n.c').decode()
results=[]
for name,s in [('baseline',old),('candidate',(R/'source/s26n.c').read_text())]:
 p=R/'build'/('subtitle_pair_'+name+'.cpp');p.write_text(header+fn(s,'s26bb_subtitle_matrix')+fn(s,'h5755fm_refresh_subtitle_final_translation')+tail);exe=p.with_suffix('.exe')
 subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
 out=subprocess.run([str(exe)],capture_output=True,text=True);results.append({'variant':name,'exit':out.returncode,'output':out.stdout});assert out.returncode==(1 if name=='baseline' else 0),results
print(results);(R/'docs/v109-evidence/subtitle_pair_ik.json').write_text(json.dumps({'scope':'Extracted actual late-replay function; mock engine setter, translated eye centers and changed anchor; not headset output.','results':results},indent=2))
