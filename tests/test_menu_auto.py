from pathlib import Path
import re,sys,subprocess
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text(encoding='utf-8')
def fn(name):
 m=re.search(r'(?m)^(?:static )?[^\n]*\b'+name+r'\([^;\n]*\)\s*\{',s);assert m,name
 a=s.index('{',m.start());d=0
 for i in range(a,len(s)):
  d+=(s[i]=='{')-(s[i]=='}')
  if not d:return s[m.start():i+1]
start=s.index('typedef struct {\n    unsigned short device[32]')
end=s.index('static u8 __attribute__((ms_abi,noinline,used)) h5750xr1_lowlevel_init_detour(',start)
header=r'''
#include <windows.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned u32;typedef int i32;
static void *query;static int module=1;
static void* ext_GetModuleHandleA(const char*s){(void)s;return module?(void*)1:0;}
static void* ext_GetProcAddress(void*p,const char*s){(void)p;(void)s;return query;}
static void zero_bytes(void*p,size_t n){memset(p,0,n);}
#define CHECK(x) do{if(!(x)){printf("FAIL line %d\n",__LINE__);exit(1);}checks++;}while(0)
static int checks;
'''
mock=r'''
static unsigned desktopW,desktopH;static int available=1;
static int __attribute__((ms_abi)) mode(const unsigned short*d,u32 which,S26CODisplayMode*m){CHECK(!d&&which==0xffffffffu);CHECK(m->size==sizeof(DEVMODEW));m->width=desktopW;m->height=desktopH;return available;}
static int menu=1,pauseActive,fw=2528,fh=2704,cw,ch;
static int g_h5754eMenuW,g_h5754eMenuH,g_h5754dLastClientW,g_h5754dLastClientH,g_h5754dWindowSourceRejects;
static int p2_full_w(void){return fw;}static int p2_full_h(void){return fh;}
static int h5754d_menu_wanted(void){return menu;}static int h5754h_pause_active(void){return pauseActive;}
static void h5754d_resolve_platform(void){}
static void h5755ag_default_client(int*w,int*h){*w=cw;*h=ch;}
'''
body=r'''
int main(void){
 CHECK(sizeof(S26CODisplayMode)==sizeof(DEVMODEW));
 CHECK(offsetof(S26CODisplayMode,width)==offsetof(DEVMODEW,dmPelsWidth));
 CHECK(offsetof(S26CODisplayMode,height)==offsetof(DEVMODEW,dmPelsHeight));
 query=(void*)mode;
 unsigned cases[][2]={{3440,1440},{1920,1080},{2560,1440},{5120,1440},{3840,2160},{1080,1920}};
 for(unsigned n=0;n<sizeof(cases)/sizeof(cases[0]);n++){
  desktopW=cases[n][0];desktopH=cases[n][1];unsigned w=~0u,h=~0u;
  CHECK(s26co_resolve_auto_video_mode(&w,&h));CHECK(w==desktopW&&h==desktopH);
  // Native menu contract and pointer normalization use desktop, never eye dimensions.
  g_h5754eMenuW=w;g_h5754eMenuH=h;cw=w;ch=h;int mw=0,mh=0;
  CHECK(h5754d_menu_source_dims(&mw,&mh));CHECK(mw==(int)w&&mh==(int)h);
  g_h5754eMenuW=g_h5754eMenuH=0;
  CHECK(h5754d_menu_source_dims(&mw,&mh));CHECK(mw==(int)w&&mh==(int)h);
 }
 unsigned w=1280,h=720;CHECK(!s26co_resolve_auto_video_mode(&w,&h));CHECK(w==1280&&h==720);
 desktopW=3440;desktopH=1440;w=1920;h=~0u;CHECK(s26co_resolve_auto_video_mode(&w,&h));CHECK(w==1920&&h==1440);
 for(int scenario=0;scenario<4;scenario++){
  w=h=~0u;module=scenario!=0;query=scenario==1?0:(void*)mode;available=scenario!=2;desktopW=scenario==3?0:3440;
  CHECK(!s26co_resolve_auto_video_mode(&w,&h));CHECK(w==~0u&&h==~0u);
 }
 menu=0;pauseActive=0;int mw,mh;CHECK(h5754d_menu_source_dims(&mw,&mh));CHECK(mw==fw&&mh==fh);
 printf("PASS %d menu resolution / ABI / fallback / gameplay checks\n",checks);
}
'''
code=header+s[start:end]+mock+fn('h5754d_menu_source_dims')+body
B=R/'build';B.mkdir(exist_ok=True);cpp=B/'menu_auto_test.c';cpp.write_text(code)
subprocess.run([sys.argv[1],'cc','-target','x86_64-windows-gnu','-O2',str(cpp),'-o',str(B/'menu_auto_test.exe')],check=True)
subprocess.run([str(B/'menu_auto_test.exe')],check=True)
low=fn('h5750xr1_lowlevel_init_detour')
assert low.index('s26co_resolve_auto_video_mode')<low.index('g_h5754eMenuW=(i32)a1')
print('PASS auto resolution is resolved before menu allocation')
