#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>
#include <string.h>
#include <wchar.h>
#define CAP 2048
#define JI_TEXT 2048
#define LIMIT (4u*1024u*1024u)
typedef struct {ULONGLONG tick; char text[JI_TEXT];} Record;
static Record queue[CAP];
static SRWLOCK lock=SRWLOCK_INIT;
static unsigned readAt,count;
static volatile LONG enabled,stopping,active,dropped;
static HANDLE file=INVALID_HANDLE_VALUE,thread;
static wchar_t path[32768];
static ULONGLONG bytes;

static int diskError;
static char writeBuffer[65536];
static DWORD buffered;
static void flushBuffer(void){
 if(!buffered||diskError)return;
 DWORD done=0;
 if(!WriteFile(file,writeBuffer,buffered,&done,NULL)||done!=buffered){diskError=1;return;}
 bytes+=done;buffered=0;
}
static void rotate(void){
 wchar_t from[32768],to[32768];
 for(int i=3;i>=1;i--){
  if(i==1)wcscpy(from,path);else swprintf(from,32768,L"%ls.%d",path,i-1);
  swprintf(to,32768,L"%ls.%d",path,i);
  if(!(i==1?CopyFileW(from,to,FALSE):MoveFileExW(from,to,MOVEFILE_REPLACE_EXISTING))&&GetLastError()!=ERROR_FILE_NOT_FOUND){diskError=1;return;}
 }
 LARGE_INTEGER zero;zero.QuadPart=0;
 if(!SetFilePointerEx(file,zero,NULL,FILE_BEGIN)||!SetEndOfFile(file)){diskError=1;return;}
 bytes=0;
}
static void writeText(const char* s){
 if(diskError)return;
 DWORD n=(DWORD)strlen(s);
 if(bytes+buffered+n>LIMIT){flushBuffer();if(!diskError)rotate();}
 if(buffered+n>sizeof(writeBuffer))flushBuffer();
 if(diskError)return;
 memcpy(writeBuffer+buffered,s,n);buffered+=n;
}
static DWORD WINAPI worker(void* unused){
 (void)unused;SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_BELOW_NORMAL);
 while(!InterlockedCompareExchange(&active,0,0)&&!InterlockedCompareExchange(&stopping,0,0))Sleep(10);
 SYSTEMTIME now;GetSystemTime(&now);char line[JI_TEXT+160];
 snprintf(line,sizeof(line),"\n[SOMA VR 1.1.1-S26JI logging] UTC %04u-%02u-%02uT%02u:%02u:%02uZ pid=%lu; timestamps=GetTickCount64 milliseconds; bounded asynchronous logging; final queued records can be lost on forced termination\n",now.wYear,now.wMonth,now.wDay,now.wHour,now.wMinute,now.wSecond,(unsigned long)GetCurrentProcessId());
 if(active)writeText(line);
 char last[JI_TEXT]={0};unsigned repeats=0;ULONGLONG lastTime=0;
 for(;;){
  Record rec;int got=0;
  AcquireSRWLockExclusive(&lock);
  if(count){rec=queue[readAt];readAt=(readAt+1)%CAP;count--;got=1;}
  ReleaseSRWLockExclusive(&lock);
  if(got){
   if(!strcmp(last,rec.text)&&rec.tick-lastTime<1000){repeats++;continue;}
   if(repeats){snprintf(line,sizeof(line),"[log] previous message repeated %u additional times\n",repeats);writeText(line);repeats=0;}
   snprintf(line,sizeof(line),"[%llu ms] %s\n",(unsigned long long)rec.tick,rec.text);writeText(line);
   strcpy(last,rec.text);lastTime=rec.tick;continue;
  }
  if(repeats){snprintf(line,sizeof(line),"[log] previous message repeated %u additional times\n",repeats);writeText(line);repeats=0;}
  LONG lost=InterlockedExchange(&dropped,0);
  if(lost){snprintf(line,sizeof(line),"[log] %ld records dropped due to queue capacity/contention; gameplay thread was not blocked\n",(long)lost);writeText(line);}
  flushBuffer();
  if(stopping)break;
  Sleep(100);
 }
 return 0;
}
__declspec(dllexport) void SomaVrLog(const char* fmt,...){
 if(!InterlockedCompareExchange(&enabled,0,0)||!fmt)return;
 Record rec;rec.tick=GetTickCount64();va_list ap;va_start(ap,fmt);
 int n=vsnprintf(rec.text,sizeof(rec.text),fmt,ap);va_end(ap);
 if(n<0||(size_t)n>=sizeof(rec.text)){const char tail[]=" [truncated]";memcpy(rec.text+sizeof(rec.text)-sizeof(tail),tail,sizeof(tail));}
 if(!TryAcquireSRWLockExclusive(&lock)){InterlockedIncrement(&dropped);return;}
 if(count==CAP){ReleaseSRWLockExclusive(&lock);InterlockedIncrement(&dropped);return;}
 queue[(readAt+count)%CAP]=rec;count++;ReleaseSRWLockExclusive(&lock);
}
__declspec(dllexport) int SomaVrLogStart(const wchar_t* directory){
 if(thread||!directory||wcslen(directory)>32000)return 0;
 swprintf(path,32768,L"%ls\\hpl3vr.log",directory);
 /* Append access ensures existing legacy startup text cannot be overwritten. */
 file=CreateFileW(path,FILE_APPEND_DATA|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 if(file==INVALID_HANDLE_VALUE)return 0;
 LARGE_INTEGER size;GetFileSizeEx(file,&size);bytes=(ULONGLONG)size.QuadPart;
 SetFilePointerEx(file,(LARGE_INTEGER){.QuadPart=0},NULL,FILE_END);
 thread=CreateThread(NULL,0,worker,NULL,0,NULL);
 if(!thread){CloseHandle(file);file=INVALID_HANDLE_VALUE;return 0;}
 InterlockedExchange(&enabled,1);return 1;
}
__declspec(dllexport) void SomaVrLogActivate(void){InterlockedExchange(&active,1);}
__declspec(dllexport) int SomaVrLogStop(void){
 InterlockedExchange(&enabled,0);InterlockedExchange(&stopping,1);
 if(thread&&WaitForSingleObject(thread,2000)!=WAIT_OBJECT_0)return 0;
 if(thread){CloseHandle(thread);thread=NULL;}
 if(file!=INVALID_HANDLE_VALUE){CloseHandle(file);file=INVALID_HANDLE_VALUE;}
 return !diskError;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD why,LPVOID reserved){(void)reserved;if(why==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);}return TRUE;}

