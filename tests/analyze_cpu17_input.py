from pathlib import Path
import struct,json,sys
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes()
magic,freq,count,dropped,skipped,filtered=struct.unpack_from('<6Q',raw)
assert magic==0x4350553134455654 and len(raw)==48+count*48 and not dropped
names={0:'SDL begin update',1:'SDL finish update',2:'SDL event polling',3:'device rebuild',4:'action update'}
rows=[dict(kind=k,frame=f,phase=ph,stage=d,start=a,end=b,ms=1000*(b-a)/freq,identity=hex(v)) for k,f,st,state0,state,d,a,b,v in struct.iter_unpack('<6I3Q',raw[48:]) for ph in [state0] if k==17 or (k==10 and v==0x6e1288 and d==4)]
result={'scope':'Filtered CPU wall spans; nested stages are not additive. Absence of a repeated spike does not resolve the prior failure.','stages':[], 'largest_input_updates':[]}
for stage,name in names.items():
 q=[x for x in rows if x['kind']==17 and x['stage']==stage]
 result['stages'].append(dict(name=name,retained_calls=len(q),max_ms=max((x['ms'] for x in q),default=0)))
for outer in sorted([x for x in rows if x['kind']==10],key=lambda x:x['ms'],reverse=True)[:8]:
 result['largest_input_updates'].append(dict(outer=outer,children=[x for x in rows if x['kind']==17 and x['start']>=outer['start'] and x['end']<=outer['end']]))
(r/'input-operations.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
