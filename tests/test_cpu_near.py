from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text()
def fn(start):
 a=s.index(start);b=s.index('{',a);n=1;b+=1
 while n:n+=(s[b]=='{')-(s[b]=='}');b+=1
 return s[a:b]
code=r'''
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
#define CPU_NEAR_TYPES 1
#define CPU_WORK_PROFILE 1
#define H504_NEAR_MAX 32
#define H504_NEAR_HALF .4f
static u32 cpuNearBaseline,g_h504NearScans[2],g_h504NearBodies[2],decodes;
typedef struct {void* vt;const char* name;int invalid;} Owner;
typedef struct {unsigned char bytes[0x300];int trigger,rocker,proxy,self,area;} Body;
static Body bodies[100];static Owner owners[100];static void* types[100];static const void* entries[220];static int entryCount;
static int h20_mem_readable(const void*p,int n){(void)n;if(!p)return 0;for(int i=0;i<100;i++)if(p==&owners[i])return !owners[i].invalid;return 1;}
static int h22_rtti_name(const void*p,char*out,u32 cap){decodes++;Owner*o=(Owner*)p;if(!o||o->invalid||!o->name)return 0;snprintf(out,cap,"%s",o->name);return 1;}
static int h25_str_contains(const char*a,const char*b){return strstr(a,b)!=0;}
static void* userdata(const void*p){return (void*)p;}
#define p_h14GetUserData userdata
static int s26y_rocker_body(const void*p){return p&&((Body*)p)->rocker;}
static int h35_is_hand_proxy_body(const void*p){return ((Body*)p)->proxy;}
static const void* collision(const void*p){return p;}
#define p_h14GetCollision collision
static int trigger(const void*p){return ((Body*)p)->trigger;}
#define p_h14IsTrigger trigger
static int h530_self_body_kind(const void*p){return ((Body*)p)->self;}
static int h540_nonphysical_area_body(const void*p){return ((Body*)p)->area;}
static void zero_bytes(void*p,size_t n){memset(p,0,n);}
static float h9_abs(float v){return fabsf(v);}
static float h5755ea_world_units_per_meter(void){return 1;}
typedef struct {const void* body[H504_NEAR_MAX];int count;} H504Near;
static void enumerate(const void*w,const float*lo,const float*hi,void(__attribute__((ms_abi))*cb)(const void*,void*),void*u){(void)w;(void)lo;(void)hi;for(int i=0;i<entryCount;i++)cb(entries[i],u);}
#define p_h14WorldAABB enumerate
'''+fn('static i32 h47_self_occluder_kind(')+'\n'+(r/'source/scan_type_cache_ep.inc').read_text()+'''\ntypedef struct {H504Near* near;H530SelfScan types;} CPUNearScope;\n'''+fn('static void __attribute__((ms_abi)) h504_near_cb(')+'\n'+fn('static void h504_collect_near(')+r'''
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL line %d case %d\n",__LINE__,test);return 1;}}while(0)
int main(void){unsigned original=0,candidate=0;float m[16]={0};
 for(int test=0;test<10000;test++){
  memset(bodies,0,sizeof(bodies));memset(owners,0,sizeof(owners));entryCount=0;
  for(int i=0;i<100;i++){
   int typ=(i+test)%9;owners[i].vt=&types[typ];owners[i].name=typ==1?"cLuxCameraEntity":typ==2?"cCharacterBodyNewton":"cLuxProp";
   owners[i].invalid=(i+test)%17==0;if((i+test)%23==0){owners[i].name=0;owners[i].vt=&types[99];}
   void*p=&owners[i];memcpy(bodies[i].bytes+0x2c0,&p,8);p=&owners[(i+3)%100];memcpy(bodies[i].bytes+0x160,&p,8);
   bodies[i].trigger=(i+test)%13==0;bodies[i].rocker=(i+test)%19==0;bodies[i].proxy=(i+test)%29==0;bodies[i].self=(i+test)%31==0;bodies[i].area=(i+test)%37==0;
  }
  int n=test%101;for(int i=0;i<n;i++){entries[entryCount++]=&bodies[i];if(i%7==0)entries[entryCount++]=&bodies[i];}
  H504Near a,b;cpuNearBaseline=1;decodes=0;h504_collect_near((void*)1,0,m,m,&a);original+=decodes;
  cpuNearBaseline=0;decodes=0;h504_collect_near((void*)1,0,m,m,&b);candidate+=decodes;
  CHECK(a.count==b.count);CHECK(!memcmp(a.body,b.body,a.count*sizeof(void*)));
  /* No retained identity: same addresses, different class on next enumeration. */
  for(int i=0;i<100;i++)owners[i].name="cLuxCameraEntity";
  cpuNearBaseline=1;h504_collect_near((void*)1,1,m,m,&a);cpuNearBaseline=0;h504_collect_near((void*)1,1,m,m,&b);
  CHECK(a.count==b.count);CHECK(!memcmp(a.body,b.body,a.count*sizeof(void*)));
 }
 /* Capacity overflow: 100 distinct immutable types, all excluded as camera bodies. */
 int test=10000;entryCount=100;memset(bodies,0,sizeof(bodies));
 for(int i=0;i<100;i++){owners[i].vt=&types[i];owners[i].name="cLuxCameraEntity";owners[i].invalid=0;void*p=&owners[i];memcpy(bodies[i].bytes+0x2c0,&p,8);entries[i]=&bodies[i];}
 H504Near a,b;cpuNearBaseline=1;h504_collect_near((void*)1,0,m,m,&a);cpuNearBaseline=0;h504_collect_near((void*)1,0,m,m,&b);CHECK(a.count==0&&b.count==0);
 printf("PASS 20001 ordered near-list comparisons; original/candidate RTTI calls %u/%u; filters, duplicates, invalid types, limits, scope reuse\n",original,candidate);return 0;
}
'''
b=r/'build/cpu-near';b.mkdir(exist_ok=True);(b/'contract.c').write_text(code)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'contract.c'),'-o',str(b/'contract.exe')],check=True)
subprocess.run([str(b/'contract.exe')],check=True)
