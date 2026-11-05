from pathlib import Path
import struct,json,sys,collections,statistics
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();magic,freq,count,dropped,skipped,filtered=struct.unpack_from('<6Q',raw)
assert magic==0x4350553134455654 and len(raw)==48+count*48 and freq
names={1:'render_wrapper',2:'scene_submit',3:'xr_begin_wait_locate',7:'gpu_scene',8:'physics_stage',9:'newton',10:'native_module',11:'completion_stage',12:'worker_wait',13:'texture_stage',14:'bitmap_cleanup',15:'map_stage',16:'gpu_texture_cpu_call',17:'input_stage'}
rows=[]
for kind,frame,step,phase,state,detail,a,b,identity in struct.iter_unpack('<6I3Q',raw[48:]):
 assert b>=a
 rows.append(dict(kind=names.get(kind,str(kind)),frame=frame,step=step,phase=phase,state=state,detail=detail,start=a,end=b,ms=(b-a)/(1e6 if kind==7 else freq/1000),identity=hex(identity)))
movement=list(struct.iter_unpack('<4I9f',(p/'cpu6_movement.bin').read_bytes()))
byframe=collections.defaultdict(list)
for r in rows:byframe[r['frame']].append(r)
spikes=[]
for m in sorted(movement,key=lambda m:m[4],reverse=True):
 if any(abs(m[1]-s['frame'])<4 for s in spikes):continue
 nearby=[r for f in range(max(0,m[1]-2),m[1]+2) for r in byframe[f]]
 spikes.append(dict(frame=m[1],phase=m[0],interval_ms=m[4],held=bool(m[2]),events=sorted(nearby,key=lambda r:r['ms'],reverse=True)[:22]))
 if len(spikes)==15:break
summary=[]
for (kind,detail),group in __import__('itertools').groupby(sorted(rows,key=lambda r:(r['kind'],r['detail'])),key=lambda r:(r['kind'],r['detail'])):
 v=sorted(r['ms'] for r in group);summary.append(dict(kind=kind,detail=detail,count=len(v),mean_ms=statistics.mean(v),p99_ms=v[int(.99*(len(v)-1))],max_ms=max(v)))
result=dict(scope='Actual OpenXR, synthetic controller input. Nested CPU spans are not additive. GPU duration is queued scene work, not compositor time; correlated by issuing frame. Neighbour spans establish coincidence, not causality. No image readback.',events=count,short_spans_filtered=filtered,dropped=dropped,gpu_skipped=skipped,summary=summary,spikes=spikes)
(p/'event-summary.json').write_text(json.dumps(result,indent=2))
assert not dropped,'Incomplete event capture: buffer overflow'
assert set(range(11)).issubset({r['phase'] for r in rows}),'Missing event phases'
assert any(r['kind']=='gpu_scene' for r in rows),'No GPU samples'
print('Events',count,'dropped',dropped,'GPU skipped',skipped)
for s in sorted(summary,key=lambda r:r['max_ms'],reverse=True)[:14]:print(s)
print('Worst intervals:',[(s['frame'],s['phase'],round(s['interval_ms'],2)) for s in spikes[:8]])
