from pathlib import Path
import json,sys,struct,statistics,math
roots=[Path(x) for x in sys.argv[1:]]
assert len(roots)==2
receipts=[json.loads((p/'build-receipt.json').read_text()) for p in roots]
a,b=[dict(x['arguments']) for x in receipts]
assert a.pop('newton_clock') is False and b.pop('newton_clock') is True
assert a==b, 'Unmatched build options'
out=[]
for p in roots:
 raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw)
 rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and h[3]==0
 f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
 pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
 regions=[]
 for anchor in [(10.25,18),(21.2501,49.167),(4.25,68.75)]:
  near={k:v for k,v in pos.items() if math.hypot(v[0]-anchor[0],v[1]-anchor[1])<6}
  assert near
  start=min(v[2] for v in near.values())+5*h[1]
  frames={k for k,v in near.items() if v[2]>=start}
  q=sorted(1000*(x[7]-x[6])/h[1] for x in rows if x[0]==9 and x[1] in frames)
  assert q
  regions.append(dict(steps=len(q),mean_ms=statistics.mean(q),p99_ms=q[int(.99*(len(q)-1))],max_ms=q[-1],over1ms=sum(x>1 for x in q)))
 out.append(dict(capture=str(p),regions=regions,exit_code=json.loads((p/'result.json').read_text())['process_exit_code']))
result=dict(scope='Matched options, all recorded native Newton steps per region after five-second settling exclusion. Sequential runs are not deterministic; max differences alone do not prove clock overhead. No optimisation gain claimed.',runs=out)
target=roots[1]/'cpu25-clock-comparison.json';target.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
