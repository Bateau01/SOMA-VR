from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];A=R/'audit/rate-menu-unit';A.mkdir(parents=True,exist_ok=True)
head=r'''
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;
static u8 exe[4096];static unsigned g_s26gdRateMultiplier=1;
static char saved[16]="60\n",pending[16];static int failure,opens,moves,deletes;
static int make_sibling_path(char*p,unsigned n,const char*s){snprintf(p,n,"%s",s);return failure!=1;}
static void* ext_GetModuleHandleA(const char*p){return exe;}
static void* ext_fopen(const char*p,const char*m){opens++;return failure==2?0:(void*)1;}
static u64 ext_fwrite(const void*p,u64 size,u64 n,void*f){memcpy(pending,p,n);pending[n]=0;return failure==3?0:n;}
static int ext_fclose(void*f){return failure==4?-1:0;}
static i32 __attribute__((ms_abi)) move_file(const char*a,const char*b,u32 flags){assert(flags==9);moves++;if(failure==5)return 0;strcpy(saved,pending);pending[0]=0;return 1;}
static i32 __attribute__((ms_abi)) delete_file(const char*p){pending[0]=0;deletes++;return 1;}
static void* ext_GetProcAddress(void*k,const char*n){if(failure==6)return 0;return strcmp(n,"MoveFileExA")==0?(void*)move_file:(void*)delete_file;}
static int s26gd_requested(void){return strcmp(saved,"120\n")==0;}
static int h5748t_sso_eq(const void*p,const char*s,u32 n){return p&&strcmp(p,s)==0;}
static void ext_Log(const char*f,...){}
'''
tail=r'''
int main(void){
 *(u32*)(exe+0x3c)=0x80;*(u32*)(exe+0x80)=0x4550;*(u32*)(exe+0x88)=0x6151d1ca;*(u32*)(exe+0x80+24+56)=0x8fb000;
 assert(s26ge_rate_token("SUPPORTED")==1);assert(!s26ge_rate_token("GET"));assert(!s26ge_rate_token("bad"));assert(!opens&&!moves);
 for(int active=1;active<=2;active++){
  g_s26gdRateMultiplier=active;
  for(int initial=0;initial<=1;initial++){
   const char*old=initial?"120\n":"60\n";const char*command=initial?"OFF":"ON";
   for(failure=1;failure<=6;failure++){strcpy(saved,old);assert(!s26ge_rate_token(command));assert(!strcmp(saved,old));assert(g_s26gdRateMultiplier==(unsigned)active);assert(!pending[0]);}
   failure=0;strcpy(saved,old);assert(s26ge_rate_token(command));assert(s26ge_rate_token("GET")==!initial);assert(g_s26gdRateMultiplier==(unsigned)active);
  }
 }
 *(u32*)(exe+0x88)=0;strcpy(saved,"60\n");assert(!s26ge_rate_token("ON"));assert(!strcmp(saved,"60\n"));assert(!s26ge_rate_token("SUPPORTED"));assert(s26ge_rate_token("OFF"));
 puts("PASS: atomic selection, both directions/rates, path/open/write/close/rename/API failure, unsupported enable rejection, live multiplier unchanged");
}
'''
p=A/'test.c';p.write_text(head+(R/'source/simulation_menu_ge.inc').read_text()+tail)
subprocess.run([sys.argv[1],'cc',str(p),'-O2','-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(r.stdout,r.stderr);assert r.returncode==0
(A/'result.json').write_text(json.dumps({'pass':True,'output':r.stdout,'scope':'Production native writer with mocked filesystem failures'},indent=2))
