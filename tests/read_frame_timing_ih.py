"""CPU wall spans, sparse GPU spans and mesh-write snapshots; not compositor FPS."""
from pathlib import Path
import struct,json,sys,collections
ROW=struct.Struct('<6I3Q32f')
NAMES={1:'runtime_begin_wait_locate',2:'scene_call',3:'eye_submit',4:'desktop_mirror',5:'runtime_end',6:'mesh_write',7:'gpu_scene',8:'newton',9:'camera_view'}
def read(path):
 data=Path(path).read_bytes()
 if len(data)<24:raise ValueError('Truncated header')
 magic,ver,size,n,freq=struct.unpack_from('<4IQ',data)
 if (magic,ver,size)!=(0x48494653,1,ROW.size) or not freq or n>32768 or len(data)!=24+n*size:raise ValueError('Invalid capture header/length')
 rows=list(ROW.iter_unpack(data[24:]));stats={}
 for kind,name in NAMES.items():
  a=[r for r in rows if r[0]==kind]
  if not a:continue
  duration=sorted((r[7]-r[6])*1000/(1e9 if kind==7 else freq) for r in a)
  if duration[0]<0:raise ValueError('Reversed timestamp')
  stats[name]={'count':len(a),'median_ms':duration[len(a)//2],'p95_ms':duration[int(len(a)*.95)],'max_ms':duration[-1]}
 return {'rows':n,'qpc_frequency':freq,'spans':stats,'states':dict(collections.Counter(r[4] for r in rows)),
 'limits':'Scene wall time includes driver waits; GPU samples are sparse per-call intervals. Mesh writes are not proof of visible pixels. Begin combines wait/begin/locate; no compositor presentation measurement.'}
if __name__=='__main__':print(json.dumps(read(sys.argv[1]),indent=2))
