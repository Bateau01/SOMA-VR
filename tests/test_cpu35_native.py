"""Native scoped main-clock observer parity, not full-game coverage."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu35-native';b.mkdir(exist_ok=True)
s=(r/'tests/cpu34_native_fixture.c').read_text().replace('/* CPU34_OBSERVER */',(r/'tests/cpu34_cycles.inc').read_text())
s=s.replace('static unsigned samples,cycles;','static unsigned samples,cycles,points;static unsigned callers[32],callerCount;')
s=s.replace('if(kind==48){','if(kind==50){points++;unsigned i=0;for(;i<callerCount;i++)if(callers[i]==detail)break;if(i==callerCount&&callerCount<32)callers[callerCount++]=detail;}if(kind==51)C(0);if(kind==48){')
s=s.replace('/* Private scoped Newton timing,', 'static u32 cpuMainThread;static u32(__attribute__((ms_abi))*cpuThreadId)(void)= (void*)GetCurrentThreadId;\n'+(r/'tests/cpu35_point.inc').read_text()+'\n/* Private scoped Newton timing,',1)
s=s.replace('cpuCounter(&t);return (u32)((t/cpuFreq)', 'cpuCounter(&t);cpu35_point(__builtin_return_address(0),t);return (u32)((t/cpuFreq)',1)
s=s.replace('int main(){','int main(){cpuMainThread=GetCurrentThreadId();',1)
s=s.replace('C(samples>0&&cycles>0);','C(samples>0&&cycles>0&&points>0);printf("NATIVE_POINTS %u callers",points);for(unsigned j=0;j<callerCount;j++)printf(" %x",callers[j]);printf("\\n");')
(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=60)
(r/'audit/cpu35-native-unit.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)

