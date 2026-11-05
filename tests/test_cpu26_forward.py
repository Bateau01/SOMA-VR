from pathlib import Path
import subprocess,sys,json,re
r=Path(__file__).resolve().parents[1];b=r/'build/cpu26-unit';b.mkdir(exist_ok=True)
core=(r/'tests/cpu26_callbacks.inc').read_text().split('static void cpu26_install(void)')[0]
wrapper=re.search(r'static i32 __attribute__\(\(ms_abi\)\) h530_hand_overlap_filter\(const void\*m,.*?\n', (r/'build/movement/test.c').read_text()).group()
wrapper+=re.search(r'static u64 __attribute__\(\(ms_abi\)\) s26_overlap_detour\(const void\*m,.*?\n', (r/'build/movement/test.c').read_text()).group()
pre=r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x)){printf("FAIL line %d\n",__LINE__);ExitProcess(1);}}while(0)
#define cpuThreadId GetCurrentThreadId
#define ext_Log(...) ((void)0)
static u32 cpu14Saved;static u64 sums[3],calls[3],maxima[3],invalid;
static int cpuCounter(u64*p){return QueryPerformanceCounter((LARGE_INTEGER*)p);}
static u64 cpu_detail_begin(void){return 1;}
static void cpu14_event(u32 k,u32 d,u64 a,u64 e,u64 id){(void)a;(void)e;if(k==33)sums[d]=id;if(k==35)calls[d]=id;if(k==36)maxima[d]=id;if(k==34)invalid=id;}
static volatile LONG observed[3];
static u64 __attribute__((ms_abi)) cpu26_overlap_body(const void*m,const void*a,const void*b,i32 thread){C(m==(void*)11&&a==(void*)22&&b==(void*)33);InterlockedIncrement(&observed[0]);return thread&1?0x123400000007ULL:0;}
static void __attribute__((ms_abi)) originalContact(const void*j,float dt,i32 thread){C(j==(void*)44&&dt==.125f);(void)thread;InterlockedIncrement(&observed[1]);}
static i32 cpu26_hand_body(const void*m,const void*a,const void*b,i32 thread){C(m==(void*)11&&a==(void*)22&&b==(void*)33);InterlockedIncrement(&observed[2]);return thread&1?0:1;}
static i32 __attribute__((ms_abi)) threadCount(const void*w){C(w==(void*)99);return 8;}
'''
post=r'''
static DWORD WINAPI worker(void*p){i32 t=(i32)(INT_PTR)p;for(int i=0;i<10000;i++){C(s26_overlap_detour((void*)11,(void*)22,(void*)33,t)==(t&1?0x123400000007ULL:0));cpu26_contact((void*)44,.125f,t);C(h530_hand_overlap_filter((void*)11,(void*)22,(void*)33,t)==(t&1?0:1));}return 0;}
int main(){cpu26ContactOriginal=originalContact;cpu26ThreadCount=threadCount;
C(s26_overlap_detour((void*)11,(void*)22,(void*)33,1)==0x123400000007ULL);C(observed[0]==1);
cpu26_before((void*)99);C(cpu26Active==1);
HANDLE h[9];for(int i=0;i<9;i++)h[i]=CreateThread(0,0,worker,(void*)(INT_PTR)i,0,0);C(WaitForMultipleObjects(9,h,TRUE,10000)==WAIT_OBJECT_0);for(int i=0;i<9;i++)CloseHandle(h[i]);
C(s26_overlap_detour((void*)11,(void*)22,(void*)33,-1)==0x123400000007ULL);cpu26_contact((void*)44,.125f,64);C(h530_hand_overlap_filter((void*)11,(void*)22,(void*)33,64)==1);
cpu26_contact((void*)44,.125f,0);cpu26_after(1,2);C(!cpu26Active&&invalid==0);for(int i=0;i<3;i++){C(calls[i]==90001+(i==1)&&sums[i]>0&&maxima[i]>0);C(observed[i]==90001+(i==0)+(i==1));}
for(int i=0;i<3;i++){cpu26_before((void*)99);C(!cpu26Active);}cpu26_before((void*)99);C(cpu26Active);cpu26_after(1,2);for(int i=0;i<3;i++)C(calls[i]==0);
cpu26Active=1;cpu26Invalid=0;for(int i=0;i<64;i++)cpu26Owners[i]=0xffffffff;LONG prior=observed[1];cpu26_contact((void*)44,.125f,0);C(cpu26Invalid==1&&observed[1]==prior+1);cpu26Active=0;cpu14Saved=1;cpu26_before((void*)99);C(!cpu26Active);puts("PASS exact forwarding/rejection values;270000 concurrent callbacks on9actual worker threads; arbitrary native indices forwarded; capture off and1-in4sampling");}
'''
(b/'test.c').write_text(pre+core+wrapper+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=30);print(x.stdout+x.stderr)
(r/'audit/cpu26-unit.json').write_text(json.dumps(dict(scope='Compiled actual observer and generated hand wrapper with mock original callbacks; not native collision outcome proof',exit=x.returncode,output=x.stdout+x.stderr),indent=2));raise SystemExit(x.returncode)
