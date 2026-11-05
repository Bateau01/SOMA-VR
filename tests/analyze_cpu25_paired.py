from pathlib import Path
import struct,json,sys,math,statistics
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw)
rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and not h[3]
f=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
def region(row):
 v=pos.get(row[1])
 if v:
  for i,a in enumerate(anchors):
   if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:return i
 return -1
steps=[x for x in rows if x[0]==32];assert len(steps)>1000
blocks=[];i=0
while i+3<len(steps):
 q=steps[i:i+4]
 if [x[5] for x in q]!=[0,1,1,0]:i+=1;continue
 i+=4
 if len({region(x) for x in q})!=1 or len({x[3] for x in q})!=1:continue
 total=[1000*(x[7]-x[6])/h[1] for x in q]
 native=[1000*(x[8]-x[6])/h[1] for x in q]
 blocks.append(dict(region=region(q[0]),off_ms=(total[0]+total[3])/2,on_ms=(total[1]+total[2])/2,delta_ms=(total[1]+total[2]-total[0]-total[3])/2,native_delta_ms=(native[1]+native[2]-native[0]-native[3])/2))
assert len(blocks)>1000
out=[]
for reg in [-1,0,1,2]:
 q=[x for x in blocks if x['region']==reg];assert q
 out.append(dict(region=reg,blocks=len(q),off_mean_ms=statistics.mean(x['off_ms'] for x in q),on_mean_ms=statistics.mean(x['on_ms'] for x in q),paired_mean_delta_ms=statistics.mean(x['delta_ms'] for x in q),paired_median_delta_ms=statistics.median(x['delta_ms'] for x in q),paired_native_mean_delta_ms=statistics.mean(x['native_delta_ms'] for x in q)))
result=dict(scope='ABBA adjacent native steps, same game session. Total span includes scoped clock setup/counters/restore. Adjacent dynamics and scheduling still vary; no bitwise scene equivalence asserted. Observer overhead, not an optimisation.',events=h[2],dropped=h[3],steps=len(steps),regions=out,exit_code=json.loads((p/'result.json').read_text())['process_exit_code'])
(p/'cpu25-paired-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
