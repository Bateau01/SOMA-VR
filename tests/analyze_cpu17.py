from pathlib import Path
import struct,json,sys,statistics
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes();magic,freq,count,dropped,skipped,filtered=struct.unpack_from('<6Q',raw);assert not dropped
rows=[dict(kind=k,frame=f,phase=ph,detail=d,start=a,end=b,ms=1000*(b-a)/freq,value=v) for k,f,st,ph,state,d,a,b,v in struct.iter_unpack('<6I3Q',raw[48:]) if k in (13,16)]
names={0:'GL texture deletion',1:'immutable storage allocation',2:'compressed subimage upload',3:'retirement child destruction'}
result={'scope':'CPU wall spans including driver waits. Short calls below50us filtered; averages describe retained calls only. Nested spans are not additive.','operations':[],'retirement_spikes':[]}
for d,name in names.items():
 q=[x for x in rows if x['kind']==16 and x['detail']==d];v=sorted(x['ms'] for x in q)
 result['operations'].append(dict(name=name,count=len(q),mean_ms=statistics.mean(v) if v else None,max_ms=max(v) if v else None,largest=sorted(q,key=lambda x:x['ms'],reverse=True)[:5]))
for outer in sorted([x for x in rows if x['kind']==13 and x['detail']==3],key=lambda x:x['ms'],reverse=True)[:10]:
 children=[x for x in rows if x['kind']==16 and x['start']>=outer['start'] and x['end']<=outer['end']]
 result['retirement_spikes'].append({'outer':outer,'children':children})
(r/'texture-operations.json').write_text(json.dumps(result,indent=2))
for x in result['operations']:print({k:v for k,v in x.items() if k!='largest'})
for x in result['retirement_spikes'][:3]:print(x)
