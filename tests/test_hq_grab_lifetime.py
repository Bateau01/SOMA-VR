"""Archived HQ source test: inject the logged stale-owner state; exercise actual observer fast path and acquisition queue. Mocked engine, no game replay."""
from pathlib import Path
import ast,re,subprocess,sys,json
r=Path(__file__).resolve().parents[1];out=r/'audit/HQ-grab-lifetime';b=r/'build/hq-source-audit'
tree=ast.parse((r/'tests/test_grab_lifetime_il.py').read_text());head=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='head' for t in n.targets))
results=[]
for label,path,expected in [('HQ',b/'source/s26n.c',False),('IL',r/'source/s26n.c',True)]:
 s=path.read_text();a=s.index('static void h5755em_queue_native_grab_semantics_ex(i32 hand,const void* body,const void* semanticBody,const float* contact,i32 late){');end=s.index('\nstatic void h5755ch_queue_native_grab_semantics(',a);queue=s[a:end]
 fast=re.search(r'    if\(st==g_h5729LastState&&mod==g_h5729LastModule&&sobj==g_h5729LastScriptObject\)[^\n]+',s).group(0)
 helper=''
 if expected:
  x=s.index('static void s26il_reconcile_grab_shell(');helper=s[x:s.index('\nstatic void h5729_state_boundary_observe',x)]
 mock='''
static void *g_h5729LastState=(void*)10,*g_h5729LastModule=(void*)20,*g_h5729LastScriptObject=(void*)30;
static const char *g_h5729LastModuleName="player/PlayerState_Normal.hps",*g_h5729LastClassName="cScrPlayerState_Normal";
static int h5729_kind_names(const char*a,const char*b){return 4;}
static void observed_unchanged_normal(void){void*st=g_h5729LastState,*mod=g_h5729LastModule,*sobj=g_h5729LastScriptObject;
'''+fast+'\n}\n'
 main='''
int main(void){float p[3]={0,0,0};
/* Seed the committed stale owner from the reported sequence, not a gameplay outcome. */
seed();g_h30NativeMouseDown=0;observed_unchanged_normal();
h5755em_queue_native_grab_semantics_ex(1,(void*)999,0,p,0);
assert(g_h5755chGrabPending[1].valid==EXPECTED);
assert(g_h5755chGrabSecondaryDifferent[1]==(1-EXPECTED));
return 0;}
'''.replace('EXPECTED','1' if expected else '0')
 c=b/(label+'_logged_state.c');exe=c.with_suffix('.exe');c.write_text(head+helper+mock+queue+main)
 subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 results.append({'version':label,'queue_created':expected,'foreign_owner_rejection':not expected,'scope':__doc__})
(out/'regression.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
