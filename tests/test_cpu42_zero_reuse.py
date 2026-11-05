"""Private native-only zero-contact reuse experiment; no game integration."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu42-reuse';b.mkdir(exist_ok=True)
s=(r/'build/cpu41-native/test.c').read_text()
start=s.index('static void c41_pair(');end=s.index('\nstatic void c41_hook',start)
s=s[:start]+r'''
/* The table is valid only inside the original synchronous generation job.
   Bounded probing fails back to native. No positive contacts are reused.
   This experiment has not audited custom collision callback side effects. */
typedef struct {unsigned used;unsigned char in[48],out[48],body0[0x208],body1[0x208],material[0xa0];} C42Entry;
static C42Entry cache[256];static unsigned generation;static unsigned long long hits,misses;
static void c41_pair(void*w,void*p,float dt,int thread){
 if(!c41Active||thread!=0||!C41_MAIN()){c41Kernel(w,p,dt,thread);return;}
 unsigned char*in=p;void*a=*(void**)in,*b=*(void**)(in+8),*m=*(void**)(in+24);
 if(*(void**)(in+16)){c41Kernel(w,p,dt,thread);return;}
 unsigned hash=(unsigned)(((unsigned long long)a>>4)^((unsigned long long)b>>7)^((unsigned long long)m>>5))&255;
 C42Entry*slot=0;
 for(unsigned j=0;j<4;j++){
  C42Entry*q=cache+((hash+j)&255);
  if(q->used!=generation){slot=q;break;}
  if(memcmp(q->in,in,32)||memcmp(q->in+40,in+40,8))continue;
  if(memcmp(q->body0,a,0x208)||memcmp(q->body1,b,0x208)||memcmp(q->material,m,0xa0))continue;
  /* Preserve this pair's scratch destination, whose storage remains native. */
  memcpy(in,q->out,32);memcpy(in+40,q->out+40,8);hits++;return;
 }
 unsigned char saved[48];memcpy(saved,p,48);c41Kernel(w,p,dt,thread);misses++;
 if(slot&&*(unsigned*)(in+40)==0&&*(void**)(in+32)==*(void**)(saved+32)){
  slot->used=generation;memcpy(slot->in,saved,48);memcpy(slot->out,in,48);
  memcpy(slot->body0,a,0x208);memcpy(slot->body1,b,0x208);memcpy(slot->material,m,0xa0);
 }
}
'''+s[end:]
s=s.replace('c41Active=c41Observe&&((++c41Seq%8)==0);','if(++generation==0){memset(cache,0,sizeof(cache));generation=1;}c41Active=c41Observe;')
s=s.replace('C(c41Records>0);','C(hits>0);')
s=s.replace('printf("PAIR_RECORDS','printf("REUSE hits=%llu misses=%llu\\n",hits,misses);printf("PAIR_RECORDS')
compound='--compound' in sys.argv
debug='--debug-callback' in sys.argv
unguarded='--unguarded' in sys.argv
if not unguarded:
 needle='if(*(void**)(in+16))'
 assert s.count(needle)==1
 s=s.replace(needle,r'''void*sa=*(void**)((char*)a+0x200),*sb=*(void**)((char*)b+0x200);
 /* NewtonStaticCollisionSetDebugCallback RVA3820 verifies flag4000 and
    stores its callback at shape+98. Such callbacks remain authoritative. */
 if(((*(unsigned*)((char*)sa+0x58)&0x4000)&&*(void**)((char*)sa+0x98))||
    ((*(unsigned*)((char*)sb+0x58)&0x4000)&&*(void**)((char*)sb+0x98))){c41Kernel(w,p,dt,thread);return;}
'''+needle)
if debug:
 s=s.replace('static unsigned forces,contacts;', 'static unsigned forces,contacts;static unsigned debugCalls,debugReference[240];static void debugCallback(void){__atomic_fetch_add(&debugCalls,1,__ATOMIC_RELAXED);}')
 needle='end(floor,1);body(w,floor,mat);'
 assert s.count(needle)==1
 s=s.replace(needle,'end(floor,1);void(*setDebug)(void*,void*)=(void*)GetProcAddress(m,"NewtonStaticCollisionSetDebugCallback");C(setDebug);setDebug(floor,(void*)debugCallback);debugCalls=0;body(w,floor,mat);')
 s=s.replace('rr[i]=rejects;', 'rr[i]=rejects;debugReference[i]=debugCalls;')
 s=s.replace('rr[i]!=rejects)', 'rr[i]!=rejects||debugReference[i]!=debugCalls)')
if compound:
 needle='void(*autosleep)(void*,int)='
 assert s.count(needle)==1
 s=s.replace(needle,r'''void*(*compound)(void*,int,void**,int)=(void*)GetProcAddress(m,"NewtonCreateCompoundCollision");C(compound);float offset[16]={1,0,0,0,0,1,0,0,0,0,1,0,.4f,.1f,0,1};void*children[2]={c,sphere(w,.2f,.2f,.2f,0,offset)};c=compound(w,2,children,0);C(c);C(*(unsigned*)((char*)c+0x68)==5);
'''+needle)
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=180)
(r/('audit/cpu42-reuse-debug-guarded.json' if debug and not unguarded else 'audit/cpu42-reuse-debug.json' if debug else 'audit/cpu42-reuse-compound.json' if compound else 'audit/cpu42-reuse.json')).write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)
