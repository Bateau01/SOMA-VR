from pathlib import Path
import re,subprocess,sys,json
r=Path('.').resolve();s=(r/'source/cpu9_render_trial.inc').read_text();b=r/'audit/cpu9-install-contract';b.mkdir(exist_ok=True)
prefix='''#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
typedef uint64_t u64;typedef unsigned u32;typedef unsigned char u8;typedef int i32;
#define ABI __attribute__((ms_abi))
#define CPU_RENDER_JOBS 1
#define CPU_WORK_PROFILE 0
static unsigned char image[0x700000];static int createCount,enableCount,failCreate=-1,failEnable=-1;
static void zero_bytes(void*p,u64 n){memset(p,0,n);}static void ext_Log(const char*s,...){(void)s;}
static u32 ABI tid(void){return 1;}static u32(ABI*cpuThreadId)(void);static u32 cpuMainThread;static u64 cpuJobBase,cpuFreq=1;
static void*ext_GetModuleHandleA(const char*p){(void)p;return image;}static void*ext_GetProcAddress(void*m,const char*n){(void)m;(void)n;return (void*)tid;}
static int h20_mem_readable(void*p,u32 n){return (u8*)p>=image&&(u8*)p+n<=image+sizeof(image);}static int h20_mem_executable(void*p){return h20_mem_readable(p,32);}
static int ext_MH_CreateHook(void*t,void*h,void**o){(void)h;*o=t;return createCount++==failCreate?-1:0;}
static int ext_MH_EnableHook(void*t){(void)t;return enableCount++==failEnable?-1:0;}
static void*ext_fopen(const char*a,const char*b){(void)a;(void)b;return 0;}static u64 ext_fread(void*a,u64 b,u64 c,void*d){(void)a;(void)b;(void)c;(void)d;return 0;}static void ext_fclose(void*f){(void)f;}
static u64 cpu_detail_begin(void){return 0;}static int ABI counter(u64*p){*p=0;return 1;}static int(ABI*cpuCounter)(u64*)=counter;
static void(ABI*cpuQueueOriginal)(void*,void*,u8);static void(ABI*cpuWaitOriginal)(void*);static void ABI cpu_wait_call(void*p){(void)p;}
'''
code=prefix+'\n#include "'+(r/'source/cpu9_render_trial.inc').as_posix()+'"\nstatic void ABI cpu_queue_call(void*a,void*b,u8 c){(void)a;(void)b;(void)c;}\nint main(int argc,char**argv){int mode=argc>1?atoi(argv[1]):0;\n'
for name,addr in zip('abcde',[0x388030,0x376550,0x387e50,0x3880a0,0x2894a0]):
 vals=re.search(r'const u8 '+name+r'\[\]=\{([^}]+)',s).group(1);code+=f'const u8 {name}[]={{'+vals+f'}};memcpy(image+{addr},{name},sizeof({name}));\n'
code+='''*(u64*)(image+0x6e9f60)=(u64)image+0x377470;
if(mode>=1&&mode<=4){unsigned offsets[]={0x388030,0x376550,0x387e50,0x3880a0};image[offsets[mode-1]]^=1;}
if(mode==5)*(u64*)(image+0x6e9f60)=0;
if(mode>=6&&mode<=9)failCreate=mode-6;
if(mode>=10&&mode<=13)failEnable=mode-10;
cpu9_install();assert(cpu9Ready==(mode==0));if(mode>0&&mode<=5)assert(createCount==0&&enableCount==0);
if(mode>=6&&mode<=9)assert(enableCount==0);
printf("PASS install scenario %d ready %u creates %d enables %d\\n",mode,cpu9Ready,createCount,enableCount);return 0;}
'''
(b/'test.c').write_text(code);zig=str(r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe')
subprocess.run([zig,'cc',str(b/'test.c'),'-O2','-o',str(b/'test.exe')],check=True)
results=[]
for i in range(14):
 p=subprocess.run([str(b/'test.exe'),str(i)],capture_output=True,text=True);results.append({'scenario':i,'returncode':p.returncode,'output':p.stdout+p.stderr});assert p.returncode==0,results[-1]
(b/'result.json').write_text(json.dumps(results,indent=2));print('PASS 14 production install signature/vtable/create/enable fail-closed scenarios')
