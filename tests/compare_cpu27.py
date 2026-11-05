from pathlib import Path
import json,sys,statistics,struct,math
def load(p):
 p=Path(p);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and h[3]==0
 f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
 pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18};anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
 first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors];out=[]
 summary=json.loads((p/'cpu26-summary.json').read_text())
 for i,a in enumerate(anchors):
  samples=[]
  for x in rows:
   v=pos.get(x[1])
   if x[0]==9 and v and math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:samples.append(1000*(x[7]-x[6])/h[1])
  samples.sort();s=next(q for q in summary['regions'] if q['region']==i)
  out.append(dict(region=['centre','platform','zeppelin'][i],steps=len(samples),mean_ms=statistics.mean(samples),p99_ms=samples[int(.99*(len(samples)-1))],over_1ms=sum(x>1 for x in samples),hand_callback_cpu_ms=s['mean_callback_ms'][2],sampled_hand_calls=s['calls'][2],sampled_steps=s['samples']))
 return dict(path=str(p),regions=out,exit_code=summary['exit_code'],candidate=summary.get('hand_validation_candidate',False))
result=dict(scope='Sequential isolated scripted routes; first5seconds excluded per region; native step wall time separate from inclusive callback CPU across workers; not a matched frame-for-frame or campaign correctness proof',runs=[load(p) for p in sys.argv[1:]])
print(json.dumps(result,indent=2))
