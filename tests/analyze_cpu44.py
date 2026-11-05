"""Verify guarded-adapter execution; does not establish a performance comparison."""
from pathlib import Path
import sys,struct,json
p=Path(sys.argv[1]);data=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',data)
assert h[3]==0,'Lost diagnostic events'
rows=list(struct.iter_unpack('<6I3Q',data[48:]));assert len(rows)==h[2]
jobs=[r for r in rows if r[0]==67];assert jobs,'Guarded job path never executed'
hits=sum(r[8] for r in jobs)
assert 'CPU HAND MESH: verified same-job zero-result reuse enabled' in (p/'hpl3vr.log').read_text(errors='replace')
out=dict(scope=__doc__,jobs=len(jobs),reuses=hits,coverage='reuse and fallback' if hits else 'fallback only')
if '--require-hits' in sys.argv:assert hits,'No reuse exercised'
(p/'cpu44-summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
