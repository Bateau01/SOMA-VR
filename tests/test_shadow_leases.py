"""Exercise stereo shadow lease boundary against native-layout mock pools.
The allocator model is transcribed from Ghidra 1401f1b10; no GPU is simulated.
"""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
src=r'''
#include <stdio.h>
#include <string.h>
#include <stdint.h>
typedef unsigned char u8;typedef unsigned u32;typedef uint64_t u64;typedef int i32;
static void* ext_GetModuleHandleA(int n){return 0;}
static int h20_mem_readable(const void*p,u32 n){return p!=0;}
static int h20_mem_writable(void*p,u32 n){return p!=0;}
#include "shadow_leases_dm.inc"
static int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
static void* native_lease(u8** rec,int n,u32 frame,void* light){
 int bestAge=-1;u8* best=0;
 for(int i=0;i<n;i++){
  u32 used=*(u32*)(rec[i]+0x18);
  if(*(void**)(rec[i]+0x20)==light&&used!=frame){best=rec[i];bestAge=1;break;}
  int age=(int)(used-frame);if(age<0)age=-age;
  if(age>bestAge){bestAge=age;best=rec[i];}
 }
 if(best&&bestAge>0){*(u32*)(best+0x18)=frame;return best;}return 0;
}
int main(void){
 u8 renderer[0x1000]={0},records[4][0x38];u8* ptrs[4];int world,frustum,light;
 for(int i=0;i<4;i++){ptrs[i]=records[i];}
 *(u64*)(renderer+0x850)=(u64)ptrs;*(u64*)(renderer+0x858)=(u64)(ptrs+4);
 for(int order=0;order<2;order++)for(int fault=0;fault<8;fault++){
  memset(records,0x45,sizeof(records));memset(&g_s26dmShadowBoundary,0,sizeof(g_s26dmShadowBoundary));
  for(int i=0;i<4;i++){*(u32*)(records[i]+0x18)=99;*(void**)(records[i]+0x20)=&light;}
  C(s26dm_shadow_begin(1,renderer,&world,&frustum,200,100,order)==0);
  // Four leases exhaust the native current-frame pool, independent of light.
  for(int i=0;i<4;i++)C(native_lease(ptrs,4,100,&light)!=0);
  C(native_lease(ptrs,4,100,&light)==0);
  if(fault!=1)s26dm_shadow_end(1,renderer,&world,&frustum,200,100,order);
  u8 before[sizeof(records)];memcpy(before,records,sizeof(records));
  u32 n=s26dm_shadow_begin(fault!=2,fault==3?0:renderer,fault==4?0:&world,&frustum,fault==5?201:200,fault==6?101:100,fault==7?order:1-order);
  C(n==(fault==0?4:0));
  for(int i=0;i<4;i++)for(int j=0;j<0x38;j++)if(j<0x18||j>=0x1c)C(records[i][j]==before[i*0x38+j]);
  if(!fault){C(native_lease(ptrs,4,100,&light)!=0);C(s26dm_shadow_begin(1,renderer,&world,&frustum,200,100,1-order)==0);}
  else C(memcmp(before,records,sizeof(records))==0);
 }
 C(!s26dm_native_render_stamp());
 printf("PASS %d stereo lease, pool exhaustion, unchanged contents/ages and rejection checks\n",checks);return 0;
}
'''
c=B/'shadow_leases_test.c';c.write_text(src);exe=B/'shadow_leases_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-I'+str(R/'source'),str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
