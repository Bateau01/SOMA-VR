"""Separate matched-option native runs; do not imply identical contact history."""
from pathlib import Path
import json,struct,sys,math,statistics,collections
def analyze(p):
    p=Path(p);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);assert not h[3]
    rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2]
    f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
    pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
    anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
    first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
    bins=[[] for _ in range(3)]
    for x in rows:
        if x[0]!=9 or x[1] not in pos:continue
        v=pos[x[1]]
        for i,a in enumerate(anchors):
            if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:bins[i].append(1000*(x[7]-x[6])/h[1])
    stats=[]
    for q in bins:
        q.sort();assert len(q)>1000
        stats.append(dict(steps=len(q),mean_ms=statistics.mean(q),p99_ms=q[int(.99*(len(q)-1))],max_ms=max(q)))
    return dict(capture=str(p),settings=json.loads((p/'build-receipt.json').read_text())['arguments'],steps=stats,route=json.loads((p/'route-summary.json').read_text())['regions'],exit=json.loads((p/'result.json').read_text())['process_exit_code'])
a,b=map(analyze,sys.argv[1:3]);assert not a['settings']['newton_workers_2'] and b['settings']['newton_workers_2']
aa=dict(a['settings']);bb=dict(b['settings']);aa.pop('newton_workers_2');bb.pop('newton_workers_2');assert aa==bb,'Unmatched build settings'
assert a['exit']==b['exit']==0
out=dict(scope='Separate native OpenXR synthetic-controller runs with matching build/scenario options. Contacts, headset pose and scheduling can vary. No causal or universal speedup guarantee.',reference=a,candidate=b,
    delta_ms=[dict(region=i,newton_mean=b['steps'][i]['mean_ms']-a['steps'][i]['mean_ms'],newton_p99=b['steps'][i]['p99_ms']-a['steps'][i]['p99_ms'],frame_mean=b['route'][i]['timing_ms']['frame_interval']['mean']-a['route'][i]['timing_ms']['frame_interval']['mean']) for i in range(3)])
(Path(sys.argv[2])/'cpu33-comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['delta_ms'],indent=2))
