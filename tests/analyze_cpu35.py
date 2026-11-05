"""Native clock stage intervals; nested wall spans are not additive frame costs."""
from pathlib import Path
import collections,json,struct,sys,statistics
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);assert not h[3]
rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2]
assert json.loads((p/'build-receipt.json').read_text())['arguments']['main_native_clock']
assert not any(x[0]==51 for x in rows), 'Invalid cycle read or caller'
steps=collections.defaultdict(list)
for x in rows:steps[x[2]].append(x)
records=[];buckets=collections.defaultdict(list)
for step,q in steps.items():
 points=[x for x in q if x[0]==50]
 if not points:continue
 samples=[x for x in q if x[0]==48];assert len(samples)==1 and not samples[0][8]
 spans=[]
 for a,b in zip(points,points[1:]):
  assert b[6]>=a[6] and b[8]>=a[8]
  span=dict(boundary=hex(a[5])+' -> '+hex(b[5]),wall_ms=1000*(b[6]-a[6])/h[1],main_cycles=b[8]-a[8]);spans.append(span);buckets[span['boundary']].append(span)
 records.append(dict(step=step,frame=points[0][1],phase=points[0][3],wall_ms=1000*(samples[0][7]-samples[0][6])/h[1],points=len(points),spans=spans))
assert len(records)>100
out=dict(scope=__doc__,samples=len(records),boundaries={k:dict(count=len(v),mean_ms=statistics.mean(x['wall_ms'] for x in v),mean_main_cycles=statistics.mean(x['main_cycles'] for x in v),max_ms=max(x['wall_ms'] for x in v)) for k,v in buckets.items()},worst=sorted(records,key=lambda x:x['wall_ms'],reverse=True)[:20],limitations='Boundary timing includes observer query/event cost. Stages encompass multiple native functions; this does not identify a specific costly instruction or lock. Sampled1/32; no performance improvement claimed.')
(p/'cpu35-summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
