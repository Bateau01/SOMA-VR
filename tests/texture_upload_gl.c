
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL %d %s GL=%x\n",__LINE__,#x,glGetError());exit(1);}}while(0)
typedef void (APIENTRY *Image)(GLenum,GLint,GLenum,GLsizei,GLsizei,GLint,GLsizei,const void*);
typedef void (APIENTRY *Sub)(GLenum,GLint,GLint,GLint,GLsizei,GLsizei,GLenum,GLsizei,const void*);
typedef void (APIENTRY *Storage)(GLenum,GLsizei,GLenum,GLsizei,GLsizei);
typedef void (APIENTRY *Get)(GLenum,GLint,void*);
typedef void (APIENTRY *Buffers)(GLsizei,GLuint*);
typedef void (APIENTRY *Bind)(GLenum,GLuint);
typedef void (APIENTRY *Data)(GLenum,intptr_t,const void*,GLenum);
static Image image;static Sub sub;static Storage storage;static Get get;static Buffers gen,del;static Bind bind;static Data bufferData;
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return 1000.0*t.QuadPart/f.QuadPart;}

typedef uint64_t u64;typedef unsigned u32;typedef int i32;typedef unsigned char u8;
#define CPU_WORK_PROFILE 1
typedef u64 (__attribute__((ms_abi))*CPUTextureBitmap)(void*,void*,i32);static CPUTextureBitmap cpuBitmapOriginal;static u32 cpuStorageStreamingDepth=1;typedef void (__attribute__((ms_abi))*CPUTextureCall)(void*,float);static CPUTextureCall cpuTextureOriginal;
static int ext_MH_CreateHook(void*a,void*b,void**c){return 1;}static int ext_MH_EnableHook(void*a){return 1;}
#define ext_glGetIntegerv glGetIntegerv
#define ext_glBindTexture glBindTexture
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_GetProcAddress GetProcAddress
#define ext_fopen fopen
#define ext_fread fread
#define ext_fclose fclose
#define ext_Log(...) ((void)0)
static u32 mainThread(void){return GetCurrentThreadId();}static u32(*cpuThreadId)(void)=mainThread;static u32 cpuMainThread;
#include "../source/cpu_texture_storage_trial.inc"
static unsigned rd(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
int main(int argc,char**argv){
 int latc=getenv("CPU5_LATC")!=0;cpuTrialMinBytes=65536;
 WNDCLASSA c={0};c.style=CS_OWNDC;c.lpfnWndProc=DefWindowProcA;c.hInstance=GetModuleHandleA(0);c.lpszClassName="TextureUploadTest";CHECK(RegisterClassA(&c));
 HWND win=CreateWindowA(c.lpszClassName,"Texture upload verification",WS_OVERLAPPEDWINDOW,0,0,128,128,0,0,c.hInstance,0);HDC dc=GetDC(win);
 PIXELFORMATDESCRIPTOR p={0};p.nSize=sizeof(p);p.nVersion=1;p.dwFlags=PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|PFD_DOUBLEBUFFER;p.iPixelType=PFD_TYPE_RGBA;p.cColorBits=32;
 CHECK(SetPixelFormat(dc,ChoosePixelFormat(dc,&p),&p));HGLRC ctx=wglCreateContext(dc);CHECK(wglMakeCurrent(dc,ctx));
 image=(Image)wglGetProcAddress("glCompressedTexImage2D");sub=(Sub)wglGetProcAddress("glCompressedTexSubImage2D");storage=(Storage)wglGetProcAddress("glTexStorage2D");get=(Get)wglGetProcAddress("glGetCompressedTexImage");gen=(Buffers)wglGetProcAddress("glGenBuffers");del=(Buffers)wglGetProcAddress("glDeleteBuffers");bind=(Bind)wglGetProcAddress("glBindBuffer");bufferData=(Data)wglGetProcAddress("glBufferData");CHECK(image&&sub&&storage&&get&&gen&&del&&bind&&bufferData);
 printf("GPU %s GL %s\n",glGetString(GL_RENDERER),glGetString(GL_VERSION));
 cpuMainThread=mainThread();cpuTrialEnabled=1;cpuTrialBufferBind=(void*)bind;cpuTrialStorage=(void*)storage;cpuTrialSub=(void*)sub;cpuTrialOriginal=(void*)image;cpuTrialLevel=(void*)glGetTexLevelParameteriv;cpuTrialContext=(void*)wglGetCurrentContext;cpuTrialApiContext=wglGetCurrentContext();
 typedef void(APIENTRY*QueryFormat)(GLenum,GLenum,GLenum,GLsizei,GLint*);QueryFormat query=(QueryFormat)wglGetProcAddress("glGetInternalformativ");int supported=0;if(query)query(GL_TEXTURE_2D,0x8c72,0x826f,1,&supported);cpuTrialLatc=latc&&supported==1;CHECK(!latc||cpuTrialLatc);CHECK(glGetError()==GL_NO_ERROR);
 for(int file=1;file<argc;file++){
 FILE*f=fopen(argv[file],"rb");CHECK(f);fseek(f,0,SEEK_END);long length=ftell(f);rewind(f);unsigned char*bytes=malloc(length);CHECK(fread(bytes,1,length,f)==length);fclose(f);CHECK(!memcmp(bytes,"DDS ",4));
 int w=rd(bytes+16),h=rd(bytes+12),mips=rd(bytes+28);unsigned fmt=0,block=0;size_t header=128;
 if(!memcmp(bytes+84,"DXT1",4)){fmt=0x83f1;block=8;}if(!memcmp(bytes+84,"DXT5",4)){fmt=0x83f3;block=16;}if(!memcmp(bytes+84,"ATI2",4)||!memcmp(bytes+84,"BC5U",4)){fmt=0x8dbd;block=16;}if(!memcmp(bytes+84,"DX10",4)&&rd(bytes+128)==83){fmt=0x8dbd;block=16;header=148;}if(latc&&fmt==0x8dbd)fmt=0x8c72;CHECK(fmt&&mips>0&&mips<16);
 int sizes[16],widths[16],heights[16];size_t offsets[16],total=0;int x=w,y=h;
 for(int l=0;l<mips;l++){widths[l]=x;heights[l]=y;sizes[l]=((x+3)/4)*((y+3)/4)*block;offsets[l]=total;total+=sizes[l];x=x>1?x/2:1;y=y>1?y/2:1;}CHECK(total+header<=length);
 int decodeLevel=0;while(widths[decodeLevel]>2048||heights[decodeLevel]>2048)decodeLevel++;
 size_t decodedSize=(size_t)widths[decodeLevel]*heights[decodeLevel]*4;
 unsigned char*decoded=malloc(decodedSize),*reference=malloc(decodedSize);GLuint referenceTex;glGenTextures(1,&referenceTex);glBindTexture(GL_TEXTURE_2D,referenceTex);
 image(GL_TEXTURE_2D,0,fmt,widths[decodeLevel],heights[decodeLevel],0,sizes[decodeLevel],bytes+header+offsets[decodeLevel]);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,reference);CHECK(glGetError()==GL_NO_ERROR);glDeleteTextures(1,&referenceTex);
 unsigned char*back=malloc(total);double cpu[5]={0},complete[5]={0},max[5]={0};unsigned checks=0;
 for(int round=0;round<24;round++)for(int turn=0;turn<5;turn++){
 int mode=(round+turn)%5;GLuint tex=0,pbo=0;glFinish();double start=now();glGenTextures(1,&tex);glBindTexture(GL_TEXTURE_2D,tex);
 if(mode&2){gen(1,&pbo);bind(0x88ec,pbo);bufferData(0x88ec,total,bytes+header,0x88e0);}
 unsigned char object[0x200]={0},bitmap[0x80]={0};if(mode==4){*(int*)(object+0xac)=1;*(GLuint**)(object+0x120)=&tex;*(GLuint**)(object+0x128)=&tex+1;*(int*)(bitmap+0x68)=mips;cpu_texture_trial_begin(object,bitmap,0);}
 if(mode&1)storage(GL_TEXTURE_2D,mips,fmt,w,h);
 for(int l=0;l<mips;l++){const void*data=(mode&2)?(void*)(uintptr_t)offsets[l]:bytes+header+offsets[l];if(mode&1)sub(GL_TEXTURE_2D,l,0,0,widths[l],heights[l],fmt,sizes[l],data);else if(mode==4)cpu_trial_upload(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],data);else image(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],data);}
 if(mode==4)cpu_texture_trial_end();
 if(mode&2)bind(0x88ec,0);double submitted=now();glFinish();double finished=now();CHECK(glGetError()==GL_NO_ERROR);
 if(round>=4){cpu[mode]+=submitted-start;complete[mode]+=finished-start;if(submitted-start>max[mode])max[mode]=submitted-start;}
 for(int l=0;l<mips;l++){get(GL_TEXTURE_2D,l,back+offsets[l]);CHECK(!memcmp(back+offsets[l],bytes+header+offsets[l],sizes[l]));checks++;}CHECK(glGetError()==GL_NO_ERROR);
 if(round==0){glGetTexImage(GL_TEXTURE_2D,decodeLevel,GL_RGBA,GL_UNSIGNED_BYTE,decoded);CHECK(!memcmp(decoded,reference,decodedSize));CHECK(glGetError()==GL_NO_ERROR);}
 if(pbo)del(1,&pbo);glDeleteTextures(1,&tex);
 }
 for(int mode=0;mode<5;mode++)printf("RESULT file=%s mode=%d dimensions=%dx%d bytes=%zu submit_ms=%.5f completion_ms=%.5f max_submit_ms=%.5f exact_mip_checks=%u\n",argv[file],mode,w,h,total,cpu[mode]/20,complete[mode]/20,max[mode],checks);

 /* Existing mutable texture must keep native redefinition, not immutable storage. */
 GLuint tex=0,foreign=0;glGenTextures(1,&tex);glBindTexture(GL_TEXTURE_2D,tex);
 for(int l=0;l<mips;l++)image(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],bytes+header+offsets[l]);
 unsigned char obj[0x200]={0},bmp[0x80]={0};*(int*)(obj+0xac)=1;*(GLuint**)(obj+0x120)=&tex;*(GLuint**)(obj+0x128)=&tex+1;*(int*)(bmp+0x68)=mips;
 unsigned accepted=cpuTrialAccepted,rejected=cpuTrialRejected;cpu_texture_trial_begin(obj,bmp,0);
 for(int l=0;l<mips;l++)cpu_trial_upload(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],bytes+header+offsets[l]);
 cpu_texture_trial_end();CHECK(cpuTrialAccepted==accepted&&(cpuTrialRejected==rejected+1||sizes[0]<(int)cpuTrialMinBytes));CHECK(glGetError()==GL_NO_ERROR);
 for(int l=0;l<mips;l++){get(GL_TEXTURE_2D,l,back+offsets[l]);CHECK(!memcmp(back+offsets[l],bytes+header+offsets[l],sizes[l]));}
 glDeleteTextures(1,&tex);
 /* Foreign binding at exit: replay on the original texture, restore the foreign binding. */
 glGenTextures(1,&tex);glGenTextures(1,&foreign);glBindTexture(GL_TEXTURE_2D,tex);cpu_texture_trial_begin(obj,bmp,0);
 for(int l=0;l<mips;l++)cpu_trial_upload(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],bytes+header+offsets[l]);
 glBindTexture(GL_TEXTURE_2D,foreign);cpu_texture_trial_end();int binding=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&binding);CHECK(binding==foreign);glBindTexture(GL_TEXTURE_2D,tex);
 for(int l=0;l<mips;l++){get(GL_TEXTURE_2D,l,back+offsets[l]);CHECK(!memcmp(back+offsets[l],bytes+header+offsets[l],sizes[l]));}CHECK(glGetError()==GL_NO_ERROR);
 glDeleteTextures(1,&tex);glDeleteTextures(1,&foreign);CHECK(cpuTrial.count==0&&cpuTrial.depth==0);
 puts("PASS native fallback for existing texture and foreign binding, exact data and no retained scope");
 if(latc&&fmt==0x8c72){
  /* No LATC capability: retain the mutable/native path and identical data. */
  cpuTrialLatc=0;glGenTextures(1,&tex);glBindTexture(GL_TEXTURE_2D,tex);cpu_texture_trial_begin(obj,bmp,0);
  for(int l=0;l<mips;l++)cpu_trial_upload(GL_TEXTURE_2D,l,fmt,widths[l],heights[l],0,sizes[l],bytes+header+offsets[l]);
  cpu_texture_trial_end();int immutable=1;glGetTexParameteriv(GL_TEXTURE_2D,0x912f,&immutable);CHECK(immutable==0);CHECK(glGetError()==GL_NO_ERROR);
  for(int l=0;l<mips;l++){get(GL_TEXTURE_2D,l,back+offsets[l]);CHECK(!memcmp(back+offsets[l],bytes+header+offsets[l],sizes[l]));}
  glDeleteTextures(1,&tex);cpuTrialLatc=1;puts("PASS unsupported LATC capability retains native mutable storage and exact mip bytes");
 }
 free(decoded);free(reference);free(back);free(bytes);
 }
 wglMakeCurrent(0,0);wglDeleteContext(ctx);ReleaseDC(win,dc);DestroyWindow(win);puts("PASS exact compressed mip contents and decoded RGBA across all upload methods");return 0;
}
