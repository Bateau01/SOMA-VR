from pathlib import Path
import json,sys
out=[]
for name in sys.argv[1:]:
 p=Path(name);s=json.loads((p/'cpu23-summary.json').read_text());receipt=json.loads((p/'build-receipt.json').read_text())
 assert s['dropped']==0 and not receipt['arguments'].get('buffer_verify'), 'Do not compare readback verification timings'
 uploads=sorted([x for x in s['uploads'] if 6 in x['stages']],key=lambda x:x['frame'])
 assert len(uploads)==3,'Expected all three streamed stage6 buffers'
 out.append(dict(capture=str(p),candidate=receipt['arguments'].get('buffer_independent',False),sha=receipt['dll_sha256'],upload_ms=[x['ms'] for x in uploads],sum_ms=sum(x['ms'] for x in uploads),packed=s['packed'],exit=s['exit']))
assert len(out)==2 and not out[0]['candidate'] and out[1]['candidate']
assert len(out[0]['packed'])==0 and [x['bytes'] for x in out[1]['packed']]==[28088064,24239592,32300352]
print(json.dumps(dict(scope='Matched Theta120Hz native stage6 upload spans; no readback, no CPU20/22/27 changes; isolated sequential runs, not FPS or clean-lifecycle proof',runs=out,saved_ms=out[0]['sum_ms']-out[1]['sum_ms']),indent=2))
