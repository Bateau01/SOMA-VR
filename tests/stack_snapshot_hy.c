/* Test-only bounded thread-stack snapshot of the harness-owned child process.
   No heap dump, symbols downloaded, injections, or persistent target changes. */
#include <windows.h>
#include <tlhelp32.h>
#include <dbghelp.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){
 if(argc!=2)return 2;DWORD pid=(DWORD)strtoul(argv[1],0,10);
 HANDLE p=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ,FALSE,pid);
 if(!p)return 3;SymSetOptions(SYMOPT_DEFERRED_LOADS|SYMOPT_UNDNAME|SYMOPT_FAIL_CRITICAL_ERRORS);
 if(!SymInitialize(p,"",TRUE)){CloseHandle(p);return 4;}
 HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);THREADENTRY32 e={0};e.dwSize=sizeof(e);
 if(Thread32First(snap,&e))do{
  if(e.th32OwnerProcessID!=pid)continue;
  HANDLE t=OpenThread(THREAD_GET_CONTEXT|THREAD_SUSPEND_RESUME|THREAD_QUERY_INFORMATION,FALSE,e.th32ThreadID);
  if(!t)continue;if(SuspendThread(t)==(DWORD)-1){CloseHandle(t);continue;}
  CONTEXT c={0};c.ContextFlags=CONTEXT_FULL;
  if(GetThreadContext(t,&c)){
   STACKFRAME64 f={0};f.AddrPC.Offset=c.Rip;f.AddrPC.Mode=AddrModeFlat;f.AddrFrame.Offset=c.Rbp;f.AddrFrame.Mode=AddrModeFlat;f.AddrStack.Offset=c.Rsp;f.AddrStack.Mode=AddrModeFlat;
   printf("thread %lu\n",e.th32ThreadID);
   for(int i=0;i<24;i++){
    IMAGEHLP_MODULE64 m={0};m.SizeOfStruct=sizeof(m);
    if(SymGetModuleInfo64(p,f.AddrPC.Offset,&m))printf("  %s + 0x%llx\n",m.ModuleName,(unsigned long long)(f.AddrPC.Offset-m.BaseOfImage));
    else printf("  0x%llx\n",(unsigned long long)f.AddrPC.Offset);
    if(!StackWalk64(IMAGE_FILE_MACHINE_AMD64,p,t,&f,&c,NULL,SymFunctionTableAccess64,SymGetModuleBase64,NULL))break;
   }
  }
  ResumeThread(t);CloseHandle(t);
 }while(Thread32Next(snap,&e));
 CloseHandle(snap);SymCleanup(p);CloseHandle(p);return 0;
}
