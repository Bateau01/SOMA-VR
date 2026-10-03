from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/frame_rest_dz.inc').read_text()
head=r'''
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
typedef int i32;typedef int64_t i64;typedef unsigned u32;
static int g_s26diFrameHand[2]={1,1};
static u32 g_s26dlTouchKnown[2],g_s26dlTouched[2],g_s26dmReleasedMask[2];
#define zero_bytes(p,n) memset(p,0,n)
#define ext_Log(...) ((void)0)
static float clamp01(float x){return x<0?0:x>1?1:x;}
#define C(x) do{if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);return 1;}}while(0)
'''
body=r'''
int main(void){
 for(int hz=72;hz<=144;hz++){
  S26DZRest r={0};i64 t=1000000000LL,dt=1000000000LL/hz;float v=0;
  for(int n=0;n<hz;n++,t+=dt)v=s26dz_rest_value(&r,.35f,1,t,1);
  C(r.learned&&fabsf(v)<.00001f);
  // Thumb contact / ongoing contact cannot flatten or slow tracked motion.
  C(fabsf(s26dz_rest_value(&r,1,1,t+=dt,0)-1)<.00001f);
  C(fabsf(s26dz_rest_value(&r,.35f,1,t+=dt,0))<.00001f);
  C(s26dz_rest_value(&r,.70f,1,t+=dt,0)>.5f);
  for(int n=0;n<hz;n++,t+=dt)s26dz_rest_value(&r,.4f,1,t,1);
  C(fabsf(r.reference-.35f)<.00001f); // Never chase a larger curl upward.
  for(int n=0;n<hz;n++,t+=dt)s26dz_rest_value(&r,.1f,1,t,1);
  C(fabsf(r.reference-.1f)<.00001f);
 }
 S26DZRest r={0};i64 t=1000000000LL;
 for(int n=0;n<100;n++)s26dz_rest_value(&r,.8f,1,t+=10000000LL,1);
 C(!r.learned); // Do not interpret a closed finger as an idle reference.
 for(int n=0;n<100;n++)s26dz_rest_value(&r,n%2?.1f:.3f,1,t+=10000000LL,1);
 C(!r.learned); // Motion cannot establish rest.
 for(int n=0;n<100;n++)s26dz_rest_value(&r,.3f,1,t+=200000000LL,1);
 C(!r.learned); // Gaps / focus interruptions cannot satisfy the dwell.
 for(int n=0;n<100;n++)s26dz_rest_value(&r,.3f,1,t+=10000000LL,0);
 C(!r.learned);
 float cv[4]={.3f,.3f,.3f,.3f};g_s26dlTouchKnown[0]=31;g_s26dmReleasedMask[0]=31;g_s26dlTouched[0]=1;
 for(int n=0;n<100;n++){cv[0]=.3f;s26dz_rest_correct(0,4,t+=10000000LL,cv);}
 C(!g_s26dzRest[0][4].learned); // Thumb touch cannot establish any new reference.
 g_s26dlTouched[0]=0;
 for(int n=0;n<100;n++){cv[0]=.3f;s26dz_rest_correct(0,4,t+=10000000LL,cv);}
 C(g_s26dzRest[0][4].learned&&cv[0]<.00001f);
 C(!g_s26dzRest[0][3].learned&&!g_s26dzRest[1][4].learned);
 s26dz_rest_reset(0);C(!g_s26dzRest[0][4].learned);
 puts("PASS stable released reference at 72-144 Hz, instant curl/release, thumb isolation, closed/moving/unknown rejection, gaps and reset");return 0;
}
'''
B=R/'build';B.mkdir(exist_ok=True);p=B/'frame_rest.c';p.write_text(head+s+body)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True);subprocess.run([str(p.with_suffix('.exe'))],check=True)
