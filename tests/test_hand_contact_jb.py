"""Extracted identity/lifetime guards, not proof of solid native contact."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
code=r'''
#include <cstring>
#include <cstdio>
#include <cstdlib>
using u32=unsigned;using i32=int;using u8=unsigned char;
using H5730TString=char;
#define zero_bytes(p,n) memset(p,0,n)
static int gate=1,native=0;static void*g_s26yOwner=(void*)5;static const void*g_s26yMainRaw=(void*)6;
static int s26y_gate(){return gate;}static int ni_native_input(){return native;}
static int s26y_id(const char*t,u32*id){char*end;auto x=strtoul(t,&end,10);if(!*t||*end)return 0;*id=x;return 1;}
static int h5748t_sso_eq(const char*t,const char*s,u32 n){return strlen(t)==n&&!memcmp(t,s,n);}
static int h20_mem_readable(void*p,u32 n){return p!=0;}
alignas(8) static u8 wrapper[0x300];
static void* userdata(const void*b){return b==(void*)2?wrapper:nullptr;}
static void*(*p_h14GetUserData)(const void*)=userdata;
'''+(r/'source/hand_contact_jb.inc').read_text()+r'''
#define C(x) do{if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}checks++;}while(0)
int main(){int checks=0;*(const void**)(wrapper+0x2e8)=(void*)2;*(void**)(wrapper+0x2c0)=(void*)5;*(u32*)(wrapper+0x3c)=17;wrapper[0xe4]=1;
 C(!s26jb_solid_body((void*)2));C(s26jb_solid_token("17","S"));C(s26jb_solid_body((void*)2));
 C(!s26jb_solid_body((void*)3));C(!s26jb_solid_body(nullptr));
 native=1;C(!s26jb_solid_body((void*)2));C(!s26jb_solid_token("18","S"));native=0;
 gate=0;C(!s26jb_solid_body((void*)2));gate=1;
 wrapper[0xe4]=0;C(!s26jb_solid_body((void*)2));wrapper[0xe4]=1;
 *(u32*)(wrapper+0x3c)=18;C(!s26jb_solid_body((void*)2));*(u32*)(wrapper+0x3c)=17;
 *(void**)(wrapper+0x2c0)=(void*)7;C(!s26jb_solid_body((void*)2));*(void**)(wrapper+0x2c0)=(void*)5;
 C(s26jb_solid_token("17","U"));C(!s26jb_solid_body((void*)2));C(!s26jb_solid_token("bad","S"));
 C(!s26jb_solid_token("17","X"));C(s26jb_solid_token("17","S"));s26jb_solid_reset();C(!s26jb_solid_body((void*)2));
 for(int i=0;i<32;i++){char id[16];sprintf(id,"%d",i);C(s26jb_solid_token(id,"S"));}
 C(!s26jb_solid_token("100","S"));C(s26jb_solid_token("0","U"));C(s26jb_solid_token("100","S"));
 printf("PASS %d hand-only contact registry assertions\n",checks);
}
'''
p=r/'build/hand_contact_jb.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(r/'audit/jb-hand-contact-guards.json').write_text(json.dumps({'scope':__doc__,'exit':v.returncode,'output':v.stdout+v.stderr},indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
