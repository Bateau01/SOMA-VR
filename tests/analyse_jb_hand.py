"""Post-solver hand/item residuals; check build identity for target snapshot version. Not a claim about visible jitter or comfort."""
from pathlib import Path
import sys,struct,json,math,statistics
folder=Path(sys.argv[1]);data=(folder/'jb_hand_timing.bin').read_bytes();version=1;fmt=struct.Struct('<4Id51f4x')
if data[:4]==struct.pack('<I',0x4a424832):
 magic,version,stride,count=struct.unpack_from('<4I',data);data=data[16:];fmt=struct.Struct('<4Id67f3If4x');assert stride==fmt.size and len(data)==count*stride
assert data and len(data)%fmt.size==0,(len(data),fmt.size)
rows=list(fmt.iter_unpack(data))
def norm(a):return math.sqrt(sum(x*x for x in a))
def local(m,p):
 d=[p[k]-m[12+k] for k in range(3)]
 return [sum(m[4*a+k]*d[k] for k in range(3)) for a in range(3)]
def point(m):return m[12:15]
def stats(a):
 if not a:return None
 v=sorted(a);return {'median':statistics.median(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1]}
phases={}
for phase in range(10):
 rr=[x for x in rows if x[2]==phase];lags=[];relative=[];events=[];prev=None
 for row in rr:
  frame,step,ph,held,ms=row[:5];raw=row[5:21];hand=row[21:37];item=row[37:53]
  lag=norm([hand[12+k]-raw[12+k] for k in range(3)]);lags.append(lag)
  if held:
   relative.append(local(hand,point(item)))
   if prev and prev[3] and step==prev[1]+1:
    prior=local(prev[21:37],point(prev[37:53]));delta=norm([relative[-1][k]-prior[k] for k in range(3)])
    events.append({'frame':frame,'step':step,'ms':ms,'interval_ms':ms-prev[4],'held_relative_jump_m':delta,'hand_target_lag_m':lag, 'contact_count':row[72] if version==2 else None,'blocked':row[73] if version==2 else None,'native_use':row[74] if version==2 else None,'pre_solver_error_m':row[75] if version==2 else None})
  prev=row
 phases[phase]={'rows':len(rr),'held_rows':sum(x[3] for x in rr),'target_lag_m':stats(lags),'relative_jump_m':stats([e['held_relative_jump_m'] for e in events]),'largest_events':sorted(events,key=lambda e:e['held_relative_jump_m'],reverse=True)[:5]}
result={'scope':__doc__,'rows':len(rows),'version':version,'stride':fmt.size,'phases':phases}
(folder/'jb-hand-analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert all(phases[p]['held_rows']>0 for p in range(5,10)), 'Missing held-object movement phases; not a complete acquisition/movement test'
