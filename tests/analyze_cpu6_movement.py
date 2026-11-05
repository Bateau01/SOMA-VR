"""Validate actual held ownership and report diagnostic frame intervals, not CPU-exclusive time."""
from pathlib import Path
import argparse,struct,json,statistics
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--legacy',action='store_true');a=p.parse_args();r=a.capture
rows=list(struct.iter_unpack('<4I5f' if a.legacy else '<4I9f',(r/'cpu6_movement.bin').read_bytes()));assert len(rows)>100,'Missing or empty recording'
result=[]
for ph in range(11):
 q=[x for x in rows if x[0]==ph];assert q,f'Missing phase {ph}'
 v=sorted(x[4] for x in q);item=dict(phase=ph,frames=len(q),held=sum(x[2] for x in q),hands_min=min(x[3] for x in q),mean_ms=statistics.mean(v),p95_ms=v[int(.95*(len(v)-1))],p99_ms=v[int(.99*(len(v)-1))],max_ms=max(v),camera_y_range=max(x[8] for x in q)-min(x[8] for x in q))
 if not a.legacy:
  item['attribution_mean_ms']={n:statistics.mean(x[i] for x in q) for i,n in enumerate(('scene','xr_begin','newton','texture_completion'),9)}
  item['largest_intervals']=[dict(zip(('interval','scene','xr_begin','newton','texture_completion'),[x[4],*x[9:13]])) for x in sorted(q,key=lambda x:x[4],reverse=True)[:4]]
 result.append(item)
assert all(x['held']==x['frames'] and x['hands_min']==2 for x in result if 5<=x['phase']<=9),'Held ownership or hand lifetime failed'
assert result[-1]['held']<result[-1]['frames']/2,'Grip release failed'
assert result[3]['camera_y_range']>.5 and result[8]['camera_y_range']>.5,'Crouch did not happen'
log=(r/'hpl3vr.log').read_text(errors='replace');assert 'SHARED GRIP BEGIN R' in log and 'GRAB RELEASE R' in log
(r/'movement-summary.json').write_text(json.dumps({'scope':'Synthetic controller replay through native inputs and solver. Changing view/position; not a matched optimisation speedup. Texture time may overlap scene/CPU work; do not sum inclusive categories.','phases':result},indent=2))
for x in result:print(x['phase'],x['frames'],x['held'],round(x['mean_ms'],3),round(x['p99_ms'],3),x.get('attribution_mean_ms',''))
