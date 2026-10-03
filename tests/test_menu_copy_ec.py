from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text(encoding='utf8'); a=s.index('typedef u32 (__attribute__((ms_abi)) *S26ECGetError)');b=s.index('/* P2 mirrors',a)
head=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
typedef unsigned u32;typedef int i32;typedef unsigned char u8;
typedef void (*PFN_H5750V_BindFramebuffer)(u32,u32);
typedef void (*PFN_H5750V_BlitFramebuffer)(i32,i32,i32,i32,i32,i32,i32,i32,u32,u32);
typedef void (*PFN_H5754AQ_DrawBuffer)(u32);
typedef void (*PFN_BindBufferH9)(u32,u32);
static void (*gen)(int,u32*),(*del)(int,const u32*),(*ft)(u32,u32,u32,u32,int);
static PFN_H5750V_BindFramebuffer bind;
static PFN_H5750V_BlitFramebuffer blit;
static PFN_BindBufferH9 bb;
static u32 (*p_s26CheckResolveFbo)(u32);
#define p_h5750yGenTextures glGenTextures
#define p_h5750yDeleteTextures glDeleteTextures
#define p_h5750yTexImage2D glTexImage2D
#define p_h5750yTexParameteri glTexParameteri
#define p_h5750vReadBuffer glReadBuffer
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_GetProcAddress GetProcAddress
#define ext_glGetIntegerv glGetIntegerv
#define ext_glBindTexture glBindTexture
#define ext_glIsEnabled glIsEnabled
#define ext_glEnable glEnable
#define ext_glDisable glDisable
static void ext_Log(const char* fmt,...){va_list a;va_start(a,fmt);vprintf(fmt,a);puts("");va_end(a);}
static int h5750y_resolve_gl_ready(void){return 1;}
static int s26_resolve_validation_ready(void){return 1;}
static void h5750v_resolve_read_buffer(void){}
static PFN_H5750V_BindFramebuffer h5750v_bind_fbo(void){return bind;}
static PFN_H5750V_BlitFramebuffer h5750v_blit(void){return blit;}
// Simulate the startup condition: hand-renderer function table is not ready.
static PFN_BindBufferH9 p2_bind_buffer(void){return 0;}
typedef void* (*PFN_H5750A_WglGetProcAddress)(const char*);
static void* s26_gl_proc(void* ogl,PFN_H5750A_WglGetProcAddress wg,const char* name){return wg(name);}
static void (*h5750y_gen_fbo(void))(int,u32*){return gen;}
static void (*h5750y_delete_fbo(void))(int,const u32*){return del;}
static void (*h5750y_fbo_tex2d(void))(u32,u32,u32,u32,int){return ft;}
'''
main=r'''
#define CHECK(x) do{if(!(x)){printf("FAIL line %d error %x\n",__LINE__,glGetError());exit(1);}}while(0)
int main(int argc,char**argv){
 HMODULE sdl=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\SDL2.dll");CHECK(sdl);
 int (*init)(unsigned)=(void*)GetProcAddress(sdl,"SDL_Init");
 int (*attr)(int,int)=(void*)GetProcAddress(sdl,"SDL_GL_SetAttribute");
 void* (*win)(const char*,int,int,int,int,unsigned)=(void*)GetProcAddress(sdl,"SDL_CreateWindow");
 void* (*ctx)(void*)=(void*)GetProcAddress(sdl,"SDL_GL_CreateContext");
 CHECK(init(0x20)==0);int ms=argc>1?atoi(argv[1]):0; int ww=argc>2?atoi(argv[2]):640, hh=argc>3?atoi(argv[3]):360;
 attr(5,1);attr(13,ms?1:0);attr(14,ms);attr(17,3);attr(18,3);attr(21,2);
 void*w=win("SOMA VR isolated GL copy test",0,0,ww,hh,2|8|0x10);CHECK(w);CHECK(ctx(w)); void (*size)(void*,int*,int*)=(void*)GetProcAddress(sdl,"SDL_GL_GetDrawableSize");int actualW=0,actualH=0;size(w,&actualW,&actualH);printf("Drawable %dx%d requested %dx%d\n",actualW,actualH,ww,hh);CHECK(actualW==ww&&actualH==hh);
 #define PROC(v,n) v=(void*)wglGetProcAddress(n);CHECK(v)
 PROC(gen,"glGenFramebuffers");PROC(del,"glDeleteFramebuffers");PROC(ft,"glFramebufferTexture2D");PROC(bind,"glBindFramebuffer");PROC(blit,"glBlitFramebuffer");PROC(bb,"glBindBuffer");PROC(p_s26CheckResolveFbo,"glCheckFramebufferStatus");
 u32 f,t;gen(1,&f);glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,800,700,0,GL_RGBA,GL_UNSIGNED_BYTE,0);bind(0x8D40,f);ft(0x8D40,0x8CE0,GL_TEXTURE_2D,t,0);CHECK(p_s26CheckResolveFbo(0x8D40)==0x8CD5);
 bind(0x8D40,0);glDrawBuffer(GL_BACK);glClearColor(.25,.5,.75,1);glClear(GL_COLOR_BUFFER_BIT);glReadBuffer(GL_BACK);
 bind(0x8CA9,f);blit(0,0,ww,hh,0,0,800,700,GL_COLOR_BUFFER_BIT,GL_LINEAR);
 u32 old=glGetError();printf("Old scaled copy samples=%d error=0x%x\n",ms,old);CHECK(ms?old==0x502:old==0);
 bind(0x8D40,0);glEnable(GL_SCISSOR_TEST);glScissor(0,0,1,1);
 CHECK(s26cq_copy_menu_backbuffer(f,ww,hh,800,700));CHECK(glIsEnabled(GL_SCISSOR_TEST));
 i32 rd,dr;glGetIntegerv(0x8CAA,&rd);glGetIntegerv(0x8CA6,&dr);CHECK(!rd&&!dr);
 bind(0x8CA8,f);glReadBuffer(0x8CE0);u8 pixel[4];glReadPixels(400,350,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);
 printf("New staged pixel %u %u %u %u\n",pixel[0],pixel[1],pixel[2],pixel[3]);CHECK(abs(pixel[0]-64)<=1&&abs(pixel[1]-128)<=1&&abs(pixel[2]-191)<=1&&pixel[3]==255);CHECK(glGetError()==0);
 // A complete framebuffer whose draw buffer was NONE must still be populated,
 // and its prior state must be restored.
 bind(0x8CA9,f);glDrawBuffer(GL_NONE);bind(0x8D40,0);
 CHECK(s26cq_copy_menu_backbuffer(f,ww,hh,800,700));bind(0x8CA9,f);glGetIntegerv(GL_DRAW_BUFFER,&dr);CHECK(dr==GL_NONE);
 // Native-size restore into multisampled default framebuffer is legal.
 bind(0x8CA8,s26ec_fbo);glReadBuffer(0x8CE0);bind(0x8CA9,0);glDrawBuffer(GL_BACK);glDisable(GL_SCISSOR_TEST);blit(0,0,ww,hh,0,0,ww,hh,GL_COLOR_BUFFER_BIT,GL_NEAREST);CHECK(glGetError()==0);

 // Exercise menu -> distinct cropped left/right frames -> menu -> resumed eyes.
 u32 rightF,rightT;gen(1,&rightF);glGenTextures(1,&rightT);glBindTexture(GL_TEXTURE_2D,rightT);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,800,700,0,GL_RGBA,GL_UNSIGNED_BYTE,0);bind(0x8D40,rightF);ft(0x8D40,0x8CE0,GL_TEXTURE_2D,rightT,0);
 for(int cycle=0;cycle<3;cycle++){
  bind(0x8D40,0);glDisable(GL_SCISSOR_TEST);glClearColor(0,0,1,1);glClear(GL_COLOR_BUFFER_BIT);
  glEnable(GL_SCISSOR_TEST);glScissor(0,0,ww/2,hh);glClearColor(1,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
  CHECK(s26ee_copy_eye(0,f,ww,hh,0,0,ww/2,hh,800,700));CHECK(glIsEnabled(GL_SCISSOR_TEST));
  bind(0x8D40,0);glScissor(ww/2,0,ww-ww/2,hh);glClearColor(0,1,0,1);glClear(GL_COLOR_BUFFER_BIT);
  CHECK(s26ee_copy_eye(1,rightF,ww,hh,ww/2,0,ww,hh,800,700));
  bind(0x8CA8,f);glReadBuffer(0x8CE0);glReadPixels(400,350,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);CHECK(pixel[0]==255&&pixel[1]==0&&pixel[2]==0);
  bind(0x8CA8,rightF);glReadBuffer(0x8CE0);glReadPixels(400,350,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);CHECK(pixel[0]==0&&pixel[1]==255&&pixel[2]==0);
  bind(0x8D40,0);CHECK(s26cq_copy_menu_backbuffer(f,ww,hh,800,700));CHECK(glGetError()==0);
 }
 puts("PASS: both eyes fresh, independent asymmetric crops, menu/resume cycles");
 // Incomplete destination must fail instead of reporting ready.
 u32 broken;gen(1,&broken);CHECK(!s26cq_copy_menu_backbuffer(broken,ww,hh,800,700));
 CHECK(!s26cq_copy_menu_backbuffer(0,ww,hh,800,700));
 puts("PASS real OpenGL capture, scale, state restore, desktop restore, failed-copy rejection");return 0;
}
'''
p=r/'build/test_menu_ec.c';p.parent.mkdir(exist_ok=True);p.write_text(head+s[a:b]+main)
subprocess.run([sys.argv[1],'cc',str(p),'-lopengl32','-lgdi32','-o',str(p.with_suffix('.exe'))],check=True)
for samples,ww,hh in [('0','1920','1080'),('2','1920','1080'),('4','1920','1080'),('0','2560','1440'),('4','3440','1440')]:
 subprocess.run([str(p.with_suffix('.exe')),samples,ww,hh],check=True)



