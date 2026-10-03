from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
head=r'''
#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef long long i64;typedef RECT H5754DRect;
static i32 g_s26dzDesktopW,g_s26dzDesktopH,g_h5755akSavedClientW,g_h5755akSavedClientH,g_s26dySavedSDLW,g_s26dySavedSDLH;
static i64 g_h5755akSavedStyle;static RECT g_h5755akSavedWindowRect;static u32 g_h5755akSnapshotValid;
static void *g_h5755akWindow,*g_h5755asSDLWindow,*sw;static HWND wnd;static HMODULE sdl;static int missing,checks;
static void* current(void){return sw;}static void* currentdc(void){return (void*)1;}static void* fromdc(void*d){return wnd;}
static void* (*p_h5755asSDLGLGetCurrentWindow)(void)=current;
static void (*p_h5755asSDLSetWindowSize)(void*,int,int);
static void* (*p_h5755agWglGetCurrentDC)(void)=currentdc;
static void* (*p_h5755sWindowFromDC)(void*)=fromdc;
static BOOL (WINAPI *p_h5754dGetClientRect)(HWND,RECT*)=GetClientRect;
static BOOL (WINAPI *p_h5755akGetWindowRect)(HWND,RECT*)=GetWindowRect;
static LONG_PTR (WINAPI *p_h5755akGetWindowLongPtrA)(HWND,int)=GetWindowLongPtrA;
static void h5755ak_resolve_window_api(void){}static void h5755as_resolve_sdl_window_api(void){}static void h5755ag_resolve_query_apis(void){}
static void* ext_GetModuleHandleA(const char*n){return sdl;}
static void* ext_GetProcAddress(void*m,const char*n){return missing?0:(void*)GetProcAddress((HMODULE)m,n);}
#define ext_Log(...) ((void)0)
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
body=r'''
int main(void){
 SetProcessDPIAware();sdl=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\SDL2.dll");C(sdl);
 int(*init)(u32)=(void*)GetProcAddress(sdl,"SDL_Init");void(*quit)(void)=(void*)GetProcAddress(sdl,"SDL_Quit");
 void*(*create)(const char*,int,int,int,int,u32)=(void*)GetProcAddress(sdl,"SDL_CreateWindow");
 void(*destroy)(void*)=(void*)GetProcAddress(sdl,"SDL_DestroyWindow");void(*version)(void*)=(void*)GetProcAddress(sdl,"SDL_GetVersion");
 int(*wm)(void*,void*)=(void*)GetProcAddress(sdl,"SDL_GetWindowWMInfo");void(*size)(void*,int*,int*)=(void*)GetProcAddress(sdl,"SDL_GetWindowSize");
 p_h5755asSDLSetWindowSize=(void*)GetProcAddress(sdl,"SDL_SetWindowSize");
 C(init(0x20)==0);
 int dims[3][2]={{1920,1080},{2560,1440},{3440,1440}};
 for(int n=0;n<3;n++){
  sw=create("Hidden SOMA VR exact-client regression",0,0,dims[n][0],dims[n][1],8);C(sw);
  char info[128]={0};version(info);C(wm(sw,info));memcpy(&wnd,info+8,sizeof(wnd));
  g_s26dzDesktopW=dims[n][0];g_s26dzDesktopH=dims[n][1];
  for(int k=0;k<10;k++){
   C(s26ea_desktop_window());RECT cr;C(GetClientRect(wnd,&cr));C(cr.right==dims[n][0]&&cr.bottom==dims[n][1]);
   int w,h;size(sw,&w,&h);C(w==cr.right&&h==cr.bottom);C(g_h5755akSavedClientW==w&&g_h5755akSavedClientH==h);
   RECT before,after;GetWindowRect(wnd,&before);C(s26ea_desktop_window());GetWindowRect(wnd,&after);C(!memcmp(&before,&after,sizeof(before)));
   p_h5755asSDLSetWindowSize(sw,3512,3620);
  }
  missing=1;C(!s26ea_desktop_window());missing=0;g_s26dzDesktopW=0;C(!s26ea_desktop_window());destroy(sw);
 }
 quit();printf("PASS %d production helper checks using SOMA SDL2.dll and real hidden Windows windows; desktop/VR-size alternation and no position drift\n",checks);
}
'''
B=R/'build';p=B/'desktop_window.c'
p.write_text(head+(R/'source/desktop_window_ea.inc').read_text()+body)
subprocess.run([sys.argv[1],'cc',str(p),'-luser32','-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)

