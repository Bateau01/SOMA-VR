from pathlib import Path
import sys,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1]
production='--production' in sys.argv
p=r/('source/hand_recovery_jb.inc' if production else 'tests/jb_recovery_engine_candidate.inc')
s=p.read_text().replace('#include "../tests/jb_recovery_policy.inc"',(r/'tests/jb_recovery_policy.inc').read_text())
if production:s=s.replace('#include "hand_recovery_policy_jb.inc"',(r/'source/hand_recovery_policy_jb.inc').read_text())
code=(r/'tests/jb_recovery_dispatch.cpp.in').read_text().replace('@IMPLEMENTATION@',s)
out=r/'build/jb_recovery_dispatch.cpp';out.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(out),'-o',str(out.with_suffix('.exe'))],check=True)
v=subprocess.run([str(out.with_suffix('.exe'))],capture_output=True,text=True)
(r/('audit/jb-recovery-production-dispatch.json' if production else 'audit/jb-recovery-dispatch.json')).write_text(json.dumps(dict(scope='Extracted current engine candidate with mocked engine calls; not real geometry',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),exit=v.returncode,output=v.stdout+v.stderr),indent=2))
print(v.stdout+v.stderr);raise SystemExit(v.returncode)
