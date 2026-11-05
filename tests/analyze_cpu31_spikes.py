"""Reconcile recorded Newton totals with individual native spans, without adding nested times."""
from pathlib import Path
import collections,json,struct,sys
p=Path(sys.argv[1])
raw=(p/'cpu14_events.bin').read_bytes()
h=struct.unpack_from('<6Q',raw)
assert not h[3]
events=collections.defaultdict(list)
for x in struct.iter_unpack('<6I3Q',raw[48:]):
    events[x[1]].append(x)
movement=list(struct.iter_unpack('<4I9f',(p/'cpu6_movement.bin').read_bytes()))
out=[]
for r in sorted(movement,key=lambda x:x[4],reverse=True)[:20]:
    spans=[x for x in events[r[1]] if x[0]==9]
    times=[1000*(x[7]-x[6])/h[1] for x in spans]
    assert abs(sum(times)-r[11])<.002,(r[1],sum(times),r[11])
    out.append(dict(frame=r[1],interval_ms=r[4],newton_total_ms=r[11],
        native_steps=len(spans),step_ms=times,
        candidate_steps=sum(x[2]//120%4 in (1,2) for x in spans),
        scene_cpu_ms=r[9],runtime_wait_ms=r[10],texture_completion_ms=r[12]))
report=dict(scope='Frame-exact reconciliation of top20 intervals. Newton spans match accumulator. Scene and texture timings can overlap; do not add nested categories. Multiple fixed steps establish catch-up work, not the cause of the initial delay.',spikes=out)
(p/'cpu31-spikes.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
