"""Separate matched-option runs; not identical controller/contact history."""
from pathlib import Path
import json,sys,re,struct
source=(Path(__file__).with_name('compare_cpu33.py')).read_text()
ns={};exec(source[:source.index('a,b=map(analyze')],ns)
a,b=[ns['analyze'](p) for p in sys.argv[1:3]]
x,y=dict(a['settings']),dict(b['settings']);assert not x.pop('parallel_sse');assert y.pop('parallel_sse');assert x==y
paths=list(map(Path,sys.argv[1:3]))
assert (paths[0]/'fixture-user-settings.cfg').read_bytes()==(paths[1]/'fixture-user-settings.cfg').read_bytes()
assert json.loads((paths[0]/'test-command.json').read_text())==json.loads((paths[1]/'test-command.json').read_text())
assert a['exit']==b['exit']==0
assert 'CPU36 private SSE job dispatch create 0 enable 0' in (paths[1]/'hpl3vr.log').read_text(errors='replace')
dispatch=[x[8] for x in struct.iter_unpack('<6I3Q',(paths[1]/'cpu14_events.bin').read_bytes()[48:]) if x[0]==52];assert len(dispatch)==1 and dispatch[0]>0
ph=[json.loads((p/'movement-summary.json').read_text())['phases'] for p in paths]
held=[]
for q in ph:
 q=[v for v in q if 5<=v['phase']<=9];assert all(v['held']==v['frames'] and v['hands_min']==2 for v in q)
 n=sum(v['frames'] for v in q);held.append(dict(frame_ms=sum(v['mean_ms']*v['frames'] for v in q)/n,newton_per_frame_ms=sum(v['attribution_mean_ms']['newton']*v['frames'] for v in q)/n))
out=dict(scope=__doc__,reference=a,candidate=b,held=held,delta_ms=[dict(region=i,newton_mean=b['steps'][i]['mean_ms']-a['steps'][i]['mean_ms'],newton_p99=b['steps'][i]['p99_ms']-a['steps'][i]['p99_ms'],frame_mean=b['route'][i]['timing_ms']['frame_interval']['mean']-a['route'][i]['timing_ms']['frame_interval']['mean']) for i in range(3)])
(paths[1]/'cpu36-comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(regions=out['delta_ms'],held=held),indent=2))
