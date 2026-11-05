"""Run actual Newton 8-versus-2 worker contact parity using the retained native fixture."""
from pathlib import Path
import ast,json,subprocess,sys
r=Path(__file__).resolve().parents[1];b=r/'build/cpu33-native';b.mkdir(exist_ok=True)
tree=ast.parse((r/'tests/test_cpu25_native.py').read_text())
parts={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('pre','post')}
assert parts['post'].count('threads(w,1);')==1
post=parts['post'].replace('threads(w,1);','threads(w,mode?2:8);').replace('PASS actualNewton60/120Hz480 falling/resting contact trajectories exact;','PASS 8-versus2workers actualNewton60/120Hz480 falling/resting contact trajectories exact;')
(b/'test.c').write_text(parts['pre']+(r/'tests/cpu25_clock.inc').read_text()+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=60);print(x.stdout+x.stderr)
(r/'audit/cpu33-native-unit.json').write_text(json.dumps(dict(scope='Actual Newton DLL sphere-floor trajectories 8 versus2workers, exact per-step transforms and contact/force counts at60/120Hz. Not dense assemblies or game interactions.',exit=x.returncode,output=x.stdout+x.stderr),indent=2));raise SystemExit(x.returncode)
