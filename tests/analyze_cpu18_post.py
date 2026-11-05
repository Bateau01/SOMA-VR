from pathlib import Path
import struct,json,sys,collections
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes();freq=struct.unpack_from('<6Q',raw)[1];rows=list(struct.iter_unpack('<6I3Q',raw[48:]))
parents=sorted([v for v in rows if v[0]==10 and v[5]==6 and v[8]==0x6c2b58],key=lambda v:v[7]-v[6],reverse=True)
report=[]
for p in parents[:10]:
 children=[v for v in rows if v[0]==21 and p[6]<=v[6] and v[7]<=p[7]]
 snapshots=[v for v in rows if v[0]==22 and v[6]==p[6]]
 report.append(dict(frame=p[1],phase=p[3],parent_ms=(p[7]-p[6])*1000/freq,branches=[dict(flags=v[5],pending=v[8]) for v in snapshots],observed_children=[dict(stage=v[5],ms=(v[7]-v[6])*1000/freq) for v in children]))
stages={i:dict(count=len(v),max_ms=max(v),total_ms=sum(v)) for i in range(7) if (v:=[(x[7]-x[6])*1000/freq for x in rows if x[0]==21 and x[5]==i])}
result=dict(scope='Main-thread diagnostic native calls, nested timings not additive. Short child spans filtered. Flags:1=switch-request,2=pending-stream-map,4=stream-mode,8=resource-list,16=reload-request.',stages=stages,spikes=report)
(r/'post-attribution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
