"""Offline replay of recorded IH event order; no simulated engine or headset claims."""
from pathlib import Path
import struct,collections,json,sys
R=Path(__file__).resolve().parents[1]
P=R/'audit/capture-20261023-1715-IH'
def check(rows,fq):
 t0=min(x[6] for x in rows if x[0]!=7);last={};phys=None;seen=set();prev={};c=collections.Counter();bad=[]
 for x in rows:
  if x[0]==8:phys=x
  if x[0]==6:last[x[3]&1]=x
  if x[0]!=2 or x[3] or x[1] in seen:continue
  seen.add(x[1])
  if (x[6]-t0)/fq<1:continue
  for h,m in last.items():
   c['eye_samples']+=1
   if phys and m[2]<phys[2]:bad.append([x[1],h,m[2],phys[2]])
   if h in prev and m[6]==prev[h][6]:
    c['repeated_'+str(h)]+=1
    if phys and m[2]==phys[2]:c['repeated_latest_physics_'+str(h)]+=1
   prev[h]=m
 return dict(c),bad
if __name__=='__main__':
 d=(P/'hpl3vr_frame_timing_IH.bin').read_bytes();fq=struct.unpack_from('<Q',d,16)[0];rows=list(struct.iter_unpack('<6I3Q32f',d[24:]));c,bad=check(rows,fq)
 assert c['eye_samples']==3392 and not bad
 assert c['repeated_0']==c['repeated_latest_physics_0']==55
 assert c['repeated_1']==c['repeated_latest_physics_1']==33
 # Negative control: suppress genuine mesh publications. The audit must detect lag.
 broken=[x for x in rows if not(x[0]==6 and x[2]%3==0)]
 assert check(broken,fq)[1], 'Audit failed to detect deliberately omitted publication'
 result={'type':'recorded-event replay, not live engine replay','counts':c,'mesh_behind_completed_newton':len(bad),'negative_control':'PASS omitted writes detected','interpretation':'No recorded missed final physics-to-mesh publication. Repeats have no newer Newton completion.'}
 (R/'docs/v109-evidence/timing_ii_replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
