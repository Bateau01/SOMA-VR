"""Native serial pair observer parity: mesh, joints, rejected pairs; not full game."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu41-native';b.mkdir(exist_ok=True)
s=(r/'build/cpu40-tree/test.c').read_text()
marker='/* Private synchronous native-job scheduling.'
prefix=r'''
static DWORD c41Main;static unsigned c41Observe,c41Seq;static unsigned long long c41Records,c41Dropped;static unsigned c41Types;
#define C41_NOW() tick()
#define C41_MAIN() (GetCurrentThreadId()==c41Main)
'''+(r/'tests/cpu41_pair.inc').read_text()+r'''
static void c41_hook(HMODULE m){unsigned char*p=(unsigned char*)m+0x39a00;const unsigned char sig[]={0x4c,0x8b,0xdc,0x49,0x89,0x5b,0x08,0x49,0x89,0x6b,0x10,0x49,0x89,0x73,0x18};C(!memcmp(p,sig,15));unsigned char*t=VirtualAlloc(0,64,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);C(t);memcpy(t,p,15);unsigned char jump[14]={0xff,0x25,0,0,0,0};void*back=p+15;memcpy(jump+6,&back,8);memcpy(t+15,jump,14);c41Kernel=(void*)t;void*target=(void*)c41_pair;memcpy(jump+6,&target,8);DWORD old;C(VirtualProtect(p,15,PAGE_EXECUTE_READWRITE,&old));memcpy(p,jump,14);p[14]=0x90;FlushInstructionCache(GetCurrentProcess(),p,15);C(VirtualProtect(p,15,old,&old));}
'''
s=s.replace(marker,prefix+marker,1)
s=s.replace('int main(){','int main(){c41Main=GetCurrentThreadId();',1).replace('C(m);','C(m);c41_hook(m);',1)
s=s.replace('mode<5','mode<2').replace('requested=mode==1?2:mode==2?4:mode==3?8:mode==4?16:0;','requested=0;c41Observe=mode;c41Seq=0;')
s=s.replace('c37_job(j);if(memcmp','c41Count=c41Overflow=0;c41Active=c41Observe&&((++c41Seq%8)==0);c37_job(j);c41Active=0;c41Records+=c41Count;c41Dropped+=c41Overflow;for(unsigned z=0;z<c41Count;z++){C41Pair*q=c41Pairs+z;C(q->b>=q->a&&q->body0&&q->body1&&q->type0<32&&q->type1<32);c41Types|=1u<<q->type0;c41Types|=1u<<q->type1;}if(memcmp')
s=s.replace('C(runs>0);','C(c41Records>0);')
s=s.replace('printf("RESULT failures=', 'printf("PAIR_RECORDS %llu overflow %llu types %x\\n",c41Records,c41Dropped,c41Types);printf("RESULT failures=')
(b/'test.c').write_text(s);subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=120)
(r/'audit/cpu41-native.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
