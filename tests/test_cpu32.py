from pathlib import Path
import re,subprocess,sys,json
r=Path(__file__).resolve().parents[1];b=r/'build/cpu32-unit';b.mkdir(exist_ok=True)
prof=(r/'build/movement/cpu_work_profile.inc').read_text()
core=prof[prof.index('typedef struct {u64 calls,ticks,max;} CPU26Slot;'):prof.index('static void cpu26_install(void){')]
pairs=(r/'tests/cpu32_pairs.inc').read_text()
wrapper=re.search(r'static i32 __attribute__\(\(ms_abi\)\) h530_hand_overlap_filter\(const void\*m,.*?\n',(r/'build/movement/test.c').read_text()).group()
pre=r'''
#include <windows.h>
#include <stdio.h>
typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);ExitProcess(1);}}while(0)
#define cpuThreadId GetCurrentThreadId
#define ext_Log(...) ((void)0)
static u32 cpu14Saved;static u64 cpuFreq=10000000,recordedCalls,recordedLost;
static volatile LONG originalCalls;
static int cpuCounter(u64*p){return QueryPerformanceCounter((LARGE_INTEGER*)p);}
static u64 cpu_detail_begin(void){return 1;}
static void cpu14_event(u32 k,u32 d,u64 a,u64 b,u64 id){(void)d;(void)a;(void)b;if(k==40)recordedLost=id;if(k==41)recordedCalls=id;}
static i32 __attribute__((ms_abi)) threadCount(const void*w){C(w==(void*)99);return 8;}
static i32 cpu26_hand_body(const void*m,const void*a,const void*b,i32 t){C(m==(void*)11&&a==(void*)22&&b==(void*)33);InterlockedIncrement(&originalCalls);return t&1?-7:0;}
static void cpu32_reset(void);static void cpu32_pair(u64,u64,const void*,const void*,i32);static void cpu32_after(u64,u64);
'''
post=r'''
static DWORD WINAPI worker(void*p){i32 t=(i32)(INT_PTR)p;for(int i=0;i<10000;i++)C(h530_hand_overlap_filter((void*)11,(void*)22,(void*)33,t)==(t&1?-7:0));return 0;}
int main(){cpu26ThreadCount=threadCount;
C(h530_hand_overlap_filter((void*)11,(void*)22,(void*)33,1)==-7);
cpu26_before((void*)99);C(cpu26Active);HANDLE hs[9];for(int i=0;i<9;i++)hs[i]=CreateThread(0,0,worker,(void*)(INT_PTR)i,0,0);
C(WaitForMultipleObjects(9,hs,TRUE,10000)==WAIT_OBJECT_0);for(int i=0;i<9;i++)CloseHandle(hs[i]);
u64 rejected=0,count=0;for(int i=0;i<64;i++)for(int j=0;j<128;j++){CPU32Pair*p=&cpu32Pairs[i][j];count+=p->calls;rejected+=p->rejected;}
C(count==90000&&rejected==50000&&originalCalls==90001);cpu26_after(1,2);cpu32_after(1,2);C(recordedCalls==90000&&recordedLost==0);
for(int i=0;i<3;i++){cpu26_before((void*)99);C(!cpu26Active);}cpu26_before((void*)99);C(cpu26Active);
for(int i=0;i<129;i++)cpu32_pair(64,3,(void*)(INT_PTR)(i+1),(void*)33,1);
C(cpu32Lost[0]==1);cpu32_after(1,2);C(recordedCalls==128&&recordedLost==1);
cpu32_reset();cpu32_pair(64,3,(void*)1,(void*)2,0);cpu32_pair(64,4,(void*)2,(void*)1,1);cpu32_after(1,2);C(recordedCalls==2&&recordedLost==0);
cpu26Active=0;cpu14Saved=1;cpu26_before((void*)99);C(!cpu26Active);
C(h530_hand_overlap_filter((void*)11,(void*)22,(void*)33,0)==0&&originalCalls==90002);
puts("PASS 90000 concurrent callbacks; exact argument/result forwarding; rejection counts; independent OS-thread buckets; sampling OFF; reset and saturation; opaque ordered pairs");}
'''
(b/'test.c').write_text(pre+core+pairs+wrapper+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=30);print(x.stdout+x.stderr)
(r/'audit/cpu32-unit.json').write_text(json.dumps(dict(scope='Actual generated observer/wrapper, mocked original callback, nine Windows threads. Not native gameplay certification.',exit=x.returncode,output=x.stdout+x.stderr),indent=2));raise SystemExit(x.returncode)
