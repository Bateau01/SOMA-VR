"""Recorder mocks plus real Windows QPC/OpenGL timestamp execution."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head=r'''
#include <windows.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstring>
#undef NDEBUG
#include <cassert>
#include <cstdint>
using u32=unsigned;using i32=int;using u8=unsigned char;using u64=uint64_t;using i64=int64_t;
u32 g_frameCounter=1,g_h14PhysicsSteps=2,g_h5755bhPresentationState=3,g_h576bfMapTransitionActive,g_h5755asUiIslandActive,g_h5755asResumeClassifyActive,g_h5755azExitPending,g_h5750vPrimeWrapperActive;
#define H5755BH_GAMEPLAY_VR 3
alignas(8) unsigned char xr[256];float camera[128];bool flag=false;int writes,cameraReads;
void* p2_xr_obj(){return xr;}void*p2_camera_obj(){cameraReads++;return camera;}
void zero_bytes(void*p,u32 n){memset(p,0,n);}void ext_Log(const char*,...){}
int make_sibling_path(char*p,u32 n,const char*s){snprintf(p,n,"%s",s);return 1;}
void*ext_fopen(const char*p,const char*m){if(strstr(p,".flag"))return flag?(void*)1:nullptr;writes++;return fopen(p,m);}
int ext_fclose(void*p){return p==(void*)1?0:fclose((FILE*)p);}u64 ext_fwrite(const void*p,u64 s,u64 n,void*f){return fwrite(p,s,n,(FILE*)f);}
void*ext_GetModuleHandleA(const char*s){return GetModuleHandleA(s);}void*ext_GetProcAddress(void*m,const char*s){return (void*)GetProcAddress((HMODULE)m,s);}
'''
gpu=r'''
static void* (*p_s26efContext)()=[]()->void*{return wglGetCurrentContext();};
static void (*p_s26eiGenQueries)(i32,u32*);static void (*p_s26eiQueryCounter)(u32,u32);
static void (*p_s26eiQueryAvailable)(u32,u32,u32*);static void (*p_s26eiQueryResult)(u32,u32,u64*);static void (*p_s26eiTimerBindBuffer)(u32,u32);
void ext_glGetIntegerv(u32 e,i32*p){glGetIntegerv(e,p);}int s26ei_timer_init(){return wglGetCurrentContext()!=nullptr;}
'''
tail=r'''
int main(){setbuf(stdout,nullptr);puts("stage recorder");
 s26ih_begin_capture();assert(!g_s26ihEnabled&&s26ih_now()==0);s26ih_event(1,0,1,2,0,0);assert(!g_s26ihCount&&!writes);
 flag=true;g_s26ihInit=0;s26ih_begin_capture();assert(g_s26ihEnabled&&g_s26ihFrequency);
 float m[16]={};m[12]=12;m[15]=1;s26ih_hand(0,m);assert(g_s26ihCount==1&&g_s26ihRows[0].model[12]==12);
 g_h576bfMapTransitionActive=1;s26ih_hand(0,m);assert(g_s26ihCount==1&&cameraReads==1);g_h576bfMapTransitionActive=0;
 g_h5755bhPresentationState=0;s26ih_hand(0,m);assert(g_s26ihCount==1);g_h5755bhPresentationState=3;
 u32 owner=g_s26ihOwner;g_s26ihOwner=0;s26ih_hand(0,m);assert(g_s26ihOtherThread==1&&g_s26ihCount==1);g_s26ihOwner=owner;
 puts("stage GL context");HWND w=CreateWindowA("STATIC","IH test",WS_POPUP,0,0,32,32,0,0,GetModuleHandleA(0),0);assert(w);HDC dc=GetDC(w);
 PIXELFORMATDESCRIPTOR p={sizeof(p),1};p.dwFlags=PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|PFD_DOUBLEBUFFER;p.iPixelType=PFD_TYPE_RGBA;p.cColorBits=24;
 puts("window ready");int pf=ChoosePixelFormat(dc,&p);assert(pf&&SetPixelFormat(dc,pf,&p));puts("pixel format ready");HGLRC ctx=wglCreateContext(dc);assert(ctx&&wglMakeCurrent(dc,ctx));
#define LOAD(dst,name) dst=(decltype(dst))wglGetProcAddress(name);printf("%s %p\n",name,(void*)dst);assert(dst && (uintptr_t)dst>4096)
 LOAD(p_s26eiGenQueries,"glGenQueries");LOAD(p_s26eiQueryCounter,"glQueryCounter");LOAD(p_s26eiQueryAvailable,"glGetQueryObjectuiv");LOAD(p_s26eiQueryResult,"glGetQueryObjectui64v");LOAD(p_s26eiTimerBindBuffer,"glBindBuffer");
 void(*genBuffers)(int,u32*);LOAD(genBuffers,"glGenBuffers");u32 qb=0;genBuffers(1,&qb);p_s26eiTimerBindBuffer(0x9192,qb);
 puts("stage GPU pairs");for(int k=0;k<320;k++){int ticket=s26ih_gpu_begin();glClear(GL_COLOR_BUFFER_BIT);s26ih_gpu_end(ticket);glFlush();Sleep(1);g_frameCounter++;}
 puts("stage validate");int binding=0;glGetIntegerv(0x9193,&binding);assert((u32)binding==qb);assert(glGetError()==GL_NO_ERROR);
 int gpuRows=0;for(u32 i=0;i<g_s26ihCount;i++)if(g_s26ihRows[i].type==7){gpuRows++;assert(g_s26ihRows[i].end>=g_s26ihRows[i].begin);}assert(gpuRows>10);
 // Wrong context must not issue an end query for the old context.
 puts("stage context switch");g_s26ihGPUCalls=7;int t=s26ih_gpu_begin();HGLRC ctx2=wglCreateContext(dc);assert(wglMakeCurrent(dc,ctx2));s26ih_gpu_end(t);assert(t<0||g_s26ihGPU[t].pending==0);assert(glGetError()==0);
 wglMakeCurrent(dc,ctx);wglDeleteContext(ctx2);
 u64 a=s26ih_now();u32 before=g_s26ihCount;for(int k=0;k<20000;k++){u64 t=s26ih_now();s26ih_event(2,0,t,s26ih_now(),0,0);}u64 b=s26ih_now();
 printf("Recorder QPC+row mean %.3f us; actual GPU rows %d\n",double(b-a)*1e6/g_s26ihFrequency/(g_s26ihCount-before),gpuRows);
 while(g_s26ihCount<S26IH_CAP){u64 t=s26ih_now();s26ih_event(2,0,t,t,0,0);}s26ih_flush();assert(writes==1&&g_s26ihSaved&&!g_s26ihEnabled);s26ih_flush();assert(writes==1);
 FILE*f=fopen("hpl3vr_frame_timing_IH.bin","rb");assert(f);fseek(f,0,SEEK_END);assert(ftell(f)==24+S26IH_CAP*sizeof(S26IHRow));fclose(f);
 wglMakeCurrent(0,0);wglDeleteContext(ctx);ReleaseDC(w,dc);DestroyWindow(w);
 puts("PASS recorder OFF, gates, thread rejection, matrix copy, bounded save; real-driver GPU timestamps, query buffer restoration and context guard");
}
'''
cpp=B/'test_frame_timing_ih.cpp';cpp.write_text(head+'\n#include "../source/frame_timing_ih.inc"\n'+gpu+'\n#include "../source/frame_gpu_ih.inc"\n'+tail)
subprocess.run([sys.argv[1],'c++',str(cpp),'-O2','-lopengl32','-lgdi32','-o',str(B/'test_frame_timing_ih.exe')],check=True)
subprocess.run([str(B/'test_frame_timing_ih.exe')],cwd=B,check=True)
