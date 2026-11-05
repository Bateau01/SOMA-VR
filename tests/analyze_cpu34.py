"""OS thread cycles are not elapsed time; no cycles-to-ms conversion."""
from pathlib import Path
import collections,json,math,statistics,struct,sys
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw)
assert h[0]==0x4350553134455654 and not h[3]
rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2]
assert json.loads((p/'build-receipt.json').read_text())['arguments']['worker_cycles']
steps=collections.defaultdict(list)
for x in rows:steps[x[2]].append(x)
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
data=[]
for step,q in steps.items():
 outer=[x for x in q if x[0]==9]
 if len(outer)!=1:continue
 x=outer[0];v=pos.get(x[1]);region=-1
 if v:
  for i,a in enumerate(anchors):
   if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:region=i
 d=dict(step=step,frame=x[1],phase=x[3],region=region,wall_ms=1000*(x[7]-x[6])/h[1],sampled=False)
 sampled=[z for z in q if z[0]==48]
 if sampled:
  assert len(sampled)==1
  n=sampled[0][5];assert not sampled[0][8], 'Invalid thread handle or counter'
  cycles={z[5]:z[8] for z in q if z[0]==47};ids={z[5]:z[8] for z in q if z[0]==49}
  assert set(cycles)==set(ids)==set(range(n+1)) and len(set(ids.values()))==n+1
  worker=[cycles[i] for i in range(n)];total=sum(worker)
  d.update(sampled=True,workers=n,worker_cycles=worker,main_cycles=cycles[n],total_worker_cycles=total,maximum_worker_fraction=max(worker)/total if total else None)
 data.append(d)
by_step={d['step']:d for d in data};regions=[]
for region in range(3):
 q=[d for d in data if d['sampled'] and d['region']==region];assert len(q)>20
 near=[]
 for d in q:
  ns=[by_step.get(d['step']+o) for o in (-1,1)]
  if all(n and not n['sampled'] and n['region']==region for n in ns):near.append(d['wall_ms']-statistics.mean(n['wall_ms'] for n in ns))
 regions.append(dict(region=region,samples=len(q),median_wall_ms=statistics.median(d['wall_ms'] for d in q),median_worker_cycles=statistics.median(d['total_worker_cycles'] for d in q),median_main_cycles=statistics.median(d['main_cycles'] for d in q),sampled_minus_neighbour_ms=statistics.mean(near) if near else None,worst=sorted(q,key=lambda d:d['wall_ms'],reverse=True)[:8]))
out=dict(scope=__doc__,limitations='Cycle samples include measurement boundary skew. Main cycles and sampled wall include the initial query loop. Neighbour deltas are not exact overhead bounds. No stacks, exact waiting times or collision-only worker breakdown. No policy changes.',events=h[2],samples=sum(d['sampled'] for d in data),regions=regions)
(p/'cpu34-summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
