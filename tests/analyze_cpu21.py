"""Attribution evidence, not a passing gameplay or lifecycle verdict."""
from pathlib import Path
import sys,struct,json
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes()
h=struct.unpack_from('<6Q',raw);rows=list(struct.iter_unpack('<6I3Q',raw[48:]))
assert len(rows)==h[2] and h[3]==0,'Incomplete/dropped capture'
def ms(x):return 1000*(x[7]-x[6])/h[1]
slow=[]
for x in rows:
 if x[0]==27 and ms(x)>2:
  parents=[a for a in rows if a[0]==21 and a[5]==5 and a[6]<=x[6] and a[7]>=x[7]]
  slow.append(dict(frame=x[1],kind=x[5],ms=ms(x),stream_ms=[ms(a) for a in parents]))
r=json.loads((p/'result.json').read_text())
report=dict(scope='Actual native attribution; nested times not additive. Exit failure remains failure.',
 events=len(rows),dropped=h[3],process_exit_code=r['process_exit_code'],
 slow=slow,log=[l for l in (p/'hpl3vr.log').read_text(errors='replace').splitlines() if 'CPU21_' in l])
(p/'cpu21-summary.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
