"""Native callback thread/stage audit; not full HPL callback safety proof."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu39-callbacks';b.mkdir(exist_ok=True)
s=(r/'build/cpu38-jointed-native/test.c').read_text()
assert hashlib.sha256(Path(r'D:\SteamLibrary\steamapps\common\SOMA\Newton.dll').read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74'
s=s.replace('static void contact(',r"""static DWORD mainThread;static unsigned generation, cb[3][3];
static void note(unsigned k){__atomic_fetch_add(&cb[k][0],1,__ATOMIC_RELAXED);if(GetCurrentThreadId()!=mainThread)__atomic_fetch_add(&cb[k][1],1,__ATOMIC_RELAXED);if(__atomic_load_n(&generation,__ATOMIC_RELAXED))__atomic_fetch_add(&cb[k][2],1,__ATOMIC_RELAXED);}
static int overlap(const void*m,const void*a,const void*b,int thread){note(0);return 1;}
static void contact(""")
s=s.replace('__atomic_fetch_add(&contacts,1,__ATOMIC_RELAXED);','note(1);__atomic_fetch_add(&contacts,1,__ATOMIC_RELAXED);')
s=s.replace('int main(){','int main(){mainThread=GetCurrentThreadId();')
s=s.replace('c37_job(j);if(memcmp','__atomic_store_n(&generation,1,__ATOMIC_RELAXED);c37_job(j);__atomic_store_n(&generation,0,__ATOMIC_RELAXED);if(memcmp')
s=s.replace('mc(w,0,0,0,0,contact);contacts=forces=0;','mc(w,0,0,0,overlap,contact);contacts=forces=0;memset(cb,0,sizeof(cb));')
s=s.replace('*job=old;destroy(w);',r"""printf("CALLBACK scene=%d hz=%d jobs=%u overlap=%u/%u/%u process=%u/%u/%u\n",scene,rate,requested,cb[0][0],cb[0][1],cb[0][2],cb[1][0],cb[1][1],cb[1][2]);*job=old;destroy(w);""")
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=180)
(r/'audit/cpu39-callbacks.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)
