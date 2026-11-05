"""Native Newton SSE scheduling parity and cost, not HPL gameplay proof."""
from pathlib import Path
import ast,sys,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu38-jointed-native';b.mkdir(exist_ok=True)
assert hashlib.sha256(Path(r'D:\SteamLibrary\steamapps\common\SOMA\Newton.dll').read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74'
t=ast.parse((r/'tests/test_cpu36_native.py').read_text());v={n.targets[0].id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['pre','post']}
pre=v['pre']+'#define C37_MIN_PAIRS 2\n'+r"""
static unsigned requested,nativeStep;static unsigned long long timingFreq;static unsigned long long batches;
static unsigned long long tick(void){LARGE_INTEGER q;QueryPerformanceCounter(&q);return q.QuadPart;}
#define C37_NOW() tick()
#define C37_MODE(j) (requested==16?c38_select((j)->world,(unsigned)(j)->limit,++nativeStep,1,timingFreq):requested)
#define C37_MAIN() 1
#define C37_REPORT(c) do {if((c)->n)batches++;unsigned long long largest=0;unsigned long long cost=(c)->joined-(c)->start;if((c)->n){cost=0;for(unsigned k=0;k<(c)->n;k++){unsigned long long part=(c)->end[k]-(c)->begin[k];cost+=part;if(part>largest)largest=part;}}c38_observe(cost,largest,(c)->n);} while(0)
"""
pre=pre.replace('static void(*force)', 'static void*(*getUD)(const void*);static void(*setTorque)(const void*,const float*);\nstatic void(*force)')
pre=pre.replace('force(b,f);__atomic', 'unsigned long long id=getUD?(unsigned long long)getUD(b):0;if(id){if(id<=16){float t[4]={0,.25f,0,0};setTorque(b,t);}else f[0]=.3f;}force(b,f);__atomic')
core=(r/'tests/cpu38_policy.inc').read_text()+(r/'tests/cpu37_core.inc').read_text()
wrapper=r"""
static void entry(void*j){unsigned char old[40];memcpy(old,j,40);unsigned mx=c37_getmx();c37_job(j);if(memcmp(old,j,40)!=0){puts("DESCRIPTOR CHANGED");exit(1);}if((c37_getmx()&~63u)!=(mx&~63u)){puts("MXCSR CONTROL CHANGED");exit(1);}if(c37_getmx()!=mx){static unsigned reports;if(reports++<16)printf("MXCSR STATUS requested=%u old=%x new=%x\n",requested,mx,c37_getmx());}}
"""
post=v['post'].replace('scene<3','scene<5').replace('int n=scene==1?64:96;', 'int n=scene==1?64:scene==3?16:96;').replace('scene==2','scene>=2').replace('c36Execute','c37Execute').replace('c36Queue','c37Queue').replace('c36Join','c37Join').replace('c36Runs','batches').replace('c36_job','entry')
post=post.replace('for(int mode=0;mode<2;mode++){','for(int mode=0;mode<5;mode++){requested=mode==1?2:mode==2?4:mode==3?8:mode==4?16:0;nativeStep=0;double one=0;unsigned long long rb=batches;')
post=post.replace('timings[mode]+=','one+=')
post=post.replace('*job=old;destroy(w);','*job=old;destroy(w);printf("MODE scene=%d hz=%d jobs=%u ms=%.6f batches=%llu max_delta=%.9g mismatch=%u\\n",scene,rate,requested,one/180,batches-rb,maxdelta,countdiff);if(mode==0)timings[0]=one;else timings[1]=one;')
post=post.replace('force=(void*)GetProcAddress(m,"NewtonBodySetForce");', 'getUD=(void*)GetProcAddress(m,"NewtonBodyGetUserData");setTorque=(void*)GetProcAddress(m,"NewtonBodySetTorque");C(getUD&&setTorque);force=(void*)GetProcAddress(m,"NewtonBodySetForce");')
post=post.replace('int n=scene==1?', 'void(*setUD)(void*,void*)=(void*)GetProcAddress(m,"NewtonBodySetUserData");void*(*makeHinge)(void*,const float*,const float*,void*,void*)=(void*)GetProcAddress(m,"NewtonConstraintCreateHinge");void*(*makeSlider)(void*,const float*,const float*,void*,void*)=(void*)GetProcAddress(m,"NewtonConstraintCreateSlider");C(setUD&&makeHinge&&makeSlider);int n=scene==1?')
post=post.replace('bs[i]=body(w,c,mat);', 'if(scene==4&&i<32)mat[13]=.98f;bs[i]=body(w,c,mat);')
post=post.replace('if(scene>=2)autosleep(bs[i],0);', 'if(scene>=2)autosleep(bs[i],0);if(scene==4&&i<32){float pivot[3]={mat[12],mat[13],mat[14]},axis[3]={i<16?0.f:1.f,i<16?1.f:0.f,0};C((i<16?makeHinge:makeSlider)(w,pivot,axis,bs[i],0));setUD(bs[i],(void*)(unsigned long long)(i+1));}')
post=post.replace('if(mode)*job=vt;','*job=vt;')
post=post.replace('QueryPerformanceFrequency(&freq);','QueryPerformanceFrequency(&freq);timingFreq=(unsigned long long)freq.QuadPart;')
s=pre+core+wrapper+post;(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=120)
(r/'audit/cpu38-jointed-native-unit.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
