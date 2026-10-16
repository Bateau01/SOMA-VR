"""Production timer detour and timing helpers with mocked hook/file boundaries."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];A=R/'audit/simulation-unit';A.mkdir(parents=True,exist_ok=True)
head=r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
typedef long long i64;typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
static char content[200];static u8 exe[0x8fb000],newton[0xe9000];static int created,enabled,failCreate,failEnable,calls,lastRate,returnNull;
static int fail120Only;
static int make_sibling_path(char*p,unsigned n,const char*s){return 1;}
static void* ext_fopen(const char*p,const char*m){return content[0]?(void*)1:0;}
static u64 ext_fread(void*p,u64 a,u64 n,void*f){u64 len=strlen(content);if(len>n)len=n;memcpy(p,content,len);return len;}
static void ext_fclose(void*f){}
static void ext_Log(const char*f,...){}
static void* ext_GetModuleHandleA(void*p){return p?(strcmp((char*)p,"kernel32.dll")==0?(void*)GetModuleHandleA("kernel32.dll"):(void*)newton):(void*)exe;}
static void* ext_GetProcAddress(void*h,const char*n){return (void*)GetProcAddress((HMODULE)h,n);}
static void* __attribute__((ms_abi)) original(void*p,i32 rate){calls++;lastRate=rate;return (returnNull||(fail120Only&&rate==120))?0:(void*)1234;}
static void __attribute__((ms_abi)) damping_original(void*p){}
static int ext_MH_CreateHook(void*t,void*d,void**o){created++;*o=t==newton+0x1f150?(void*)damping_original:(void*)original;return failCreate;}
static int ext_MH_EnableHook(void*t){enabled++;return failEnable;}
'''
mover_test=r"""
static unsigned char fakeMover[0x400],fakeVectors[720];static int resizeCalls;
static void* __attribute__((ms_abi)) mover_original(void*self,void*a,void*b,void*c){return self;}
static void __attribute__((ms_abi)) resize_mock(void*v,u64 n){assert(v==fakeMover+0x358&&n==60);resizeCalls++;((u64*)v)[1]=((u64*)v)[0]+n*12;}
static unsigned char fakePlayer[0x500],fakeSpeed[280],fakeDir[840];static int playerCalls,playerResizes;
static void __attribute__((ms_abi)) player_original(void*p,float dt){assert(p==fakePlayer&&dt>0);playerCalls++;}
static void __attribute__((ms_abi)) player_float_resize(void*v,u64 n){assert(v==fakePlayer+0x3a8&&n==70);((u64*)v)[1]=((u64*)v)[0]+n*4;playerResizes++;}
static void __attribute__((ms_abi)) player_dir_resize(void*v,u64 n){assert(v==fakePlayer+0x3e0&&n==70);((u64*)v)[1]=((u64*)v)[0]+n*12;playerResizes++;}
static void test_player(void){
 o_s26gfPlayerUpdate=player_original;p_s26gfResizeFloats=player_float_resize;p_s26gfResizeVectors=player_dir_resize;
 for(unsigned rate=1;rate<=2;rate++){
  memset(fakePlayer,0,sizeof(fakePlayer));u64*a=(u64*)(fakePlayer+0x3a8),*b=(u64*)(fakePlayer+0x3e0);a[0]=(u64)fakeSpeed;a[1]=a[0]+140;b[0]=(u64)fakeDir;b[1]=b[0]+420;
  g_s26gdRateMultiplier=rate;playerResizes=playerCalls=0;s26gf_player_update(fakePlayer,1.0f/(rate*60));assert(playerCalls==1&&playerResizes==(rate==2?2:0));
  if(rate==2){s26gf_player_update(fakePlayer,1.0f/120);assert(playerResizes==2&&playerCalls==2);}
 }
}
static int observedGround;
static void __attribute__((ms_abi)) step_original(void*self,float*a,char b,float*c,float dt){observedGround=*(int*)((u8*)self+0xe0)-4<*(int*)((u8*)self+0xdc);}
static void test_step(void){
 unsigned char body[0x800]={0};o_s26ghStep=step_original;
 for(int hz=60;hz<=120;hz+=60){g_s26gdRateMultiplier=hz/60;
  for(int age=0;age<24;age++){
   int max=hz/5;*(int*)(body+0xe0)=max;*(int*)(body+0xdc)=max-age;
   s26gh_step(body,0,1,0,1.0f/hz);
   assert(*(int*)(body+0xe0)==max);assert(observedGround==(age<hz/15));
  }
  for(int max=0;max<=10;max++){*(int*)(body+0xe0)=max;*(int*)(body+0xdc)=0;
   s26gh_step(body,0,1,0,1.0f/hz);assert(*(int*)(body+0xe0)==max);assert(observedGround==(max-4<0));
  }
 }
}
static void test_mover(void){
 o_s26gfMoverCtor=mover_original;p_s26gfResizeVectors=resize_mock;
 for(unsigned rate=1;rate<=2;rate++){
  memset(fakeMover,0,sizeof(fakeMover));u64*v=(u64*)(fakeMover+0x358);v[0]=(u64)fakeVectors;v[1]=v[0]+360;
  g_s26gdRateMultiplier=rate;resizeCalls=0;assert(s26gf_mover_ctor(fakeMover,0,0,0)==fakeMover);assert(resizeCalls==(rate==2));
  if(rate==2){s26gf_mover_ctor(fakeMover,0,0,0);assert(resizeCalls==1);}
 }
 memset(fakeMover,0,sizeof(fakeMover));resizeCalls=0;s26gf_mover_ctor(fakeMover,0,0,0);assert(!resizeCalls);
}
"""
test=r'''
static void reset(void){const u8 ss[]={0x0f,0x2f,0x15,0x3a,0x21,0x11,0};memcpy(exe+0x57c8ff,ss,7);exe[0x57c959]=0x83;exe[0x57c95a]=0xe8;exe[0x57c95b]=4;*(float*)(exe+0x68ea40)=0.0001f;g_s26ghStepThreshold=0;g_s26gdInstalled=g_s26gdTimerSeen=0;g_s26gdRateMultiplier=1;created=enabled=failCreate=failEnable=calls=lastRate=returnNull=0;o_s26gdCreateTimer=original;}
int main(void){
 test_player();test_mover();test_step();
 const char* bad[]={"","60","119","120x","120\n120","-120","120.0","\xef\xbb\xbf" "120"};
 for(unsigned i=0;i<sizeof(bad)/sizeof(*bad);i++){strcpy(content,bad[i]);assert(!s26gd_requested());}
 strcpy(content," \r\n120\t ");assert(s26gd_requested());memset(content,'1',100);content[100]=0;assert(!s26gd_requested());
 *(u32*)(exe+0x3c)=0x80;*(u32*)(exe+0x80)=0x4550;*(u32*)(exe+0x88)=0x6151d1ca;*(u32*)(exe+0x80+24+56)=0x8fb000;
 const u8 sig[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf9,0xb9,0x50,0,0,0,0x8b,0xda};memcpy(exe+0x364f10,sig,sizeof(sig));
 *(u32*)(newton+0x3c)=0x80;*(u32*)(newton+0x80)=0x4550;*(u32*)(newton+0x88)=0x54bcf792;*(u32*)(newton+0x80+24+56)=0xe9000;
 const u8 ds[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x81,0xec,0x80,0,0,0,0xf3,0x0f,0x10,0x91,0xcc,1,0,0};memcpy(newton+0x1f150,ds,sizeof(ds));
 const u8 cs[]={0x48,0x8b,0xc4,0x48,0x89,0x48,8,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};memcpy(exe+0x54540,cs,sizeof(cs));
 const u8 rs[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x30};memcpy(exe+0x54170,rs,sizeof(rs));
 const u8 us[]={0x48,0x8b,0xc4,0x55,0x57,0x41,0x54,0x48,0x8d,0x68,0xa1,0x48,0x81,0xec,0xa0,0,0,0};memcpy(exe+0x161510,us,sizeof(us));
 const u8 gs[]={0x48,0x8b,0xc4,0x55,0x53,0x48,0x8d,0xa8,0x08,0xff,0xff,0xff,0x48,0x81,0xec,0xe8,1,0,0};memcpy(exe+0x57c8b0,gs,sizeof(gs));
 const u8 fs[]={0x48,0x89,0x5c,0x24,0x10,0x56,0x48,0x83,0xec,0x20,0x4c,0x8b,9,0x48,0x8b,0xda};memcpy(exe+0xaf5e0,fs,sizeof(fs));
 reset();strcpy(content,"60");s26gd_install();assert(!created&&g_s26gdRateMultiplier==1);
 reset();strcpy(content,"120");s26gd_install();s26gd_install();assert(created==5&&enabled==5&&g_s26gdRateMultiplier==1);
 assert(s26gd_create_timer((void*)9,60)==(void*)1234);assert(calls==1&&lastRate==120&&g_s26gdRateMultiplier==2);
 assert(exe[0x57c95b]==4&&*g_s26ghStepThreshold==0.000025f&&*(float*)(exe+0x68ea40)==0.0001f);
 
 s26gd_create_timer((void*)9,60);assert(calls==2&&lastRate==60);
 reset();s26gd_install();fail120Only=1;
 assert(s26gd_create_timer(0,60)==(void*)1234&&calls==2&&lastRate==60&&g_s26gdRateMultiplier==1);
 assert(*g_s26ghStepThreshold==0.0001f);fail120Only=0;
 reset();s26gd_create_timer(0,30);assert(lastRate==30&&g_s26gdRateMultiplier==1);
 reset();returnNull=1;assert(!s26gd_create_timer(0,60)&&g_s26gdRateMultiplier==1);
 reset();exe[0x364f10]^=1;s26gd_install();assert(!created);exe[0x364f10]^=1;
 reset();*(u32*)(exe+0x88)=0x6151ca9c;s26gd_install();assert(!created);*(u32*)(exe+0x88)=0x6151d1ca;
 reset();failCreate=1;s26gd_install();assert(created==1&&!enabled&&g_s26gdRateMultiplier==1);
 reset();failEnable=1;s26gd_install();assert(created==1&&enabled==1&&g_s26gdRateMultiplier==1);
 for(unsigned hz=60;hz<=120;hz+=60){g_s26gdRateMultiplier=hz/60;for(unsigned ticks=1;ticks<=600;ticks++)assert(fabs((double)s26gd_steps(ticks)/hz-(double)ticks/60)<1e-8);assert(fabs(s26gd_tick_amount(.012f)*hz-.72f)<1e-6);}
 reset();newton[0x1f150]^=1;s26gd_install();assert(!created);newton[0x1f150]^=1;
 for(unsigned i=1;i<=100;++i){float d=i*.0002f;float h=s26gd_half_damping(d);assert(fabs((1-h)*(1-h)-(1-d))<2e-7);}
 float coeffs[]={.45f,.75f,.82f};for(unsigned i=0;i<3;i++){g_s26gdRateMultiplier=1;assert(s26gd_alpha(coeffs[i])==coeffs[i]);g_s26gdRateMultiplier=2;float a=s26gd_alpha(coeffs[i]);assert(fabs(1-(1-a)*(1-a)-coeffs[i])<1e-6);}
 puts("PASS: strict opt-in, startup-only hook, executable/signature rejection, hook failures, single native timer call, unexpected calls, duration equivalence and filtering equivalence");
}
'''
p=A/'test.c';p.write_text(head+(R/'source/simulation_rate_gd.h').read_text()+(R/'source/simulation_rate_gd.inc').read_text()+mover_test+test)
subprocess.run([sys.argv[1],'cc',str(p),'-O2','-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(r.stdout,r.stderr);assert r.returncode==0
(A/'result.json').write_text(json.dumps({'pass':True,'output':r.stdout,'scope':'mocked boundary tests; no hardware validation'},indent=2))
