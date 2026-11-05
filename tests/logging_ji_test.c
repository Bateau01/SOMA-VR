#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <wchar.h>
typedef int (*Start)(const wchar_t*);typedef void (*Log)(const char*,...);typedef void (*Void)(void);typedef int (*Stop)(void);
static Log logfn;
static DWORD WINAPI flood(void*p){int id=(int)(intptr_t)p;for(int i=0;i<50000;i++)logfn("thread %d message %d",id,i);return 0;}
int wmain(int argc,wchar_t**argv){
 if(argc!=4)return 2;HMODULE h=LoadLibraryW(argv[1]);if(!h)return 3;
 Start start=(Start)GetProcAddress(h,"SomaVrLogStart");logfn=(Log)GetProcAddress(h,"SomaVrLog");Void activate=(Void)GetProcAddress(h,"SomaVrLogActivate");Stop stop=(Stop)GetProcAddress(h,"SomaVrLogStop");
 CreateDirectoryW(argv[2],NULL);wchar_t legacyPath[32768];swprintf(legacyPath,32768,L"%ls\\hpl3vr.log",argv[2]);FILE*legacy=_wfopen(legacyPath,L"w");if(!legacy)return 7;fprintf(legacy,"LEGACY STARTUP\n");fflush(legacy);if(!start(argv[2]))return 4;activate();
 LARGE_INTEGER freq,t0,t1;QueryPerformanceFrequency(&freq);
 if(!wcscmp(argv[3],L"flood")){HANDLE t[4];QueryPerformanceCounter(&t0);for(int i=0;i<4;i++)t[i]=CreateThread(NULL,0,flood,(void*)(intptr_t)i,0,NULL);WaitForMultipleObjects(4,t,TRUE,INFINITE);QueryPerformanceCounter(&t1);for(int i=0;i<4;i++)CloseHandle(t[i]);printf("flood 200000 producer calls wall_ms=%.3f\n",1000.0*(t1.QuadPart-t0.QuadPart)/freq.QuadPart);}
 else if(!wcscmp(argv[3],L"rotate")){char text[1501];memset(text,'x',1500);text[1500]=0;for(int i=0;i<18000;i++){logfn("rotation %d %s",i,text);if(i%100==0)Sleep(15);}logfn("FINAL SENTINEL");Sleep(300);}
 else {
  QueryPerformanceCounter(&t0);for(int i=0;i<1000;i++)logfn("producer timing message %d value %.4f",i,1.2345);QueryPerformanceCounter(&t1);printf("async producer 1000 calls ms=%.3f\n",1000.0*(t1.QuadPart-t0.QuadPart)/freq.QuadPart);
  Sleep(200);wchar_t p[32768];swprintf(p,32768,L"%ls\\baseline.log",argv[2]);FILE*f=_wfopen(p,L"w");if(!f)return 6;
  QueryPerformanceCounter(&t0);for(int i=0;i<1000;i++){fprintf(f,"producer timing message %d value %.4f\n",i,1.2345);fflush(f);}QueryPerformanceCounter(&t1);fclose(f);printf("synchronous fprintf/fflush 1000 calls ms=%.3f\n",1000.0*(t1.QuadPart-t0.QuadPart)/freq.QuadPart);
  for(int i=0;i<500;i++)logfn("duplicate message");Sleep(200);logfn("FINAL SENTINEL");Sleep(200);
 }
 int ok=stop();printf("stop=%d\n",ok);fclose(legacy);return ok?0:5;
}
