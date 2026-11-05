from pathlib import Path
import struct,json,sys,math,statistics
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2] and not h[3]
f=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
positions={x[1]:(f(x[8]>>32),f(x[5]),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
steps={x[7]:x for x in rows if x[0]==9};counters={}
paired={x[8]:x[5] for x in rows if x[0]==32}
for x in rows:
 if x[0]==19:counters.setdefault(x[6],{})[x[5]]=x[8]
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)];first={}
for pos in positions.values():
 for i,a in enumerate(anchors):
  if math.hypot(pos[0]-a[0],pos[2]-a[1])<6:first[i]=min(first.get(i,pos[3]),pos[3])
records=[]
for end,c in counters.items():
 if paired and paired.get(end)!=1:continue
 if end not in steps or len(c)!=8:continue
 x=steps[end];pos=positions.get(x[1]);region=-1
 if pos:
  for i,a in enumerate(anchors):
   if math.hypot(pos[0]-a[0],pos[2]-a[1])<6 and pos[3]>=first[i]+5*h[1]:region=i
 records.append(dict(frame=x[1],step=x[2],phase=x[3],region=region,position=pos[:3] if pos else None,wall_ms=1000*(x[7]-x[6])/h[1],counter_ms=[c[i]/1000 for i in range(8)]))
regions=[]
for i in range(3):
 q=[x for x in records if x['region']==i];regions.append(dict(region=i,slow_steps=len(q),mean_ms=[statistics.mean(x['counter_ms'][k] for x in q) for k in range(8)] if q else [],max_ms=[max(x['counter_ms'][k] for x in q) for k in range(8)] if q else [],slowest=sorted(q,key=lambda x:x['wall_ms'],reverse=True)[:8]))
report=dict(scope='Native Newton microsecond counters for steps exceeding1ms only; overlapping stages, do not sum; reference header labels pending binary call-path validation. Not optimisation performance gain.',events=h[2],dropped=h[3],sampled_steps=len(records),nonzero=sum(any(x['counter_ms']) for x in records),mean_wall_minus_total_ms=statistics.mean(x['wall_ms']-x['counter_ms'][0] for x in records) if records else None,regions=regions,slowest=sorted(records,key=lambda x:x['wall_ms'],reverse=True)[:10],process_exit=json.loads((p/'result.json').read_text())['process_exit_code'])
(p/'cpu25-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
