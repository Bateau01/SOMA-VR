"""Native Newton SSE scheduling parity and cost, not HPL gameplay proof."""
from pathlib import Path
import ast,sys,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu37-native';b.mkdir(exist_ok=True)
assert hashlib.sha256(Path(r'D:\SteamLibrary\steamapps\common\SOMA\Newton.dll').read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74'
t=ast.parse((r/'tests/test_cpu36_native.py').read_text());v={n.targets[0].id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['pre','post']}
pre=v['pre']+'#define C37_MIN_PAIRS 2\n'+r"""
static unsigned requested;static unsigned long long batches;
static unsigned long long tick(void){LARGE_INTEGER q;QueryPerformanceCounter(&q);return q.QuadPart;}
#define C37_NOW() tick()
#define C37_MODE(j) requested
#define C37_MAIN() 1
#define C37_REPORT(c) do {if((c)->n)batches++;} while(0)
"""
core=(r/'tests/cpu37_core.inc').read_text()
wrapper=r"""
static void entry(void*j){unsigned char old[40];memcpy(old,j,40);unsigned mx=c37_getmx();c37_job(j);C(memcmp(old,j,40)==0);C(c37_getmx()==mx);}
"""
post=v['post'].replace('scene<3','scene<4').replace('int n=scene==1?64:96;', 'int n=scene==1?64:scene==3?16:96;').replace('scene==2','scene>=2').replace('c36Execute','c37Execute').replace('c36Queue','c37Queue').replace('c36Join','c37Join').replace('c36Runs','batches').replace('c36_job','entry')
post=post.replace('for(int mode=0;mode<2;mode++){','for(int mode=0;mode<4;mode++){requested=mode==1?2:mode==2?4:mode==3?8:0;double one=0;unsigned long long rb=batches;')
post=post.replace('timings[mode]+=','one+=')
post=post.replace('*job=old;destroy(w);','*job=old;destroy(w);printf("MODE scene=%d hz=%d jobs=%u ms=%.6f batches=%llu max_delta=%.9g mismatch=%u\\n",scene,rate,requested,one/180,batches-rb,maxdelta,countdiff);if(mode==0)timings[0]=one;else timings[1]=one;')
s=pre+core+wrapper+post;(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=120)
(r/'audit/cpu37-native-unit.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
