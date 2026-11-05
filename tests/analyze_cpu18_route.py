from pathlib import Path
import struct,json,sys,re,math,statistics
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes()
magic,freq,count,dropped,skip,filtered=struct.unpack_from('<6Q',raw)
assert magic==0x4350553134455654 and len(raw)==48+48*count and not dropped
def f(v):return struct.unpack('<f',struct.pack('<I',v))[0]
points=[]
for k,frame,step,phase,state,d,a,b,v in struct.iter_unpack('<6I3Q',raw[48:]):
 if k==18:
  p=[f(v>>32),f(d),f(v&0xffffffff)];assert all(math.isfinite(x) for x in p)
  points.append(dict(frame=frame,phase=phase,t=a,position=p))
assert points,'Missing frame-linked world positions'
log=(r/'hpl.log').read_text(errors='replace')
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
regions=[]
movement={m[1]:m for m in struct.iter_unpack('<4I9f',(r/'cpu6_movement.bin').read_bytes())}
for i,anchor in enumerate(anchors):
 q=[p for p in points if math.hypot(p['position'][0]-anchor[0],p['position'][2]-anchor[1])<6]
 first=min((p['t'] for p in q),default=0)
 q=[p for p in q if p['t']>=first+5*freq]
 extent=[max((p['position'][j] for p in q),default=0)-min((p['position'][j] for p in q),default=0) for j in (0,2)]
 frames=[movement[p['frame']] for p in q if p['frame'] in movement]
 timing={}
 for j,label in [(4,'frame_interval'),(9,'scene_cpu'),(10,'xr_wait'),(11,'newton'),(12,'texture_completion')]:
  values=sorted(m[j] for m in frames)
  timing[label]=dict(mean=statistics.mean(values),p99=values[int(.99*(len(values)-1))],max=max(values)) if values else None
 regions.append(dict(region=i,frames=len(q),xz_extent=extent,walked=bool(q) and max(extent)>1,timing_ms=timing))
summary=json.loads((r/'event-summary.json').read_text())
spikes=[]
for spike in summary['spikes']:
 p=min(points,key=lambda p:abs(p['frame']-spike['frame']))
 spikes.append(dict(frame=spike['frame'],interval_ms=spike['interval_ms'],position=p['position'],nearest_position_frame=p['frame'],events=spike['events']))
result=dict(scope='Real OpenXR, synthetic initial controller replay followed by staged native character Move tests. Explicit setup relocations between regions; first5seconds excluded from regional extents. Local motion respects collision. Positions are camera world coordinates. Story intro omitted; not full progression validation.',complete=all(x['walked'] for x in regions) and 'CPU18_ROUTE_COMPLETE' in log,regions=regions,point_count=len(points),bounds=[[min(p['position'][i] for p in points),max(p['position'][i] for p in points)] for i in range(3)],spikes=spikes)
(r/'route-summary.json').write_text(json.dumps(result,indent=2))
print({k:v for k,v in result.items() if k!='spikes'})
for s in spikes[:5]:print('Spike',s['frame'],s['interval_ms'],s['position'])
assert result['complete'],'Incomplete route coverage; inspect obstacles and replan rather than teleporting'
