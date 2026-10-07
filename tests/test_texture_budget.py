"""Exercise the actual menu-controlled budget implementation and restoration."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=(R/'source/s26n.c').read_text();start=s.index('static i32 g_s26TextureSetting=');end=s.index('static void h25_dispatch_pending',start)
source=s[start:end]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;typedef unsigned long long u64;
static u8 game[0x900000];static int running=1,on=1,g_h576mScriptRuntimePublished=1,readable=1;
static void* ext_GetModuleHandleA(void*p){return game;}
static int h20_mem_readable(void*p,u32 n){return readable;}
static int p2_xr_on(void){return on;}static int p2_xr_running(void){return running;}
#define ext_Log(...) ((void)0)
#define C(x) do{++checks;if(!(x)){printf("FAIL %d: %s\n",__LINE__,#x);return 1;}}while(0)
static int checks;
'''
# Copy the production verification bytes into the fake engine.
sig=source[source.index('const u8 sig[29]='):source.index(';',source.index('const u8 sig[29]='))+1]
body=r'''
int main(void){
 SIGNATURE
 memcpy(game+0x2de9c0,sig,sizeof(sig));u64* budget=(u64*)(game+0x80cca8);*budget=0x40000000ull;
 s26_texture_streaming_step();C(*budget==0x40000000ull&&!g_s26TextureVerified);
 s26ef_set_texture_budget(1);s26_texture_streaming_step();C(*budget==0x60000000ull&&g_s26TextureOwned);
 s26ef_set_texture_budget(0);s26_texture_streaming_step();C(*budget==0x40000000ull&&!g_s26TextureOwned);
 for(int i=0;i<100;i++){
  s26ef_set_texture_budget(1);s26_texture_streaming_step();C(*budget==0x60000000ull);
  running=0;s26_texture_streaming_step();C(*budget==0x40000000ull);running=1;
 }
 s26_texture_streaming_step();*budget=0x70000000ull;s26ef_set_texture_budget(0);s26_texture_streaming_step();
 C(*budget==0x70000000ull&&!g_s26TextureOwned); // Never overwrite another owner's change.
 s26ef_set_texture_budget(1);s26_texture_streaming_step();C(*budget==0x70000000ull&&!g_s26TextureOwned);
 g_s26TextureVerified=0;g_s26TextureBudget=0;*budget=0x40000000ull;game[0x2de9c0]^=1;
 s26_texture_streaming_step();C(!g_s26TextureBudget&&*budget==0x40000000ull);
 printf("PASS %d budget lifecycle checks\n",checks);return 0;
}
'''.replace('SIGNATURE',sig)
c=B/'texture_budget_test.c';c.write_text(head+source+body);exe=B/'texture_budget_test.exe'
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
