#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
typedef unsigned u32;typedef int i32;typedef unsigned char u8;
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_GetProcAddress GetProcAddress
#define ext_glGetIntegerv glGetIntegerv
#define ext_glBindTexture glBindTexture
#define ext_glIsEnabled glIsEnabled
#define ext_glEnable glEnable
#define ext_glDisable glDisable
#define ext_glDrawArrays glDrawArrays
#define zero_bytes(p,n) memset(p,0,n)
typedef void* (__attribute__((ms_abi)) *PFN_H5750A_WglGetProcAddress)(const char*);
static void* s26_gl_proc(void* gl,PFN_H5750A_WglGetProcAddress wg,const char* name){void* p=wg(name);return p?p:(void*)GetProcAddress(gl,name);}
static void ext_Log(const char*fmt,...){va_list a;va_start(a,fmt);vprintf(fmt,a);puts("");va_end(a);}
#include "../source/smaa_iu.inc"
#include "../build/native_fxaa_iu.inc"
#define CHECK(x) do{if(!(x)){printf("FAIL line %d: %s error %x\n",__LINE__,#x,glGetError());exit(1);}}while(0)
static u32 fxaaProgram;
static void fxaa_init(){
 const char* vs="#version 330 compatibility\nout vec2 uv;void main(){uv=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(uv*2.-1.,0,1);}";
 u32 v=s26iu.shader(0x8b31),f=s26iu.shader(0x8b30);s26iu.source(v,1,&vs,0);s26iu.compile(v);const char* fs=fxaaShader;s26iu.source(f,1,&fs,0);s26iu.compile(f);int ok=0;s26iu.shaderStatus(f,0x8b81,&ok);if(!ok){char log[2048];s26iu.shaderLog(f,2048,0,log);puts(log);exit(1);}
 fxaaProgram=s26iu.program();s26iu.attach(fxaaProgram,v);s26iu.attach(fxaaProgram,f);s26iu.link(fxaaProgram);s26iu.programStatus(fxaaProgram,0x8b82,&ok);CHECK(ok);s26iu.delShader(v);s26iu.delShader(f);
}
static void fxaa_draw(u32 tex,u32 target,int w,int h){
 S26IUState state;s26iu_save(&state);s26iu.bindFbo(0x8ca9,s26iu.fbo[2]);s26iu.drawBuffer(0x8ce0);s26iu.viewport(0,0,w,h);s26iu.bindVao(s26iu.vao);s26iu.active(0x84c0);glBindTexture(GL_TEXTURE_2D,tex);s26iu.bindSampler(0,s26iu.sampler);s26iu.use(fxaaProgram);s26iu.u1(s26iu.location(fxaaProgram,"tex"),0);
 void(*u2)(int,float,float)=(void*)wglGetProcAddress("glUniform2f");u2(s26iu.location(fxaaProgram,"avInvScreenSize"),1.f/w,1.f/h);glDrawArrays(4,0,3);
 s26iu_restore(&state);
}
static u32 fbo[2],tex[2];static int w,h;static u8* pixels;
static void scene(int eye){
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){
  int p=(y*w+x)*4;int bright=(x>y*.73+40&&x<y*.73+180)||(x>w/2&&y>h/2&&((x+y/3)%37<7));
  pixels[p]=bright?255:20;pixels[p+1]=bright?255:20;pixels[p+2]=eye?(bright?100:220):(bright?255:20);pixels[p+3]=255;
 }
 glBindTexture(GL_TEXTURE_2D,tex[eye]);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
}
static void output(const char* name,u32 f){
 s26iu.bindFbo(0x8ca8,f);glReadBuffer(0x8ce0);glReadPixels(0,0,w,h,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 FILE*out=fopen(name,"wb");fprintf(out,"P6\n%d %d\n255\n",w,h);for(int y=h-1;y>=0;y--)for(int x=0;x<w;x++)fwrite(pixels+(y*w+x)*4,1,3,out);fclose(out);
}
int main(int argc,char**argv){
 w=argc>1?atoi(argv[1]):640;h=argc>2?atoi(argv[2]):480;
 WNDCLASSA c={0};c.style=CS_OWNDC;c.lpfnWndProc=DefWindowProcA;c.hInstance=GetModuleHandleA(0);c.lpszClassName="SMAATest";RegisterClassA(&c);
 HWND win=CreateWindowA(c.lpszClassName,"SMAA GPU check",WS_OVERLAPPEDWINDOW,0,0,128,128,0,0,c.hInstance,0);HDC dc=GetDC(win);
 PIXELFORMATDESCRIPTOR p={0};p.nSize=sizeof(p);p.nVersion=1;p.dwFlags=PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|PFD_DOUBLEBUFFER;p.iPixelType=PFD_TYPE_RGBA;p.cColorBits=32;p.cDepthBits=24;
 int pf=ChoosePixelFormat(dc,&p);CHECK(SetPixelFormat(dc,pf,&p));HGLRC context=wglCreateContext(dc);CHECK(wglMakeCurrent(dc,context));
 printf("GPU %s GL %s\n",glGetString(GL_RENDERER),glGetString(GL_VERSION));CHECK(s26iu_api());
 pixels=malloc(w*h*4);s26iu.genFbo(2,fbo);glGenTextures(2,tex);
 for(int e=0;e<2;e++){scene(e);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,0x812f);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,0x812f);s26iu.bindFbo(0x8d40,fbo[e]);s26iu.attachTex(0x8d40,0x8ce0,GL_TEXTURE_2D,tex[e],0);glDrawBuffer(0x8ce0);CHECK(s26iu.checkFbo(0x8d40)==0x8cd5);}
 s26iu.bindFbo(0x8d40,0);CHECK(glGetError()==0);CHECK(s26iu_process(tex[0],fbo[0],w,h,1));CHECK(glGetError()==0);
 // Exact foreign state restoration, including active DFR and unrelated samplers.
 glViewport(7,8,11,12);glEnable(GL_SCISSOR_TEST);glScissor(1,2,3,4);glEnable(GL_DEPTH_TEST);glEnable(GL_BLEND);glColorMask(1,0,1,0);glEnable(0x8c89);s26iu.active(0x84c2);
 if(s26iu.vrs)glEnable(0x9563);
 S26IUState before,after;int viewport[4];glGetIntegerv(GL_VIEWPORT,viewport);
 CHECK(s26iu_process(tex[1],fbo[1],w,h,1));CHECK(glGetError()==0);int v[4];glGetIntegerv(GL_VIEWPORT,v);CHECK(memcmp(viewport,v,sizeof(v))==0);
 CHECK(glIsEnabled(GL_SCISSOR_TEST)&&glIsEnabled(GL_DEPTH_TEST)&&glIsEnabled(GL_BLEND)&&glIsEnabled(0x8c89));GLboolean mask[4];glGetBooleanv(GL_COLOR_WRITEMASK,mask);CHECK(mask[0]&&!mask[1]&&mask[2]&&!mask[3]);int active;glGetIntegerv(0x84e0,&active);CHECK(active==0x84c2);if(s26iu.vrs){CHECK(glIsEnabled(0x9563));glDisable(0x9563);}
 glDisable(0x8c89);glDisable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glColorMask(1,1,1,1);
 output("build/smaa-left.ppm",fbo[0]);output("build/smaa-right.ppm",fbo[1]);
 // Distinct eye images, flat interiors unchanged and fractional coverage produced.
 for(int e=0;e<2;e++){
  s26iu.bindFbo(0x8ca8,fbo[e]);glReadBuffer(0x8ce0);glReadPixels(0,0,w,h,GL_RGBA,GL_UNSIGNED_BYTE,pixels);int fractional=0;
  CHECK(pixels[2]==(e?220:20));for(int i=0;i<w*h;i++)if(pixels[4*i]>21&&pixels[4*i]<254)fractional++;CHECK(fractional>100);printf("eye%d fractional-edge-pixels %d\n",e,fractional);
 }
 // Menu/loading/pause/off rejects, then gameplay resumes; no accidental processing.
 CHECK(!s26iu_should_process(0,0,1,0,0,0,1));CHECK(!s26iu_should_process(1,0,0,0,0,0,1));CHECK(!s26iu_should_process(1,0,1,1,0,0,1));CHECK(!s26iu_should_process(1,0,1,0,1,0,1));CHECK(!s26iu_should_process(1,0,1,0,0,1,1));CHECK(!s26iu_should_process(1,0,1,0,0,0,0));CHECK(s26iu_should_process(1,1,1,0,0,0,1));
 // Resize resources and return to original dimensions without stale edges.
 CHECK(!s26iu_process(tex[0],fbo[0],w/2,h/2,0));CHECK(g_s26iuReady);CHECK(!s26iu_process(tex[0],fbo[0],w,h,0));CHECK(g_s26iuReady);CHECK(glGetError()==0);
 void(*genq)(int,u32*)=(void*)wglGetProcAddress("glGenQueries");void(*beginq)(u32,u32)=(void*)wglGetProcAddress("glBeginQuery");void(*endq)(u32)=(void*)wglGetProcAddress("glEndQuery");void(*resultq)(u32,u32,unsigned long long*)=(void*)wglGetProcAddress("glGetQueryObjectui64v");u32 q;genq(1,&q);
 // Each sample reloads the same source outside the measured interval.
 fxaa_init();
 for(int mode=0;mode<3;mode++){
  unsigned long long total=0;
  for(int i=0;i<40;i++){scene(0);scene(1);glFinish();beginq(0x88bf,q);
   for(int e=0;e<2;e++){if(mode==2)s26iu_process(tex[e],fbo[e],w,h,1);else if(mode==1)fxaa_draw(tex[e],fbo[e],w,h);}
   endq(0x88bf);unsigned long long ns;resultq(q,0x8866,&ns);if(i>=8)total+=ns;
  }
  printf("BENCH %s stereo %dx%d mean %.4f ms (32 GPU samples)\n",mode==2?"SMAA":mode==1?"FXAA":"OFF",w,h,total/32000000.);CHECK(glGetError()==0);
 }
 puts("PASS: production SMAA shader pixels both eyes, DFR state, state restoration, resize and presentation guards");return 0;
}
