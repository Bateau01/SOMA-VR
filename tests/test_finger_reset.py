from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
header=r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
typedef unsigned char u8;typedef int i32;typedef int64_t i64;typedef unsigned u32;
static u32 g_s26dlTouchKnown[2]={31,31},g_s26dlTouched[2],g_s26dmReleasedMask[2]={31,31};
static u8 g_s26diFrameHand[2]={1,1};static float g_lastSqueeze[2],g_lastTrigger[2];
#define zero_bytes(p,n) memset(p,0,n)
#define ext_Log(...) ((void)0)
static float clamp01(float x){return x<0?0:x>1?1:x;}
#define C(x) do{if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
'''
body=r'''
int main(void){
 float raw[2][5];u8 valid[2]={1,1};i64 t=1000000000LL;
 for(int h=0;h<2;h++)for(int f=0;f<5;f++)raw[h][f]=.1f+f*.18f;
 g_s26eaResetRequest=1;s26ea_finger_reset_tick(t,1,raw,valid);
 for(int i=0;i<499;i++)s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
 C(g_s26eaResetState==1&&!g_s26dzRest[0][4].manual);
 for(int i=0;i<100;i++)s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
 C(g_s26eaResetState==3);
 for(int h=0;h<2;h++)for(int f=0;f<5;f++){
  S26DZRest*r=&g_s26dzRest[h][f];C(r->manual&&fabsf(r->reference-raw[h][f])<.00001);
  C(s26dz_rest_value(r,raw[h][f],1,t,1)<.00001);
  C(s26dz_rest_value(r,1,1,t,0)>.99999);
  C(s26dz_rest_value(r,raw[h][f]+(1-raw[h][f])*.5f,1,t,0)>.4999);
 }
 float saved=g_s26dzRest[0][4].reference;
 // Touch / motion / unavailable tracking / saturation cannot commit.
 for(int scenario=0;scenario<5;scenario++){
  g_s26eaResetRequest=1;
  for(int i=0;i<1600;i++){
   valid[1]=scenario==0?0:1;g_s26dlTouched[0]=scenario==1?1:0;
   raw[0][4]=scenario==2?.99f:scenario==3?(i%2?.1f:.5f):saved;
   g_lastSqueeze[0]=scenario==4?.8f:0;
   s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
  }
  C(g_s26eaResetState==4&&fabsf(g_s26dzRest[0][4].reference-saved)<.00001);
 }
 g_s26eaResetRequest=1;s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
 g_s26eaResetRequest=2;s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);C(g_s26eaResetState==0);
 C(fabsf(g_s26dzRest[0][4].reference-saved)<.00001);
 g_s26eaResetRequest=1;s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
 s26ea_finger_reset_tick(t+=10000000LL,0,raw,valid);C(g_s26eaResetState==4);
 // Controllers without capacitive action coverage can explicitly reset.
 g_s26diFrameHand[0]=g_s26diFrameHand[1]=0;
 g_s26dlTouchKnown[0]=g_s26dlTouchKnown[1]=0;
 g_s26dlTouched[0]=g_s26dlTouched[1]=0;
 g_lastSqueeze[0]=g_lastSqueeze[1]=0;
 valid[0]=valid[1]=1;
 for(int h=0;h<2;h++)for(int f=0;f<5;f++)raw[h][f]=.2f;
 g_s26eaResetRequest=1;
 for(int i=0;i<600;i++)s26ea_finger_reset_tick(t+=10000000LL,1,raw,valid);
 C(g_s26eaResetState==3&&fabsf(g_s26dzRest[1][4].reference-.2f)<.00001);
 puts("PASS delayed atomic rest capture, endpoints, invalid/touched/moving/saturated/gripped rejection, cancel and focus-loss preservation");
}
'''
B=R/'build';p=B/'finger_reset.c'
p.write_text(header+(R/'source/frame_rest_dz.inc').read_text()+(R/'source/finger_reset_ea.inc').read_text()+body)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)

