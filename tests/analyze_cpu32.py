from pathlib import Path
import collections,json,math,statistics,struct,sys
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw)
assert h[0]==0x4350553134455654 and not h[3]
rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==h[2]
assert json.loads((p/'build-receipt.json').read_text())['arguments']['collision_pairs']
steps=collections.defaultdict(list)
for x in rows:steps[x[2]].append(x)
f=lambda n:struct.unpack('<f',struct.pack('<I',n))[0]
pos={x[1]:(f(x[8]>>32),f(x[8]&0xffffffff),x[6]) for x in rows if x[0]==18}
anchors=[(10.25,18),(21.2501,49.167),(4.25,68.75)]
first=[min(v[2] for v in pos.values() if math.hypot(v[0]-a[0],v[1]-a[1])<6) for a in anchors]
data=[]
for step,q in steps.items():
    outer=[x for x in q if x[0]==9]
    if len(outer)!=1:continue
    x=outer[0];v=pos.get(x[1]);region=-1
    if v:
        for i,a in enumerate(anchors):
            if math.hypot(v[0]-a[0],v[1]-a[1])<6 and v[2]>=first[i]+5*h[1]:region=i
    sampled=any(z[0]==40 for z in q)
    d=dict(step=step,frame=x[1],region=region,wall_ms=1000*(x[7]-x[6])/h[1],sampled=sampled)
    if sampled:
        get=lambda k,detail=0:next(z[8] for z in q if z[0]==k and z[5]==detail)
        d.update(lost=get(40),calls=get(41),hand_calls=get(35,2),hand_cpu_ms=1000*get(33,2)/h[1],pairs=[])
        assert d['calls']+d['lost']==d['hand_calls'],d
        for detail in {z[5] for z in q if z[0]==42}:
            d['pairs'].append(dict(worker=detail>>8,rank=detail&255,a=hex(get(42,detail)),b=hex(get(43,detail)),calls=get(44,detail),rejected=get(45,detail),cpu_ms=1000*get(46,detail)/h[1]))
        assert all(z['calls']>=z['rejected'] for z in d['pairs'])
        d['top4_cpu_fraction']=sum(z['cpu_ms'] for z in d['pairs'])/d['hand_cpu_ms'] if d['hand_cpu_ms'] else 0
    data.append(d)
regions=[];by_step={d['step']:d for d in data}
for region in range(3):
    q=[d for d in data if d['region']==region and d['sampled']];assert len(q)>50
    slow=[d for d in q if d['wall_ms']>=1]
    neighbours=[]
    for d in q:
        near=[by_step.get(d['step']+o) for o in (-1,1)]
        if all(n and not n['sampled'] and n['region']==region for n in near):neighbours.append(d['wall_ms']-statistics.mean(n['wall_ms'] for n in near))
    regions.append(dict(region=region,sampled_steps=len(q),lost=sum(d['lost'] for d in q),mean_calls=statistics.mean(d['calls'] for d in q),
        slow_steps=len(slow),mean_top4_fraction=statistics.mean(d['top4_cpu_fraction'] for d in slow) if slow else None,
        sampled_minus_neighbour_ms=statistics.mean(neighbours) if neighbours else None,
        worst=sorted(q,key=lambda d:d['wall_ms'],reverse=True)[:8]))
report=dict(scope='Opaque ordered body addresses valid only within their observed step. Top4 individual OS-worker/pair buckets, not merged global pairs. Worker CPU is inclusive and not wall time. Neighbour comparison is not a matched overhead bound. No physics-policy changes.',events=h[2],sampled_steps=sum(d['sampled'] for d in data),lost=sum(d.get('lost',0) for d in data),regions=regions)
(p/'cpu32-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert not report['lost'],'Pair ranking incomplete: bounded table overflowed'
