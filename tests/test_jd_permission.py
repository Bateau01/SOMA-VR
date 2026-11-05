from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];src=(r/'source/s26n.c').read_bytes().decode('cp1252')
a=src.index('static i32 s26jd_lever_denied(');b=src.index('\nstatic const void* g_s26dpReadableContactBody;',a)
helper=src[a:b]
head=r'''
#include <cstdio>
#include <cstdint>
using i32=int;using u32=unsigned;using u64=uint64_t;using u8=unsigned char;
using PFN_H25_CanInteract=u64(*)(void*,int,void*);using PFN_H25_GetInteractIconId=int(*)(void*,int,void*);
int iconValue,allowed,resolvable=1,canCalls,checks;
void* vt[16];void** object=vt;
u64 can(void*,int,void*){++canCalls;return allowed;}
int icon(void*,int,void*){return iconValue;}
int h20_mem_readable(void*,int){return 1;}int h25_soma_code_ptr(void*p){return p!=nullptr;}
int h25_resolve_native_target(const void*,void**w,void**e,void**c,void**on,u32*off,char*,int){*w=(void*)1;*e=&object;*c=(void*)can;return resolvable;}
#define C(x) do{++checks;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
'''
main=r'''
int main(){vt[0x68/8]=(void*)icon;
for(int k=0;k<32;++k)for(int p=0;p<2;++p){iconValue=k;allowed=p;canCalls=0;int denied=s26jd_lever_denied((void*)1);C(denied==((k==5||k==6)&&!p));C(canCalls==((k==5||k==6)?1:0));}
resolvable=0;C(!s26jd_lever_denied((void*)1));
printf("PASS %d extracted native permission guard checks; mocked engine\n",checks);}
'''
p=r/'build/jd-permission.cpp';p.write_text(head+helper+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout);assert v.returncode==0
# Entry-boundary coverage: queue and latch must gate before any attempt/anchor write.
q=src[src.index('static i32 h25_queue_native_interact('):];assert q.index('s26jd_lever_denied(body)')<q.index('g_h25AttemptBody[hand]=body')
i=src.index('static void h14_latch(',src.index('static void h14_latch(')+1);l=src[i:];assert l.index('s26jd_lever_denied(body)')<l.index('g_h15GripBodyAnchor[hand]')
(r/'audit/jd-lever-permission/helper.json').write_text(json.dumps({'scope':'Extracted production helper with engine stubs and entry-boundary assertions; not physical gameplay','exit':v.returncode,'output':v.stdout},indent=2))
