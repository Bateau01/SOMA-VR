from pathlib import Path
import subprocess,sys,json
from cpu31_transform import function
r=Path(__file__).resolve().parents[1];s=(r/'build/movement/test.c').read_text()
core='\n'.join(function(s,n)[2] for n in ('s26y_slot','s26y_body_slot','cpu31_slot','h540_nonphysical_area_body','cpu31_area','h5755ct_noncharacter_body_eligible','cpu31_eligible'))
pre=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
typedef struct{void*BaseAddress;void*AllocationBase;u32 AllocationProtect;unsigned short PartitionId,pad0;u64 RegionSize;u32 State,Protect,Type,pad1;}H20MBI;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
static u8 mem[8192];static void*w=mem+512;static u64 queries;static int fail,split,gate=1,trigger,active=1;static u32 protect=4,state=0x1000;
static i32 h20_mem_query(const void*p,H20MBI*m){queries++;if(fail)return 0;memset(m,0,sizeof(*m));u64 a=(u64)p,lo=(u64)mem,cut=(u64)w+0x250;if(a<lo||a>=lo+sizeof(mem))return 0;m->BaseAddress=(void*)(split&&a>=cut?cut:lo);m->RegionSize=split?(a>=cut?lo+sizeof(mem)-cut:cut-lo):sizeof(mem);m->State=state;m->Protect=protect;return 1;}
static i32 h20_mem_readable(const void*p,u64 n){H20MBI m;if(!h20_mem_query(p,&m)||m.State!=0x1000)return 0;u32 pr=m.Protect;if((pr&0x100)||(pr&0xff)==1)return 0;u64 a=(u64)p,b=(u64)m.BaseAddress,e=b+m.RegionSize;return a>=b&&a+n>=a&&a+n<=e;}
static void*userdata(const void*b){return b?w:0;}static void*(*p_h14GetUserData)(const void*)=userdata;
static const void*collision(const void*b){return b;}static const void*(*p_h14GetCollision)(const void*)=collision;
static int trig(const void*b){return trigger;}static int(*p_h14IsTrigger)(const void*)=trig;
static i32 s26y_gate(void){return gate;}
static struct{int used;u32 id;void*owner;}g_s26yRocker[64];static int g_s26yCount=1;
#define H5755DB_AREA_STEP_CACHE_MAX 32
static u32 g_h5755dbAreaCacheStep,g_h14PhysicsSteps=1;static u8 g_h5755dbAreaCacheCount,g_h5755dbAreaCacheKind[32];static const void*g_h5755dbAreaCacheBody[32];
static void h5755db_area_cache_put(const void*b,i32 k){if(b&&g_h5755dbAreaCacheCount<32){int i=g_h5755dbAreaCacheCount++;g_h5755dbAreaCacheBody[i]=b;g_h5755dbAreaCacheKind[i]=k;}}
static int h22_rtti_name(const void*p,char*out,u32 cap){strcpy(out,p==(void*)1?"cLuxArea":"cLuxProp");return 1;}
static int h25_str_contains(const char*a,const char*b){return strstr(a,b)!=0;}
'''
post=r'''
static int baseline(const void*b){if(s26y_body_slot(b)>=0)return 0;if(h540_nonphysical_area_body(b))return 0;return h5755ct_noncharacter_body_eligible(0,b);}
static int candidate(const void*b){CPU31View v={0};if(cpu31_slot(b,&v)>=0)return 0;if(cpu31_area(b,&v))return 0;return cpu31_eligible(0,b,&v);}
int main(){u64 tests=0;for(int bits=0;bits<32768;bits++){
 memset(mem,0,sizeof(mem));gate=bits&1;g_s26yCount=(bits>>1)&1;trigger=(bits>>2)&1;fail=(bits>>3)&1;split=(bits>>4)&1;protect=(bits&32)?1:4;state=(bits&64)?0:0x1000;
 *(u8*)((u8*)w+0xe4)=(bits>>7)&1;*(u8*)((u8*)w+0x249)=(bits>>8)&1;*(u8*)((u8*)w+0x2e0)=(bits>>9)&1;*(i32*)((u8*)w+0x258)=(bits&1024)?0:-1;*(u32*)((u8*)w+0x240)=(bits&2048)?1:0;
 *(void**)((u8*)w+0x2c0)=(bits&4096)?(void*)1:(void*)2;*(u32*)((u8*)w+0x3c)=17;*(void**)((u8*)w+0x2e8)=(bits&8192)?(void*)22:(void*)23;g_s26yRocker[0].used=1;g_s26yRocker[0].id=(bits&16384)?17:18;g_s26yRocker[0].owner=(void*)2;
 g_h5755dbAreaCacheCount=0;g_h5755dbAreaCacheStep=0;int a=baseline((void*)22);g_h5755dbAreaCacheCount=0;g_h5755dbAreaCacheStep=0;int b=candidate((void*)22);C(a==b);tests++;
 }
 fail=split=0;state=0x1000;protect=4;CPU31View v={0};C(cpu31_readable(&v,w,w,0x2f0));u64 before=queries;C(cpu31_readable(&v,w,(u8*)w+0xe4,1)&&queries==before);
 /* Eligibility reads changed flags even after a region proof. */
 *(u8*)((u8*)w+0xe4)=1;*(u8*)((u8*)w+0x249)=0;*(u8*)((u8*)w+0x2e0)=1;*(i32*)((u8*)w+0x258)=0;*(u32*)((u8*)w+0x240)=1;C(cpu31_eligible(0,(void*)22,&v)==1);*(u32*)((u8*)w+0x240)=0;C(cpu31_eligible(0,(void*)22,&v)==0);
 void*old=w;w=mem+2048;before=queries;C(cpu31_readable(&v,w,w,8)&&queries==before+1);w=old;
 CPU31View fresh={0};protect=1;C(!cpu31_readable(&fresh,w,w,8));protect=0x104;C(!cpu31_readable(&fresh,w,w,8));
 printf("PASS %llu complete filter-chain combinations; query failures/boundaries, live permission mutation, wrapper identity change and invocation reset\n",tests);
}
'''
b=r/'build/cpu31-unit';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+(r/'tests/cpu31_local.inc').read_text()+core+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr);(r/'audit/cpu31-unit.json').write_text(json.dumps(dict(exit=x.returncode,output=x.stdout,scope='Compiled actual original/candidate helper chains with mocked engine/memory queries; not native interaction proof'),indent=2));raise SystemExit(x.returncode)
