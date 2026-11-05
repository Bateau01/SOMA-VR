"""Native narrow cache parity, not HPL gameplay validation."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu43-native';b.mkdir(exist_ok=True)
# CPU42 generated compound/debug fixture supplies its verified baseline checks.
s=(r/'build/cpu42-reuse/test.c').read_text()
assert 'setDebug(floor' in s and 'compound(w,2' in s
start=s.index('/* The table is valid');end=s.index('\nstatic void c41_hook',start)
prefix='''#define C43_MAIN() (GetCurrentThreadId()==c41Main)
#define C43_NOW() tick()
#define C43_TARGET(a,b) 1
#define C43_MIN_TICKS 0u
#define C43_SHADOW 0
static unsigned long long totalHits,totalEligible;
'''
s=s[:start]+prefix+(r/'tests/cpu43_reuse.inc').read_text()+s[end:]
s=s.replace('c41Kernel=(void*)t;','c43Kernel=(void*)t;').replace('(void*)c41_pair','(void*)c43_pair')
needle='if(++generation==0){memset(cache,0,sizeof(cache));generation=1;}c41Active=c41Observe;'
assert s.count(needle)==1
s=s.replace(needle,'c43_begin(c41Observe);')
s=s.replace('c37_job(j);c41Active=0;', 'c37_job(j);totalHits+=c43Hits;totalEligible+=c43Eligible;c43Active=0;')
s=s.replace('C(hits>0);','')
s=s.replace('hits,misses);printf', 'totalHits,totalEligible);printf')
debug='--debug-callback' in sys.argv
if not debug:s=s.replace('setDebug(floor,(void*)debugCallback);','')
s=s.replace('printf("RESULT failures=', ('C(totalHits==0);' if debug else 'C(totalHits>0);')+'printf("RESULT failures=')
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=180)
(r/('audit/cpu43-native-debug.json' if debug else 'audit/cpu43-native.json')).write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)
