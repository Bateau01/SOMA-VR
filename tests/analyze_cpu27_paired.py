from pathlib import Path
import json,sys,statistics,struct,math,collections
p=Path(sys.argv[1]);receipt=json.loads((p/'build-receipt.json').read_text());assert receipt['arguments']['hand_validation_paired']
raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and not h[3]
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18};anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
records={x[7]:dict(frame=x[1],step=x[2],mode=int(x[2]//120%4 in (1,2)),wall_ms=1000*(x[7]-x[6])/h[1],invalid=x[8],calls=[0]*3,cpu=[0.]*3,region=-1) for x in rows if x[0]==34}
assert records and all(x['invalid']==0 for x in records.values())
for x in rows:
 if x[0] in (33,35) and x[6] in records:records[x[6]]['cpu' if x[0]==33 else 'calls'][x[5]]=1000*x[8]/h[1] if x[0]==33 else x[8]
for x in records.values():
 v=pos.get(x['frame'])
 if v:
  for i,a in enumerate(anchors):
   if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:x['region']=i
out=[]
for region in (0,1,2):
 q=[x for x in records.values() if x['region']==region];modes=[]
 for mode in (0,1):
  a=[x for x in q if x['mode']==mode];calls=sum(x['calls'][2] for x in a)
  modes.append(dict(candidate=bool(mode),samples=len(a),native_mean_ms=statistics.mean(x['wall_ms'] for x in a),hand_cpu_ms=statistics.mean(x['cpu'][2] for x in a),hand_calls=calls,cpu_us_per_call=1000*sum(x['cpu'][2] for x in a)/calls))
 bins=collections.defaultdict(lambda:[[],[]])
 for x in q:bins[tuple(x['calls'])][x['mode']].append(x)
 weight=0;wall=cpu=0.
 for a,b in bins.values():
  if not a or not b:continue
  w=min(len(a),len(b));weight+=w;wall+=w*(statistics.mean(x['wall_ms'] for x in b)-statistics.mean(x['wall_ms'] for x in a));cpu+=w*(statistics.mean(x['cpu'][2] for x in b)-statistics.mean(x['cpu'][2] for x in a))
 out.append(dict(region=['centre','platform','zeppelin'][region],modes=modes,equal_callback_count_weight=weight,matched_candidate_minus_baseline_wall_ms=wall/weight if weight else None,matched_candidate_minus_baseline_hand_cpu_ms=cpu/weight if weight else None))
result=dict(scope='Within-run ABBA120-step blocks; sampled1in4; region settling excluded. Equal counts do not guarantee equal contact geometry. Timings include private profiling overhead; not release FPS proof.',regions=out,events=h[2],drops=h[3],exit_code=json.loads((p/'result.json').read_text())['process_exit_code'])
(p/'cpu27-paired.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
