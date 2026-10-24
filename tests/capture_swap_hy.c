/* Isolated placement fixture only. Never shipped. Bounded async readback;
   one CPU slot, nonblocking fence poll, disk IO only on a worker.
   30 Hz presentation cap is for static screenshot fixtures, NOT timing tests. */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define PACK 0x88EB
#define PACK_BINDING 0x88ED
#define STREAM_READ 0x88E1
static void (APIENTRY *gen)(GLsizei,GLuint*);
static void (APIENTRY *bindBuffer)(GLenum,GLuint);
static void (APIENTRY *data)(GLenum,intptr_t,const void*,GLenum);
static void* (APIENTRY *map)(GLenum,GLenum);
static GLboolean (APIENTRY *unmap)(GLenum);
static void* (APIENTRY *fence)(GLenum,GLbitfield);
static GLenum (APIENTRY *poll)(void*,GLbitfield,uint64_t);
static void (APIENTRY *delSync)(void*);
static BOOL (WINAPI *original)(HDC);
static HGLRC owner;
static GLuint pbo;
static void* pending;
static int w,h,ready,disabled;
static DWORD lastIssue,lastSwap;
static unsigned frames;
static volatile LONG slot;
static unsigned char pixels[1280*720*3];
static int outW,outH;
static unsigned outFrame;
static HANDLE wake;
static DWORD WINAPI writer(void*unused){
    SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_BELOW_NORMAL);
    for(;;){
        WaitForSingleObject(wake,INFINITE);
        if(InterlockedCompareExchange(&slot,2,1)!=1)continue;
        char name[80];sprintf(name,"hy_frame_%05u.ppm",outFrame%12);
        FILE*f=fopen(name,"wb");
        if(f){fprintf(f,"P6\n%d %d\n255\n",outW,outH);
            for(int y=outH-1;y>=0;--y)fwrite(pixels+(size_t)y*outW*3,1,(size_t)outW*3,f);
            fclose(f);}
        InterlockedExchange(&slot,0);
    }
}
static int load(void){
#define LOAD(name,symbol) name=(void*)wglGetProcAddress(symbol);if((uintptr_t)name<=3||(intptr_t)name==-1)return 0
    LOAD(gen,"glGenBuffers");LOAD(bindBuffer,"glBindBuffer");LOAD(data,"glBufferData");
    LOAD(map,"glMapBuffer");LOAD(unmap,"glUnmapBuffer");
    LOAD(fence,"glFenceSync");LOAD(poll,"glClientWaitSync");LOAD(delSync,"glDeleteSync");
#undef LOAD
    owner=wglGetCurrentContext();gen(1,&pbo);return pbo!=0;
}
static BOOL WINAPI capture(HDC dc){
    DWORD now=GetTickCount();
    if(lastSwap && now-lastSwap<33)Sleep(33-(now-lastSwap));
    lastSwap=GetTickCount();
    if(!disabled && wglGetCurrentContext()){
        if(!ready){ready=load();if(!ready)disabled=1;}
        if(ready && owner==wglGetCurrentContext()){
            GLint old;glGetIntegerv(PACK_BINDING,&old);
            if(pending){
                GLenum status=poll(pending,0,0); /* NEVER wait for the GPU */
                if(status==0x911A||status==0x911C){
                    if(InterlockedCompareExchange(&slot,0,0)==0){
                        bindBuffer(PACK,pbo);void*p=map(PACK,0x88B8);
                        if(p){memcpy(pixels,p,(size_t)w*h*3);GLboolean valid=unmap(PACK);
                            if(valid){outW=w;outH=h;outFrame=frames;InterlockedExchange(&slot,1);SetEvent(wake);}}
                        bindBuffer(PACK,old);
                    }
                    delSync(pending);pending=NULL;
                }else if(status==0x911D||GetTickCount()-lastIssue>3000){disabled=1;}
            }
            if(!pending && !disabled && frames<40 && GetTickCount()-lastIssue>1500 && InterlockedCompareExchange(&slot,0,0)==0){
                GLint v[4],read,pack,row,skipRows,skipPixels;glGetIntegerv(GL_VIEWPORT,v);
                if(v[0]==0&&v[1]==0&&v[2]>0&&v[3]>0&&v[2]<=1280&&v[3]<=720){
                    w=v[2];h=v[3];glGetIntegerv(GL_READ_BUFFER,&read);glGetIntegerv(GL_PACK_ALIGNMENT,&pack);
                    glGetIntegerv(GL_PACK_ROW_LENGTH,&row);glGetIntegerv(GL_PACK_SKIP_ROWS,&skipRows);glGetIntegerv(GL_PACK_SKIP_PIXELS,&skipPixels);
                    bindBuffer(PACK,pbo);data(PACK,(intptr_t)w*h*3,NULL,STREAM_READ);
                    glReadBuffer(GL_FRONT);glPixelStorei(GL_PACK_ALIGNMENT,1);glPixelStorei(GL_PACK_ROW_LENGTH,0);glPixelStorei(GL_PACK_SKIP_ROWS,0);glPixelStorei(GL_PACK_SKIP_PIXELS,0);
                    glReadPixels(0,0,w,h,GL_RGB,GL_UNSIGNED_BYTE,0);
                    pending=fence(0x9117,0);glFlush();
                    glReadBuffer(read);glPixelStorei(GL_PACK_ALIGNMENT,pack);glPixelStorei(GL_PACK_ROW_LENGTH,row);glPixelStorei(GL_PACK_SKIP_ROWS,skipRows);glPixelStorei(GL_PACK_SKIP_PIXELS,skipPixels);bindBuffer(PACK,old);
                    lastIssue=GetTickCount();frames++;if(!pending)disabled=1;
                }
            }
        }
    }
    return original(dc);
}
static DWORD WINAPI install(void*unused){
    wake=CreateEventW(NULL,FALSE,FALSE,NULL);if(!wake)return 3;
    HANDLE worker=CreateThread(NULL,0,writer,NULL,0,NULL);if(!worker)return 4;CloseHandle(worker);
    HMODULE m=GetModuleHandleA("SDL2.dll");if(!m)return 1;
    unsigned char*b=(unsigned char*)m;IMAGE_DOS_HEADER*d=(void*)b;IMAGE_NT_HEADERS*n=(void*)(b+d->e_lfanew);
    IMAGE_IMPORT_DESCRIPTOR*i=(void*)(b+n->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress);
    for(;i->Name;i++){
        IMAGE_THUNK_DATA*t=(void*)(b+i->OriginalFirstThunk),*a=(void*)(b+i->FirstThunk);
        for(;t->u1.AddressOfData;t++,a++)if(!IMAGE_SNAP_BY_ORDINAL(t->u1.Ordinal)){
            IMAGE_IMPORT_BY_NAME*name=(void*)(b+t->u1.AddressOfData);
            if(!strcmp((char*)name->Name,"SwapBuffers")){
                DWORD old;if(!VirtualProtect(&a->u1.Function,sizeof(void*),PAGE_READWRITE,&old))return 5;
                original=(void*)a->u1.Function;InterlockedExchangePointer((void*volatile*)&a->u1.Function,capture);
                VirtualProtect(&a->u1.Function,sizeof(void*),old,&old);return 0;
            }
        }
    }return 2;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,void*reserved){if(reason==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);HANDLE t=CreateThread(NULL,0,install,NULL,0,NULL);if(t)CloseHandle(t);}return TRUE;}

