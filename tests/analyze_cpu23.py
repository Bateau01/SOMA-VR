"""Native CPU attribution; nested GL spans are subtracted, not added twice."""
from pathlib import Path
import sys,struct,json
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]))
assert len(rows)==h[2] and h[3]==0
ms=lambda x:1000*(x[7]-x[6])/h[1]
uploads=[]
for x in rows:
 if x[0]!=29 or x[5]!=0:continue
 nested=[a for a in rows if a[0]==29 and a[5]!=0 and x[6]<=a[6]<=a[7]<=x[7]]
 stages=[a for a in rows if a[0]==23 and a[6]<=x[6]<=x[7]<=a[7]]
 uploads.append(dict(frame=x[1],ms=ms(x),interleaved=x[8],stages=[a[5] for a in stages],gl_ms=sum(map(ms,nested)),other_ms=ms(x)-sum(map(ms,nested)),calls=[dict(kind=a[5],ms=ms(a),value=a[8]) for a in nested]))
report=dict(scope='Native CPU upload and nested driver calls; other_ms includes CPU copying, bookkeeping and filtered sub-50us GL calls. Not GPU duration or clean lifecycle proof.',events=len(rows),dropped=h[3],exit=json.loads((p/'result.json').read_text())['process_exit_code'],staged=[dict(frame=x[1],bytes=x[8]) for x in rows if x[0]==30],packed=[dict(frame=x[1],bytes=x[8]) for x in rows if x[0]==31],uploads=sorted(uploads,key=lambda x:x['ms'],reverse=True),log=[l for l in (p/'hpl3vr.log').read_text(errors='replace').splitlines() if 'CPU23_' in l])
(p/'cpu23-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
