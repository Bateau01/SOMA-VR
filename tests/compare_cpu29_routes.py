"""Compare identical Delta route fixtures without promoting noise to an FPS claim."""
from pathlib import Path
import json,sys
r=Path(__file__).resolve().parents[1]
a,b=[r/'audit/delta-integration'/x for x in sys.argv[1:3]]
ra,rb=[json.loads((p/'build-receipt.json').read_text()) for p in (a,b)]
assert not ra['arguments']['streaming_release'] and rb['arguments']['streaming_release']
aa,bb=[dict(q['arguments']) for q in (ra,rb)]
aa.pop('streaming_release');bb.pop('streaming_release');assert aa==bb
assert ra['source_hashes']==rb['source_hashes']
for p in (a,b):
 cmd=json.loads((p/'test-command.json').read_text());assert '--movement-visual' not in cmd and '--delta-route' in cmd
 assert json.loads((p/'result.json').read_text())['process_exit_code']==0
 assert json.loads((p/'route-summary.json').read_text())['complete']
 assert (p/'movement-summary.json').is_file()
assert json.loads((a/'test-command.json').read_text())==json.loads((b/'test-command.json').read_text())
q=[json.loads((p/'route-summary.json').read_text()) for p in (a,b)]
rows=[]
for x,y in zip(q[0]['regions'],q[1]['regions']):
 rows.append(dict(region=x['region'],reference=x['timing_ms'],candidate=y['timing_ms'],candidate_minus_reference_ms={k:{metric:y['timing_ms'][k][metric]-v[metric] for metric in ('mean','p99','max')} for k,v in x['timing_ms'].items()}))
result=dict(reference=a.name,candidate=b.name,scope='Separate actual OpenXR sessions, identical synthetic route/settings, no image readback; live tracking and scheduling are nondeterministic. Regional scene/physics/runtime spans can overlap. This is regression evidence, not a statistically established sustained-FPS benefit.',regions=rows)
(r/'audit/cpu29-route-comparison.json').write_text(json.dumps(result,indent=2))
for row in rows:print(row['region'],row['candidate_minus_reference_ms'])
