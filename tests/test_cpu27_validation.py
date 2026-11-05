from pathlib import Path
import subprocess,sys,json,re
r=Path(__file__).resolve().parents[1];b=r/'build/cpu27-unit';b.mkdir(exist_ok=True)
s=(r/'source/s26n.c').read_text()
old=re.search(r'static i32 h5755ct_noncharacter_body_eligible\(.*?\n}',s,re.S).group()
candidate=old.replace('h5755ct_noncharacter_body_eligible','candidate').replace('!w||!h20_mem_readable((u8*)w+0x2e0,1)||!h20_mem_readable((u8*)w+0x258,4)||!h20_mem_readable((u8*)w+0x240,4)||!h20_mem_readable((u8*)w+0x0e4,1)','!cpu27_wrapper_readable(w)')
readable=re.search(r'static i32 h20_mem_readable\(const void\* p,u64 n\).*?\n',s).group()
pre=r'''
#include <windows.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
typedef MEMORY_BASIC_INFORMATION H20MBI;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);ExitProcess(1);}}while(0)
static u8 bytes[8192];static int realQuery,queries,split,state=MEM_COMMIT,protect=PAGE_READWRITE,failAt=-1;
static i32 h20_mem_query(const void*p,H20MBI*m){queries++;if(realQuery)return VirtualQuery(p,m,sizeof(*m))>=40;u64 off=(u64)p-(u64)bytes;if((int)off==failAt)return 0;memset(m,0,sizeof(*m));m->BaseAddress=bytes+(off<(u64)split?0:split);m->RegionSize=off<(u64)split?split:sizeof(bytes)-split;m->State=state;m->Protect=protect;return 1;}
static void*userdata(const void*p){return (void*)p;}static void*(*p_h14GetUserData)(const void*)=userdata;
'''
post=r'''
int main(){unsigned cases=0;memset(bytes,1,sizeof(bytes));
for(split=0;split<800;split++)for(int mode=0;mode<12;mode++){
state=mode==1?MEM_RESERVE:MEM_COMMIT;protect=mode==2?PAGE_NOACCESS:mode==3?PAGE_GUARD|PAGE_READWRITE:PAGE_READWRITE;
failAt=mode==4?0x2e0:mode==5?0x258:mode==6?0x240:mode==7?0xe4:-1;
/* Query failures are checked separately with distinct regions. */
if(failAt>=0)continue;
bytes[0xe4]=mode==8?0:1;bytes[0x249]=mode==9?1:0;bytes[0x2e0]=mode==10?0:1;*(int*)(bytes+0x258)=mode==11?-1:0;*(u32*)(bytes+0x240)=mode==0?0:1;
int a=h5755ct_noncharacter_body_eligible(0,bytes),c=candidate(0,bytes);C(a==c);cases++;
}
state=MEM_COMMIT;protect=PAGE_READWRITE;split=0;failAt=0x2e0;C(candidate(0,bytes)==1&&h5755ct_noncharacter_body_eligible(0,bytes)==1);cases++;
split=0x200;failAt=0xe4;C(candidate(0,bytes)==1&&h5755ct_noncharacter_body_eligible(0,bytes)==1);cases++;
split=0x280;failAt=0x258;C(candidate(0,bytes)==1&&h5755ct_noncharacter_body_eligible(0,bytes)==1);cases++;
split=0x250;failAt=0x240;C(candidate(0,bytes)==1&&h5755ct_noncharacter_body_eligible(0,bytes)==1);cases++;failAt=-1;
C(candidate(0,0)==1);p_h14GetUserData=0;C(candidate(0,bytes)==1);p_h14GetUserData=userdata;
realQuery=1;u8*p=VirtualAlloc(0,8192,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);C(p);memset(p,1,8192);
DWORD prior;C(VirtualProtect(p,4096,PAGE_READONLY,&prior));
for(int off=3300;off<4100;off++){C(h5755ct_noncharacter_body_eligible(0,p+off)==candidate(0,p+off));cases++;}
C(VirtualProtect(p,4096,PAGE_NOACCESS,&prior));
for(int off=3300;off<4100;off++){C(h5755ct_noncharacter_body_eligible(0,p+off)==candidate(0,p+off));cases++;}
C(VirtualProtect(p,4096,PAGE_READWRITE,&prior));
LARGE_INTEGER f,a,z;QueryPerformanceFrequency(&f);volatile int result=0;double elapsed[2];int counts[2];
for(int mode=0;mode<2;mode++){queries=0;QueryPerformanceCounter(&a);for(int i=0;i<200000;i++){p[0xe4]=(u8)(i&1);result+=mode?candidate(0,p):h5755ct_noncharacter_body_eligible(0,p);}QueryPerformanceCounter(&z);elapsed[mode]=1000.0*(z.QuadPart-a.QuadPart)/f.QuadPart;counts[mode]=queries;}
C(counts[0]==800000&&counts[1]==200000);VirtualFree(p,0,MEM_RELEASE);printf("PASS %u boundary/permission cases; live flags; query count %d -> %d; elapsed %.3f -> %.3f ms; checksum %d\n",cases,counts[0],counts[1],elapsed[0],elapsed[1],result);}
'''
(b/'test.c').write_text(pre+readable+(r/'tests/cpu27_validation.inc').read_text()+old+candidate+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=30);print(x.stdout+x.stderr)
(r/'audit/cpu27-unit.json').write_text(json.dumps(dict(scope='Actual original/candidate predicate, mock region boundaries and real Windows VirtualQuery; not gameplay proof',exit=x.returncode,output=x.stdout+x.stderr),indent=2));raise SystemExit(x.returncode)
