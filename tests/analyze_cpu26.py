from pathlib import Path
import struct,json,sys,statistics,math
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and not h[3]
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
records={x[7]:dict(frame=x[1],step=x[2],phase=x[3],threads=x[5],invalid=x[8],wall_ms=1000*(x[7]-x[6])/h[1],ticks=[0]*3,calls=[0]*3,max_ticks=[0]*3,region=-1) for x in rows if x[0]==34}
assert len(records)>1000 and all(x['invalid']==0 for x in records.values()),'Missing samples or OS-thread registry coverage failure'
for x in rows:
 if x[0] not in (33,35,36) or x[6] not in records:continue
 assert x[5]<3;records[x[6]][{33:'ticks',35:'calls',36:'max_ticks'}[x[0]]][x[5]]=x[8]
for x in records.values():
 x['callback_ms']=[1000*v/h[1] for v in x.pop('ticks')];x['callback_max_ms']=[1000*v/h[1] for v in x.pop('max_ticks')]
 v=pos.get(x['frame'])
 if v:
  x['position_xz']=v[:2]
  for i,a in enumerate(anchors):
   if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:x['region']=i
assert all(sum(x['calls'][k] for x in records.values())>0 for k in range(3)), 'An expected callback path was not observed'
regions=[]
for i in (-1,0,1,2):
 q=[x for x in records.values() if x['region']==i];slow=[x for x in q if x['wall_ms']>1]
 regions.append(dict(region=i,samples=len(q),slow_samples=len(slow),mean_callback_ms=[statistics.mean(x['callback_ms'][k] for x in q) for k in range(3)],slow_mean_callback_ms=[statistics.mean(x['callback_ms'][k] for x in slow) for k in range(3)] if slow else [],calls=[sum(x['calls'][k] for x in q) for k in range(3)],slowest=sorted(q,key=lambda x:x['wall_ms'],reverse=True)[:5]))
native=[x for x in rows if x[0]==9];deltas={i:[] for i in (-1,0,1,2)}
for j in range(1,len(native)-1):
 x=native[j];rec=records.get(x[7])
 if not rec:continue
 a,b=native[j-1],native[j+1]
 if a[7] in records or b[7] in records or a[3]!=x[3] or b[3]!=x[3]:continue
 # Adjacent steps are not identical simulations; this is an overhead sanity check.
 delta=1000*((x[7]-x[6])-.5*((a[7]-a[6])+(b[7]-b[6])))/h[1]
 deltas[rec['region']].append(delta)
bias=[dict(region=i,pairs=len(q),mean_ms=statistics.mean(q),median_ms=statistics.median(q)) for i,q in deltas.items() if q]
result=dict(scope='Sampled one in four synchronous Newton steps; callback CPU sums across workers are inclusive and not wall-time subtraction. Categories: native overlap chain including existing held/healing filter, HPL contact processing, VR hand overlap. Exact callback forwarding; no solver/filter changes.',events=h[2],dropped=h[3],threads=sorted({x['threads'] for x in records.values()}),observed_thread_counts=sorted({x[8].bit_count() for x in rows if x[0]==37}),sampled_minus_adjacent_unsampled=bias,samples=len(records),regions=regions,exit_code=json.loads((p/'result.json').read_text())['process_exit_code'])
result['hand_validation_candidate']=json.loads((p/'build-receipt.json').read_text())['arguments'].get('hand_validation',False)
(p/'cpu26-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
