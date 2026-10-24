from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text()
def fun(name):
 a=s.index('static ',s.index(name)-30);b=s.index('{',a);n=1;i=b+1
 while n:n+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
code=r'''
#include <cmath>
#include <cstring>
#include <cstdio>
#include <cstdlib>
using i32=int;using u32=unsigned;using u8=unsigned char;
float distanceM=1.65f;u32 g_frameCounter,g_h5748oFrameSyncEpoch;int logs;
#define H5755DU_SUBTITLE_DISTANCE_M distanceM
#define H5755FL_SUBTITLE_X_OFFSET_M .45f
#define H5755FH_VERTICAL_LIFT_M .2f
float ext_Cosf(float f){return cosf(f);}float ext_Sinf(float f){return sinf(f);}float h9_abs(float f){return fabsf(f);}
bool h9_good(float f,float lim){return std::isfinite(f)&&fabsf(f)<lim;}
void h10_identity(float*m){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;}
void h10_copy_f(float*a,const float*b,int n){memcpy(a,b,n*4);}
void ext_Log(const char*,...){logs++;}
'''+fun('s26bb_subtitle_matrix(')+'\n'+fun('s26hr_hint_matrix(')+'\n'+fun('s26hw_subtitle_compare(')+r'''
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
int main(){
 for(float d:{.75f,1.65f,4.f})for(float scale:{.5f,1.f,2.f}){
  distanceM=d;float v[16],m[16],sub[16];h10_identity(v);
  C(s26hr_hint_matrix(v,scale,m));s26bb_subtitle_matrix(sub,0,0,0,0,-1,0,scale);
  C(fabsf(m[11]+d*scale)<1e-5f);C(m[11]==sub[11]);C(fabsf(m[7]-.75f*scale)<1e-5f);
 }
 float m[16],saved[16];h10_identity(m);memcpy(saved,m,64);
 for(int i=0;i<30;i++){g_frameCounter=i*300;s26hw_subtitle_compare(m);s26hw_subtitle_compare(m);s26hw_subtitle_compare(m);}
 C(logs==12);C(memcmp(saved,m,64)==0);
 printf("PASS %d shared-distance/observation assertions\n",checks);
}
'''
code=code.replace('#include <cmath>','#include <cmath>\n#include <initializer_list>')
p=r/'build/text_hw.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'docs/v109-evidence/text_hw.json').write_text(json.dumps({'scope':'Extracted production math and bounded observer; not rendered-eye validation','exit':v.returncode,'output':v.stdout+v.stderr},indent=2));print(v.stdout+v.stderr);raise SystemExit(v.returncode)
