"""In-session scheduling comparison; scene/contact history still evolves."""
from pathlib import Path
import json,struct,statistics,collections,math,sys
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);assert h[3]==0
receipt=json.loads((p/'build-receipt.json').read_text())['arguments'];block_steps=97 if receipt.get('schedule_prime') else 120 if receipt.get('adaptive_sse') else 60
rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2]
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={r[1]:(f(r[8]>>32),f(r[8]&0xffffffff)) for r in rows if r[0]==18}
for kind in [9,53]:
 ids=[r[2] for r in rows if r[0]==kind];assert len(ids)==len(set(ids)),f'ambiguous multiple {kind} spans per step'
newton={r[2]:1000*(r[7]-r[6])/h[1] for r in rows if r[0]==9}
extra=collections.defaultdict(dict)
for r in rows:
 if r[0] in [54,55,56]:extra[r[2]][(r[0],r[5]>>16)]=1000*(r[7]-r[6])/h[1]
theta='Theta indoor physics' in json.loads((p/'identity.json').read_text())['scenario']
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
def region(r):
 if 5<=r[3]<=9:return 'held'
 if theta:return 'theta' if r[3] in [0,1,2,3,10] else None
 if r[3]!=10 or r[1] not in pos:return None
 v=pos[r[1]]
 for i,a in enumerate(anchors):
  if math.hypot(v[0]-a[0],v[1]-a[1])<6:return ['centre','platform','zeppelin'][i]
def stats(v):
 v=sorted(v);return dict(n=len(v),mean=statistics.mean(v),p99=v[int(.99*(len(v)-1))],max=max(v))
phase_groups=collections.defaultdict(list);groups=collections.defaultdict(list);bins=collections.defaultdict(list);blocks=collections.defaultdict(list);actual=collections.Counter()
for r in rows:
 if r[0]!=53:continue
 requested=(16 if r[5]&(1<<12) else 0) if r[5]&(1<<13) else r[5]&15;n=(r[5]>>4)&15;actual[(requested,n)]+=1;area=region(r)
 if area is None or r[2] not in newton:continue
 e=extra[r[2]];v=dict(step=r[2],pairs=r[8],jobs=n,job=1000*(r[7]-r[6])/h[1],newton=newton[r[2]],queue=e.get((54,0),0),join=e.get((55,0),0),worker_sum=sum(x for (k,i),x in e.items() if k==56),worker_max=max([x for (k,i),x in e.items() if k==56] or [0]))
 groups[(area,requested)].append(v)
 if 5<=r[3]<=9:phase_groups[(r[3],requested)].append(v)
 bucket=0 if r[8]<32 else 1 if r[8]<64 else 2 if r[8]<128 else 3 if r[8]<256 else 4
 bins[(area,bucket,requested)].append(v);blocks[(area,r[2]//(block_steps*(4 if receipt.get('adaptive_sse') else 8)),requested)].append(v)
def summarize(g):return [{**dict(zip(['area','mode'],k)),**{a:stats([v[a] for v in q]) for a in ['pairs','job','newton','queue','join','worker_sum','worker_max']}} for k,q in sorted(g.items())]
out=dict(scope=__doc__,dispatch=[dict(requested=k[0],actual=k[1],steps=v) for k,v in sorted(actual.items())],groups=summarize(groups),pair_bins=[dict(area=k[0],bucket=k[1],mode=k[2],samples=len(q),job=stats([v['job'] for v in q]),newton=stats([v['newton'] for v in q])) for k,q in sorted(bins.items())],balanced_blocks=[])
for area,block in sorted(set((k[0],k[1]) for k in blocks)):
 q={mode:blocks.get((area,block,mode),[]) for mode in ([0,16] if any(r[0]==53 and r[5]&(1<<13) for r in rows) else [0,2,4,8])}
 if all(len(v)>=60 for v in q.values()):out['balanced_blocks'].append(dict(area=area,block=block,modes={mode:dict(samples=len(v),pairs=statistics.mean(z['pairs'] for z in v),job=statistics.mean(z['job'] for z in v),newton=statistics.mean(z['newton'] for z in v)) for mode,v in q.items()}))
movement={m[1]:m for m in struct.iter_unpack('<4I9f',(p/'cpu6_movement.bin').read_bytes())}
frame_modes=collections.defaultdict(list)
for r in rows:
 if r[0]==53 and region(r) is not None:frame_modes[r[1]].append(r)
fg=collections.defaultdict(list)
for frame,q in frame_modes.items():
 if frame not in movement or any(not 4<(r[2]%block_steps)<block_steps-4 for r in q):continue
 modes=set((region(r),((16 if r[5]&(1<<12) else 0) if r[5]&(1<<13) else r[5]&15)) for r in q)
 if len(modes)==1:fg[next(iter(modes))].append(movement[frame])
out['held_phase_groups']=[dict(phase=k[0],mode=k[1],parallel_steps=sum(v['jobs']>0 for v in q),generation=stats([v['job'] for v in q]),newton=stats([v['newton'] for v in q])) for k,q in sorted(phase_groups.items())]
out['frame_groups']=[dict(area=k[0],mode=k[1],metrics={label:stats([m[i] for m in q]) for i,label in [(4,'interval'),(9,'scene'),(10,'runtime'),(11,'newton')]}) for k,q in sorted(fg.items())]
if any(r[0]==53 and r[5]&(1<<13) for r in rows):
 assert any(x['requested']==16 and x['actual']>0 and x['steps']>0 for x in out['dispatch']), 'Adaptive scheduling was not exercised'
 assert any(x['requested']==0 and x['steps']>0 for x in out['dispatch'])
else:assert all(any(x['actual']==n and x['steps']>0 for x in out['dispatch']) for n in [2,4,8])
assert json.loads((p/'result.json').read_text())['process_exit_code']==0
(p/'cpu37-summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out['dispatch']));print('AREA MODE N PAIRS JOBms NEWTONms QUEUEms JOINms MAXWORKERms')
for q in out['groups']:print(q['area'],q['mode'],q['job']['n'],*[round(q[k]['mean'],6) for k in ['pairs','job','newton','queue','join','worker_max']])
print('balanced blocks',len(out['balanced_blocks']))

for q in out["frame_groups"]:print("FRAME",q["area"],q["mode"],*[round(q["metrics"][k]["mean"],5) for k in ["interval","scene","runtime","newton"]])
