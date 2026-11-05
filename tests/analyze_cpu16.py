from pathlib import Path
import struct,json,sys,collections
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes();magic,freq,count,dropped,skipped,filtered=struct.unpack_from('<6Q',raw);assert not dropped
rows=[dict(kind=k,frame=f,step=s,phase=p,state=st,detail=d,start=a,end=b,ms=(b-a)*1000/freq,identity=hex(i)) for k,f,s,p,st,d,a,b,i in struct.iter_unpack('<6I3Q',raw[48:]) if k==15]
longest=sorted(rows,key=lambda x:x['ms'],reverse=True)[:20]
result={'scope':'Inclusive CPU wall spans. Native callbacks unchanged. Includes startup before replay phase99. No FPS claim.', 'largest':longest,'contained_in_largest':[]}
for top in longest[:3]:result['contained_in_largest'].append({'outer':top,'events':[x for x in rows if x is not top and x['start']>=top['start'] and x['end']<=top['end'] and x['ms']>.5]})
(r/'map-attribution.json').write_text(json.dumps(result,indent=2))
for x in longest[:10]:print(x)
