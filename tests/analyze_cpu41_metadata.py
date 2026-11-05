"""Correlate repeated native pair calls; metadata is not additional timed work."""
from pathlib import Path
import collections,json,struct,sys
p=Path(sys.argv[1]);b=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',b)
assert h[3]==0
r=list(struct.iter_unpack('<6I3Q',b[48:]));assert len(r)==h[2]
by={t:{} for t in (58,60,61,62)}
def key(x):return x[1:8]
for x in r:
 if x[0] in by:
  assert key(x) not in by[x[0]],'Ambiguous event identity'
  by[x[0]][key(x)]=x[8]
groups=collections.defaultdict(list)
for x in r:
 if x[0]!=57:continue
 k=key(x);d=x[5]
 q=dict(step=x[2],phase=x[3],body0=hex(x[8]),body1=hex(by[58][k]),ms=1000*(x[7]-x[6])/h[1],contacts=d>>16,
        pair=hex(by[60][k]) if k in by[60] else None,raw10=hex(by[61][k]) if k in by[61] else None,raw18=hex(by[62][k]) if k in by[62] else None)
 groups[(x[2],x[8],by[58][k])].append(q)
dup=[q for q in groups.values() if len(q)>1]
complete=[q for q in dup if all(x['pair'] is not None for x in q)]
out=dict(repeated_groups=len(dup),fully_observed_groups=len(complete),
 same_pair=sum(len(set(x['pair'] for x in q))==1 for q in complete),
 same_raw10=sum(len(set(x['raw10'] for x in q))==1 for q in complete),
 same_raw18=sum(len(set(x['raw18'] for x in q))==1 for q in complete),
 examples=sorted(complete,key=lambda q:sum(x['ms'] for x in q),reverse=True)[:20])
(p/'cpu41-metadata.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
