/* Test-only observer: request window MSAA before SDL creates its pixel format,
   then inspect existing complete FBOs on their context thread. Never shipped. */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
static void*(*createWindow)(const char*,int,int,int,int,unsigned);
static int(*setAttribute)(int,int);
static BOOL(WINAPI *swap)(HDC);
static unsigned swaps;static int samples=4;
static void* window(const char*t,int x,int y,int w,int h,unsigned f){
 setAttribute(13,samples>0);setAttribute(14,samples);
 FILE*o=fopen("msaa_probe.txt","a");if(o){fprintf(o,"REQUEST samples=%d window=%dx%d\n",samples,w,h);fclose(o);}return createWindow(t,x,y,w,h,f);
}
static BOOL WINAPI inspect(HDC dc){
 ++swaps;
 if(swaps==60||swaps==300||swaps==600){
  void(APIENTRY *bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
  GLboolean(APIENTRY *is)(GLuint)=(void*)wglGetProcAddress("glIsFramebuffer");
  GLenum(APIENTRY *status)(GLenum)=(void*)wglGetProcAddress("glCheckFramebufferStatus");
  if(bind&&is&&status){GLint draw=0,read=0;glGetIntegerv(0x8ca6,&draw);glGetIntegerv(0x8caa,&read);
   FILE*o=fopen("msaa_probe.txt","a");
   for(unsigned id=0;id<512;id++)if(id==0||is(id)){
    bind(0x8ca9,id);if(status(0x8ca9)==0x8cd5){GLint s=0,b=0;glGetIntegerv(0x80a9,&s);glGetIntegerv(0x80a8,&b);if(o)fprintf(o,"SWAP=%u FBO=%u samples=%d buffers=%d\n",swaps,id,s,b);}
   }
   bind(0x8ca9,draw);bind(0x8ca8,read);if(o)fclose(o);
  }
 }
 return swap(dc);
}
static int hook(HMODULE m,const char*key,void*fn,void**oldfn){
 unsigned char*b=(void*)m;IMAGE_DOS_HEADER*d=(void*)b;IMAGE_NT_HEADERS*n=(void*)(b+d->e_lfanew);
 IMAGE_IMPORT_DESCRIPTOR*i=(void*)(b+n->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress);
 for(;i->Name;i++){
  IMAGE_THUNK_DATA*t=(void*)(b+i->OriginalFirstThunk),*a=(void*)(b+i->FirstThunk);
  for(;t->u1.AddressOfData;t++,a++)if(!IMAGE_SNAP_BY_ORDINAL(t->u1.Ordinal)){
   IMAGE_IMPORT_BY_NAME*name=(void*)(b+t->u1.AddressOfData);
   if(!strcmp((char*)name->Name,key)){DWORD p;if(!VirtualProtect(&a->u1.Function,sizeof(void*),PAGE_READWRITE,&p))return 0;*oldfn=(void*)a->u1.Function;InterlockedExchangePointer((void*volatile*)&a->u1.Function,fn);VirtualProtect(&a->u1.Function,sizeof(void*),p,&p);return 1;}
  }
 }return 0;
}
static DWORD WINAPI install(void*u){
 FILE*f=fopen("msaa_request.txt","r");if(f){fscanf(f,"%d",&samples);fclose(f);}
 HMODULE s=GetModuleHandleA("SDL2.dll");if(!s)return 1;setAttribute=(void*)GetProcAddress(s,"SDL_GL_SetAttribute");
 int a=hook(GetModuleHandleA(NULL),"SDL_CreateWindow",window,(void**)&createWindow);
 int b=hook(s,"SwapBuffers",inspect,(void**)&swap);
 f=fopen("msaa_ready.txt","w");if(f){fprintf(f,"%d %d",a,b);fclose(f);}return 0;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,void*p){if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);HANDLE t=CreateThread(NULL,0,install,NULL,0,NULL);if(t)CloseHandle(t);}return TRUE;}
