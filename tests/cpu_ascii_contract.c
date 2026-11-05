#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;typedef uint32_t u32;typedef uint64_t u64;typedef int32_t i32;
typedef MEMORY_BASIC_INFORMATION H20MBI;
static u64 queries;
static i32 h20_mem_query(const void*p,H20MBI*m){queries++;if(!p||!m)return 0;memset(m,0,sizeof(*m));return VirtualQuery(p,m,sizeof(*m))>=40;}
static i32 h20_mem_readable(const void*p,u64 n){H20MBI m;if(!h20_mem_query(p,&m)||m.State!=0x1000u)return 0;u32 pr=m.Protect;if((pr&0x100u)||(pr&0xffu)==1)return 0;u64 a=(u64)p,b=(u64)m.BaseAddress,e=b+m.RegionSize;return a>=b&&a+n>=a&&a+n<=e;}
#define ext_Log(...) ((void)0)
#define CPU_STRING_SPANS 1
#include "../source/cpu_ascii_spans.inc"
#include "fixtures/cpu_ascii_baseline.inc"
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
static u32 cases;
static void compare(const void*p,u32 cap){
 char a[256],b[256];memset(a,0x5a,sizeof(a));memset(b,0x5a,sizeof(b));
 i32 x=cpu_ascii_baseline(p,a,cap),y=h21_copy_ascii(p,b,cap);
 CHECK(x==y&&memcmp(a,b,sizeof(a))==0);cases++;
}
int main(void){
 SYSTEM_INFO info;GetSystemInfo(&info);u32 page=info.dwPageSize;
 u8*mem=VirtualAlloc(0,page*3,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);CHECK(mem);
 u32 seed=7;
 for(u32 len=0;len<90;len++)for(u32 cap=0;cap<100;cap++)for(u32 mode=0;mode<4;mode++){
  memset(mem,'a',128);for(u32 j=0;j<len;j++){seed=seed*1664525+1013904223;mem[j]=(mode==0?'a':mode==1?'1':mode==2?(u8)(32+seed%95):(u8)(seed>>24));}mem[len]=0;compare(mem,cap);
 }
 for(u32 cap=0;cap<100;cap++)compare(0,cap);
 CHECK(!h21_copy_ascii(mem,0,96));
 for(u32 mode=0;mode<3;mode++){
  DWORD old;CHECK(VirtualProtect(mem,page*3,PAGE_READWRITE,&old));memset(mem,'A',page*3);mem[page+35]=0;
  DWORD protection=mode==0?PAGE_NOACCESS:mode==1?PAGE_READONLY:PAGE_READWRITE|PAGE_GUARD;
  CHECK(VirtualProtect(mem+page,page,protection,&old));
  for(u32 offset=1;offset<70;offset++)for(u32 cap=6;cap<100;cap++)compare(mem+page-offset,cap);
  compare(mem+page,96);if(mode==2){H20MBI m;VirtualQuery(mem+page,&m,sizeof(m));CHECK(m.Protect&PAGE_GUARD);}
 }
 DWORD old;VirtualProtect(mem,page*3,PAGE_READWRITE,&old);strcpy((char*)mem,".?AVcLuxProp_Interact_Grab@@");
 char out[96];LARGE_INTEGER freq,a,b;QueryPerformanceFrequency(&freq);volatile u32 total=0;
 for(int method=0;method<2;method++){
  queries=0;QueryPerformanceCounter(&a);
  for(int i=0;i<20000;i++)total+=method?h21_copy_ascii(mem,out,96):cpu_ascii_baseline(mem,out,96);
  QueryPerformanceCounter(&b);
  printf("method %s calls 20000 queries %llu elapsed_ms %.3f\n",method?"spans":"baseline",(unsigned long long)queries,(double)(b.QuadPart-a.QuadPart)*1000/freq.QuadPart);
 }
 CHECK(total==40000);VirtualFree(mem,0,MEM_RELEASE);printf("PASS %u equivalent outcomes and full buffers; real Windows page/guard boundary cases\n",cases);return 0;
}
