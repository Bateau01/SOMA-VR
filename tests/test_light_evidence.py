from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build'
head=r'''
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
static u8 renderer[0x2420],light[0x2b0];static u8* list[1]={light};static int logs,checks;
static int region(const void*p,u32 n,const void*b,u32 len){u64 a=(u64)p,z=(u64)b;return a>=z&&a-z<=len&&n<=len-(a-z);}
static int h20_mem_readable(const void*p,u32 n){return p&& (region(p,n,renderer,sizeof(renderer))||region(p,n,light,sizeof(light))||region(p,n,list,sizeof(list)));}
static void ext_Log(const char*f,...) __attribute__((format(printf,1,2)));
static void ext_Log(const char*f,...){char b[4096];va_list v;va_start(v,f);vsnprintf(b,sizeof(b),f,v);va_end(v);++logs;}
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 s26dn_light_evidence(0,1,0);s26dn_light_evidence(renderer,1,-1);s26dn_light_evidence(renderer,1,2);CHECK(!logs);
 for(int g=0;g<3;g++){*(u64*)(renderer+0x23c8+g*32)=(u64)list;*(u64*)(renderer+0x23d0+g*32)=(u64)(list+1);}
 u8 before[sizeof(renderer)];memcpy(before,renderer,sizeof(renderer));
 for(int eye=0;eye<2;eye++)for(int n=0;n<60;n++){
  int old=logs;s26dn_light_evidence(renderer,n,eye);CHECK(logs-old==(n<48?4:0));CHECK(!memcmp(before,renderer,sizeof(renderer)));
 }
 CHECK(logs==48*2*4);printf("PASS %d bounded read-only light evidence checks\n",checks);return 0;
}
'''
c=B/'light_evidence_test.c';c.write_text(head+(R/'source/light_evidence_dn.inc').read_text()+main)
exe=B/'light_evidence_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-Werror=format',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
