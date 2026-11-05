"""Same-session zero-result reuse comparison; contact history still evolves."""
from pathlib import Path
import json,struct,collections,statistics,math,sys
p=Path(sys.argv[1]);b=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',b);assert h[3]==0
rows=list(struct.iter_unpack('<6I3Q',b[48:]));assert len(rows)==h[2]
by={t:{r[2]:r for r in rows if r[0]==t} for t in (9,53,63,64,65,66)}
assert by[63] and all(len(by[t])==len(by[63]) for t in (53,64,65,66))
assert sum(r[8] for r in by[65].values())==0,'Shadow result mismatch'
args=json.loads((p/'build-receipt.json').read_text())['arguments'];shadow=not args['reuse_zero']
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={r[1]:(f(r[8]>>32),f(r[8]&0xffffffff)) for r in rows if r[0]==18}
theta='Theta' in json.loads((p/'identity.json').read_text())['scenario']
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
def region(r):
 if 5<=r[3]<=9:return 'held'
 if theta:return 'theta'
 if r[3]==10 and r[1] in pos:
  for i,a in enumerate(anchors):
   if math.hypot(pos[r[1]][0]-a[0],pos[r[1]][1]-a[1])<6:return ['centre','platform','zeppelin'][i]
 return 'setup'
def stats(v):
 v=sorted(v);return dict(n=len(v),mean=statistics.mean(v),p99=v[int(.99*(len(v)-1))],max=max(v))
groups=collections.defaultdict(list);fg=collections.defaultdict(list)
for step,r in by[63].items():
 if step not in by[9]:continue
 a=by[9][step];g=by[53][step];groups[(region(r),r[5])].append(dict(newton=1000*(a[7]-a[6])/h[1],generation=1000*(g[7]-g[6])/h[1],hits=r[8],eligible=by[64][step][8]))
 fg[r[1]].append(r)
movement={m[1]:m for m in struct.iter_unpack('<4I9f',(p/'cpu6_movement.bin').read_bytes())};frames=collections.defaultdict(list)
for frame,q in fg.items():
 modes=set((region(r),r[5]) for r in q)
 if frame in movement and len(modes)==1 and all(4<r[2]%97<93 for r in q):frames[next(iter(modes))].append(movement[frame])
out=dict(scope=__doc__,shadow=shadow,hits=sum(r[8] for r in by[63].values()),eligible=sum(r[8] for r in by[64].values()),shadow_duplicate_ms=sum(r[8] for r in by[66].values())*1000/h[1],groups=[],frames=[])
for (area,mode),q in sorted(groups.items()):out['groups'].append(dict(area=area,mode=mode,**{k:stats([v[k] for v in q]) for k in ('newton','generation')},hits=sum(v['hits'] for v in q),eligible=sum(v['eligible'] for v in q)))
for (area,mode),q in sorted(frames.items()):out['frames'].append(dict(area=area,mode=mode,interval=stats([m[4] for m in q]),scene=stats([m[9] for m in q]),runtime=stats([m[10] for m in q])))
out['reuse_exercised']=out['hits']>0
out['coverage']='reuse and fallback' if out['hits'] else 'fallback only; no reuse correctness or benefit established by this run'
if '--require-hits' in sys.argv:assert out['hits']>0,'Candidate never exercised'
(p/'cpu43-summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
