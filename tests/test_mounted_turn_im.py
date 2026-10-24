from pathlib import Path
import ast,re,zipfile,subprocess,sys,json
r=Path(__file__).resolve().parents[1];b=r/'build/im';b.mkdir(exist_ok=True)
tree=ast.parse((r/'tests/test_grab_lifetime_il.py').read_text());head=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='head' for t in n.targets))
with zipfile.ZipFile(r.parent/'release-IL/SOMA-VR-1.0.9-S26IL-Source.zip') as z:old=z.read(next(n for n in z.namelist() if n.endswith('/source/s26n.c'))).decode()
new=(r/'source/s26n.c').read_text();results=[]
for label,s,want in [('IL',old,0),('IM',new,1)]:
 a=s.index('static void s26il_reconcile_grab_shell(');helper=s[a:s.index('static void h5729_state_boundary_observe',a)]
 a=s.index('static i32 h5755cj_grab_look_sample_allowed(void){');sample=s[a:s.index('\n}',a)+2]
 look=re.search(r'    i32 h5755cjGrabLookAllowed=.*?\?1:0;',s,re.S).group(0)
 extras='''
static int g_h30NativeUseHand=0,g_h5755ceNativeSwingDoorActive[2],g_h45NativeButtonReleased[2];
static unsigned g_h5755cjGrabLookSampleFrames,g_h5755dzSwingDoorLookSampleFrames;
'''
 main='''
static int dispatch_look_allowed(void){int stateKind=4;
'''+look+'''return h5755cjGrabLookAllowed;}
int main(){for(int h=0;h<2;h++){seed();sameOwnerHeld[h]=1;g_h30NativeMouseDown=1;
s26il_reconcile_grab_shell(4);
assert(h5755cj_grab_look_sample_allowed()==WANT);assert(dispatch_look_allowed()==WANT);
sameOwnerHeld[h]=0;g_h30NativeMouseDown=0;s26il_reconcile_grab_shell(4);assert(!g_h5755chGrabStateActive);
}return 0;}
'''.replace('WANT',str(want))
 c=b/(label+'_turn.c');c.write_text(head+extras+helper+sample+main);exe=c.with_suffix('.exe')
 subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 results.append({'build':label,'look_sample_and_dispatch_allowed_while_held':bool(want),'release_clears_owner':True,'scope':'compiled production predicates with mocked native state and same-owner physical hold; both hands; no headset input'})
(r/'audit/IM-user-2004/turn-regression.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
