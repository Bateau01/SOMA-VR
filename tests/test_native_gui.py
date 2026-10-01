from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8')
a=s.index('static i32 s26cr_refresh_native_gui(');b=s.index('static void s26cr_rebuild_native_menu(',a)
c=r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
static u8* module;static int checks;
#define H5754AA_LUX_GLOBAL_RVA 0x8147C0u
#define ext_Log(...) ((void)0)
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line %d\n",__LINE__);exit(1);}}while(0)
static void* ext_GetModuleHandleA(int x){return module;}
static int h20_mem_readable(void*p,u32 n){return p!=0;}
typedef void (__attribute__((ms_abi)) *PFN_H5755DU_SetVirtualSize)(void*,const float*,float,float,const float*);
'''+s[a:b]+r'''
int main(int argc,char**argv){
 CHECK(argc==2);module=(u8*)LoadLibraryExA(argv[1],NULL,DONT_RESOLVE_DLL_REFERENCES);CHECK(module);
 unsigned char base[0x100]={0},hud[0x200]={0},pixel[0x200]={0},immediate[0x100]={0},gui[0x200]={0};
 *(void**)(module+H5754AA_LUX_GLOBAL_RVA)=base;
 *(void**)(base+0x50)=hud;*(void**)(base+0x48)=pixel;*(void**)(base+0xB8)=immediate;*(void**)(immediate+0x48)=gui;
 int sizes[][2]={{1920,1080},{3440,1440},{3440,1427},{2560,1440},{3440,1440},{3440,2800},{3440,1440}};
 for(int n=0;n<7;n++){
  int w=sizes[n][0],h=sizes[n][1];CHECK(s26cr_refresh_native_gui(w,h));
  CHECK(*(float*)(base+0x58)==1024);CHECK(*(float*)(base+0x5C)==768);
  CHECK(*(float*)(pixel+0x100)==w);CHECK(*(float*)(pixel+0x104)==h);
  CHECK(*(float*)(pixel+0x110)==-1000);CHECK(*(float*)(pixel+0x114)==1000);
  CHECK(*(float*)(pixel+0x108)==0);CHECK(*(float*)(pixel+0x10C)==0);
  CHECK(*(float*)(hud+0x100)==*(float*)(base+0x60));CHECK(*(float*)(hud+0x104)==768);
  CHECK(*(float*)(hud+0x108)==*(float*)(base+0x68));CHECK(*(float*)(hud+0x10C)==*(float*)(base+0x6C));
  CHECK(memcmp(hud+0x100,gui+0x100,24)==0);
  CHECK(*(float*)(base+0x70)==-*(float*)(base+0x68));CHECK(*(float*)(base+0x74)==-*(float*)(base+0x6C));
  CHECK(*(float*)(base+0x78)==0);CHECK(*(float*)(base+0x8C)==0);
  if(w==3440&&h==1440)CHECK(fabsf(*(float*)(base+0x60)-2104.88867f)<.01f);
 }
 CHECK(!s26cr_refresh_native_gui(0,1440));
 *(void**)(module+H5754AA_LUX_GLOBAL_RVA)=NULL;CHECK(!s26cr_refresh_native_gui(3440,1440));
 printf("PASS %d production GUI refresh checks using actual Soma.exe layout and SetVirtualSize routines; synthetic GUI objects, no renderer/headset test\n",checks);
}
'''
B=R/'build';(B/'native_gui.c').write_text(c)
subprocess.run([sys.argv[1],'cc','-O2',str(B/'native_gui.c'),'-o',str(B/'native_gui.exe')],check=True)
r=subprocess.run([str(B/'native_gui.exe'),sys.argv[2]],capture_output=True,text=True)
print(r.stdout+r.stderr)
(R/'audit/native_gui_tests.json').write_text(json.dumps({'exit':r.returncode,'output':r.stdout+r.stderr},indent=2));raise SystemExit(r.returncode)

