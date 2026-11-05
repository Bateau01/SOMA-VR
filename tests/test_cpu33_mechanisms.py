"""Native Newton joint fixtures, modeled motor laws; not game permission/ownership tests."""
from pathlib import Path
import contextlib,io,json,sys
r=Path(__file__).resolve().parents[1]
p=r/'tests/test_mechanism_cadence_ir.py';s=p.read_text()
s=s.replace("torque=api('NewtonBodySetTorque',[P,FP]);records=[]", "set_threads=api('NewtonSetThreadsCount',[P,I]);torque=api('NewtonBodySetTorque',[P,FP]);records=[]")
assert s.count('w=create(None,None);clock=')==1
s=s.replace('w=create(None,None);clock=','w=create(None,None);set_threads(w,WORKERS);clock=')
s=s.replace("'peak_force':max(map(abs,forces))", "'peak_force':max(map(abs,forces)),'forces':forces,'targets':targets,'travels':travels")
s=s[:s.index("p=R/'docs/v109-evidence/mechanism_cadence_ir.json'")]
results=[]
for workers in (8,2):
    ns={'__file__':str(p),'__doc__':__doc__,'WORKERS':workers}
    with contextlib.redirect_stdout(io.StringIO()):exec(compile(s,str(p),'exec'),ns)
    results.append(ns['records'])
checks=[]
for a,b in zip(*results):
    assert (a['kind'],a['speed'],a['hz'])==(b['kind'],b['speed'],b['hz'])
    delta={k:max(abs(x-y) for x,y in zip(a[k],b[k])) for k in ('forces','targets','travels')}
    counts={k:(len(a[k]),len(b[k])) for k in delta}
    ok=all(x==y for x,y in counts.values()) and all(x==0 for x in delta.values())
    checks.append(dict(kind=a['kind'],speed=a['speed'],hz=a['hz'],max_absolute_delta=delta,counts=counts,exact=ok))
out=dict(scope=__doc__,workers=[8,2],checks=checks,passed=all(x['exact'] for x in checks))
(r/'audit/cpu33-mechanisms.json').write_text(json.dumps(out,indent=2))
print('Exact native joint/motor traces:',sum(x['exact'] for x in checks),'/',len(checks))
assert out['passed'],'Retained differences require investigation; do not treat as equivalent'
