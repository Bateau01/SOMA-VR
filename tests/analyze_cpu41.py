"""Sampled original-serial pair costs. No cross-run body identity assumptions."""
from pathlib import Path
import json,struct,sys,collections,statistics
p=Path(sys.argv[1]);b=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',b);assert not h[3]
r=list(struct.iter_unpack('<6I3Q',b[48:]));assert len(r)==h[2] and not any(x[0]==59 for x in r),'Pair capture overflow'
a=[x for x in r if x[0]==57];z=[x for x in r if x[0]==58];assert len(a)==len(z)>0
steps=collections.defaultdict(list);groups=collections.defaultdict(list)
for x,y in zip(a,z):
 assert x[1:8]==y[1:8]
 d=x[5];v=dict(step=x[2],frame=x[1],phase=x[3],body0=hex(x[8]),body1=hex(y[8]),types=[d&31,(d>>5)&31],hands=(d>>10)&3,held=(d>>12)&3,contacts=d>>16,ms=1000*(x[7]-x[6])/h[1])
 steps[x[2]].append(v);groups[(v['body0'],v['body1'],*v['types'],v['hands'],v['held'])].append(v)
spans={x[2]:x for x in r if x[0]==53};assert all(((x[5]>>4)&15)==0 for x in spans.values()),'Not original serial'
for step,q in steps.items():
 assert len(q)==spans[step][8],(step,len(q),spans[step][8])
 assert sum(v['ms'] for v in q)<=1000*(spans[step][7]-spans[step][6])/h[1]+.001
out=dict(scope=__doc__,pairs=len(a),sampled_steps=len(steps),groups=[],slow_steps=[])
for k,q in groups.items():
 ms=sorted(v['ms'] for v in q);out['groups'].append(dict(body0=k[0],body1=k[1],types=list(k[2:4]),hands=k[4],held=k[5],samples=len(q),total_ms=sum(ms),mean_ms=statistics.mean(ms),p99_ms=ms[int(.99*(len(ms)-1))],max_ms=max(ms),phases=sorted(set(v['phase'] for v in q)),contacts=sorted(set(v['contacts'] for v in q))))
out['groups'].sort(key=lambda x:x['total_ms'],reverse=True)
for step,q in sorted(steps.items(),key=lambda x:sum(v['ms'] for v in x[1]),reverse=True)[:25]:
 s=spans[step];out['slow_steps'].append(dict(step=step,generation_ms=1000*(s[7]-s[6])/h[1],pairs=len(q),pair_total_ms=sum(v['ms'] for v in q),top=sorted(q,key=lambda x:x['ms'],reverse=True)[:6]))
(p/'cpu41-summary.json').write_text(json.dumps(out,indent=2));print('pairs',len(a),'sampled steps',len(steps));print(json.dumps(out['groups'][:12],indent=2));print(json.dumps(out['slow_steps'][:3],indent=2))
