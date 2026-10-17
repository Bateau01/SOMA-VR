"""Production swap observer with mocked renderer; verifies failure diagnostics and opt-in bounds."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text();a=s.index('void __attribute__((ms_abi,noinline,used)) s26gj_swap_begin(');b=s.index('/* Fixed call in',a)
head=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned u32;typedef int i32;static unsigned char cache[0x41000];static unsigned char* p2_base(void){return cache;}
static u32 g_s26cqStageReady,g_s26fiMirrorReady,g_h5755asUiIslandActive,g_h5755bhPresentationState,g_h5750yResolveFbo[2];
static int g_h5750yResolveW=100,g_h5750yResolveH=100,flagOn,title,drawableOn=1,targetOn,dumps,windows,stages,allocations,copies,swaps,paths,logs;
static int h5755ay_make_trace_path(char*p,const char*n){strcpy(p,"EXE/");strcat(p,n);paths++;return 1;}
static void* ext_fopen(const char*p,const char*m){if(strncmp(p,"EXE/",4))abort();return flagOn?(void*)1:0;}
static void ext_fclose(void*p){}
#define ext_Log(...) (++logs)
static int g_s26fiMirrorEnabled=1;static int s26hq_init(void){return 1;}
static int h5754d_menu_wanted(void){return title;}static int h5754h_pause_active(void){return 0;}
static int p2_xr_on(void){return 1;}static int p2_xr_running(void){return 1;}static int p2_sbs_on(void){return 1;}
static int s26cb_flat_drawable_extent(int*w,int*h){*w=100;*h=100;return drawableOn;}
static int h5750y_ensure_resolve_targets(void){allocations++;if(targetOn)g_h5750yResolveFbo[0]=1;return targetOn;}
static int s26cq_copy_menu_backbuffer(u32 f,int a,int b,int c,int d){copies++;return 1;}
static void s26cq_dump(u32 f,int w,int h,const char*n){dumps++;if(f)stages++;else windows++;}
static int original(void*p){swaps++;return 7;}static int (*o_s26cqSwap)(void*)=original;
'''
main=r'''
#define CHECK(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
int main(int argc,char**argv){int mode=atoi(argv[1]);flagOn=mode!=0;title=mode>=2;g_h5755asUiIslandActive=title;targetOn=mode==3;
 for(int i=0;i<1000;i++){s26gj_swap_begin();if(mode!=3)CHECK(!g_s26cqStageReady);}
 CHECK(paths==1);
 if(mode==0)CHECK(dumps==0&&allocations==0);
 if(mode==1)CHECK(windows==2&&stages==0&&allocations==0);
 if(mode==2)CHECK(windows==2&&stages==0&&allocations==1000&&copies==0);
 if(mode==3)CHECK(windows==2&&stages==2&&copies==1000);
 puts("PASS bounded opt-in capture and menu observer bounds");return 0;
}
'''
B=R/'build';B.mkdir(exist_ok=True);p=B/'menu_observer.c';end=s[s.index('static i32 __attribute__((ms_abi)) h5754d_xr_end_frame('):];end=end[:end.index('}\n')+2];head+='typedef void* Handle;typedef int XrFrameEndInfo;static int s26gj_xr_end_frame_impl(Handle h,const XrFrameEndInfo* i){return *i;}\n';main=main.replace('puts(','for(int k=-2;k<2;k++){g_s26cqStageReady=1;g_s26fiMirrorReady=1;CHECK(h5754d_xr_end_frame(0,&k)==k);CHECK(!g_s26cqStageReady&&!g_s26fiMirrorReady);}puts(');p.write_text(head+s[a:b]+end+main)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
for i in range(4):subprocess.run([str(p.with_suffix('.exe')),str(i)],check=True)
