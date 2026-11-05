"""Native observation test; no game permissions or campaign coverage."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1]; b=r/'build/cpu34-native'
b.mkdir(exist_ok=True)
s=(r/'tests/cpu34_native_fixture.c').read_text().replace('/* CPU34_OBSERVER */',(r/'tests/cpu34_cycles.inc').read_text())
(b/'cycles.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'cycles.c'),'-o',str(b/'cycles.exe')],check=True)
x=subprocess.run([str(b/'cycles.exe')],capture_output=True,text=True,timeout=60)
(r/'audit/cpu34-native-unit.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2))
print(x.stdout+x.stderr);raise SystemExit(x.returncode)
