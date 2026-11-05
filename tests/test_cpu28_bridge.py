from pathlib import Path
import ast,subprocess,sys,json,hashlib
from cpu28_transform import transform
r=Path(__file__).resolve().parents[1]
tree=ast.parse((r/'tests/test_cpu24_bridge.py').read_text());parts={}
for node in tree.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('pre','post'):parts[node.targets[0].id]=ast.literal_eval(node.value)
bridge=transform((r/'tests/cpu23_buffers.inc').read_text())
prefix=bridge[:bridge.index('/* Private CPU23')]
core='static u32 cpu23Scope'+bridge.split('static u32 cpu23Scope',1)[1].split('static void cpu23_install(void){')[0]
pre=parts['pre']+'''static u32 thread=1,cpuMainThread=1;static void*context=(void*)123;
static u32 tid(void){return thread;}static u32(*cpuThreadId)(void)=tid;
static void*ctx(void){return context;}static void*(*p_s26efContext)(void)=ctx;
'''
post=parts['post'].replace('static int failmap;','static int failmap,nested;static unsigned packs;')
post=post.replace('C(d==mapped&&n==65536);','C(d==mapped&&n==65536);packs++;')
post=post.replace('(enabled&&cpu23Eligible&&object[0xed])','(thread==1&&context==cpu28InstallContext&&cpu23Scope==1&&cpu23Eligible&&object[0xed])')
post=post.replace('C(p==object);cpu23_data','C(p==object);if(nested&&cpu23Scope==1){nested=0;cpu23_upload(p);nested=1;}cpu23_data')
post=post.replace('int main(){','int main(){cpu28GetContext=(void*)ctx;cpu28InstallContext=(void*)123;')
post=post.replace('C(calls==64);puts(','''C(calls==64);C(packs==2);
enabled=0;cpu23Eligible=1;cpu24Expected=object;object[0xed]=1;failmap=0;
unsigned before=packs;context=(void*)456;cpu23_upload(object);C(packs==before&&cpu23Scope==0&&cpu24Object==0);
context=(void*)123;thread=2;cpu23_upload(object);C(packs==before&&cpu23Scope==0&&cpu24Object==0);
thread=1;nested=1;cpu23_upload(object);C(packs==before+1&&cpu23Scope==0&&cpu24Object==0&&cpu28Context==0);nested=0;
cpu23_upload(object);C(packs==before+2);puts(''')
post=post.replace('PASS bridge 16 cases:', 'PASS independent bridge: recorder OFF still packs; foreign context/thread fallback; nested forwarding/outer scope recovery; 16 base cases:')
b=r/'build/cpu28-bridge';b.mkdir(exist_ok=True);(b/'test.c').write_text(pre+prefix+core+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True);print(x.stdout+x.stderr)
(r/'audit/cpu28-bridge.json').write_text(json.dumps(dict(scope='Compiled actual generated bridge with native/GL mocks; not native engine or GPU output proof',exit=x.returncode,output=x.stdout+x.stderr,generated_bridge_sha256=hashlib.sha256(bridge.encode()).hexdigest()),indent=2));raise SystemExit(x.returncode)
