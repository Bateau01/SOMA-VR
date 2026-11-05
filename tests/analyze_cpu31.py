from pathlib import Path
import json,struct,sys,math,statistics,collections
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and not h[3]
assert json.loads((p/'build-receipt.json').read_text())['arguments']['local_proof_paired']
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18};anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
bins=collections.defaultdict(lambda:[[],[],[],[]]);allrows=[]
for x in rows:
 if x[0]!=9:continue
 v=pos.get(x[1]);region=-1
 if v:
  for i,a in enumerate(anchors):
   if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:region=i
 if region<0:continue
 block=x[2]//120%4;ms=1000*(x[7]-x[6])/h[1];bins[(region,x[2]//480)][block].append(ms);allrows.append((region,block,ms))
result=[]
for region in range(3):
 deltas=[]
 for (reg,_),q in bins.items():
  if reg!=region or not all(len(x)==120 for x in q):continue
  a=q[0]+q[3];b=q[1]+q[2];deltas.append(statistics.mean(b)-statistics.mean(a))
 modes=[]
 for mode in (0,1):
  q=sorted(x[2] for x in allrows if x[0]==region and (x[1] in (1,2))==bool(mode));assert q
  modes.append(dict(candidate=bool(mode),samples=len(q),mean_ms=statistics.mean(q),p99_ms=q[int(.99*(len(q)-1))]))
 assert len(deltas)>=5
 result.append(dict(region=region,modes=modes,complete_ABBA_blocks=len(deltas),paired_mean_delta_ms=statistics.mean(deltas),paired_median_delta_ms=statistics.median(deltas),block_deltas_ms=deltas))
out=dict(scope='Same-process original/candidate ABBA120-step blocks, native Newton wall time; complete480-step regional blocks only. Contact geometry and scheduling vary. Negative delta favours candidate. No reduction in contact sampling or solver accuracy.',regions=result,exit=json.loads((p/'result.json').read_text())['process_exit_code'])
(p/'cpu31-comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
