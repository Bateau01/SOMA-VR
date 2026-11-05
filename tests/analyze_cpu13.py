"""Per-native-step attribution; inclusive categories must not be summed."""
import json,re,sys
from pathlib import Path
root=Path(sys.argv[1]);log=(root/'hpl3vr.log').read_text(errors='replace')
phases={int(p):dict(phase=int(p),steps=int(s),native_calls=int(n),dt_sum=float(dt)) for p,s,n,dt in re.findall(r'CPU13_PHASE phase (\d+) steps (\d+) native_calls (\d+) dt_sum ([0-9.]+)',log)}
assert set(phases)==set(range(11)), 'Incomplete phase capture'
for p,slot,total in re.findall(r'CPU13_COST phase (\d+) slot (\d+) total_ms ([0-9.]+)',log):
 item=phases[int(p)];item.setdefault('total_ms',{})[slot]=float(total)
for p,item in phases.items():
 assert item['steps']>0 and item['native_calls']>0
 assert 0<item['steps']<=item['native_calls'], 'Unexpected observer accounting'
 item['dt_mean']=item['dt_sum']/item['native_calls']
 item['per_step_ms']={k:v/item['steps'] for k,v in item['total_ms'].items()}
 print(p,item['steps'],item['native_calls'],round(item['dt_mean'],7),{k:round(item['per_step_ms'][k],5) for k in ('0','1','2','10','12','13')})
(root/'physics-phase-summary.json').write_text(json.dumps({'scope':'Native executed steps, diagnostic timings. PRE/POST contain subcategories. Not exclusive total CPU or FPS.','phases':list(phases.values())},indent=2))
