"""S26GS bounded recorder analysis. Observations are engine poses, not display pixels."""
import struct,sys,json,math,collections
from pathlib import Path
def analyze(data):
 h=struct.unpack_from('<8Q',data);assert h[0]==0x31454a3632535256 and h[1]==1 and h[2]==176 and h[3]>0
 assert len(data)==64+h[4]*176
 physics={};previous={};eyes={};age=[];interval=[];eye_errors=[];repeats=0;moving=0;counts=collections.Counter();threads=set()
 for off in range(64,len(data),176):
  a=struct.unpack_from('<2Q8I4f14Q',data,off);kind=a[2];counts[kind]+=1
  if kind not in (7,8):continue
  flags=a[14];hand=flags&1;eye=(flags>>1)&1;key=(a[1],hand);threads.add(a[5])
  m=struct.unpack_from('<16f',data,off+88);pos=m[12:15];target=struct.unpack_from('<3f',data,off+152)
  if not all(math.isfinite(x) for x in (*m,*target)):continue
  if kind==8:physics[key]=a[0];continue
  if key in physics and a[0]>=physics[key]:age.append((a[0]-physics[key])*1000/h[3])
  pk=key+(eye,);old=previous.get(pk)
  if old:
   interval.append((a[0]-old[0])*1000/h[3])
   if flags&8 and old[3]&8 and math.dist(target,old[2])>0.0001:
    moving+=1
    if math.dist(pos,old[1])<0.000001:repeats+=1
  previous[pk]=(a[0],pos,target,flags)
  ek=key+(a[16],a[3]);pair=eyes.setdefault(ek,{})
  pair[eye]=pos
  if len(pair)==2:eye_errors.append(math.dist(pair[0],pair[1]))
 def stats(x):
  x=sorted(x)
  return {'n':len(x),'median':x[len(x)//2],'p95':x[min(len(x)-1,int(len(x)*.95))],'max':x[-1]} if x else None
 return {'kinds':dict(counts),'dropped_busy_samples':h[5],'ring_full':h[4]==h[6], 'hand_sample_threads':sorted(threads),'draw_interval_ms':stats(interval),'latest_physics_sample_age_ms':stats(age),'eye_position_difference_game_units':stats(eye_errors),'draws_with_changed_target':moving,'unchanged_draw_position_despite_changed_target':repeats,'limitations':'Repeated poses can be legitimate contact/held constraints. Eye pairing uses engine frame and predicted display time. No compositor/display capture; timings include diagnostic overhead.'}
if __name__=='__main__':print(json.dumps(analyze(Path(sys.argv[1]).read_bytes()),indent=2))
