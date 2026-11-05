from pathlib import Path
import struct,json,sys,re
r=Path(sys.argv[1]);raw=(r/'cpu14_events.bin').read_bytes();header=struct.unpack_from('<6Q',raw);freq=header[1];rows=list(struct.iter_unpack('<6I3Q',raw[48:]));assert len(rows)==header[2] and header[3]==0
def ms(v):return (v[7]-v[6])*1000/freq
def stats(q):
 v=sorted(map(ms,q))
 return dict(count=len(v),total_ms=sum(v),max_ms=max(v,default=0),p99_ms=v[int(.99*(len(v)-1))] if v else 0)
complete=[x for x in rows if x[0]==23 and x[5]==26 and x[8]==27]
slices=[x for x in rows if x[0]==26]
log=(r/'hpl3vr.log').read_text(errors='replace');summary=[x for x in log.splitlines() if 'CPU20_XML' in x]
result=dict(scope='Native isolated OpenXR with synthetic controller replay; nested times not additive; cleanup budget includes traversal and native destructors.',stage26_completion=[dict(frame=x[1],ms=ms(x)) for x in complete],stream=stats([x for x in rows if x[0]==21 and x[5]==5]),xml=stats([x for x in rows if x[0]==21 and x[5]==10]),slices=stats(slices),queue_log=summary)
if json.loads((r/'build-receipt.json').read_text())['arguments'].get('xml_observer'):
 result['scope']='Actual OpenXR native loader observation only; no synthetic inputs or hand assertions. Nested times not additive.'
result['final_retirement_batches']=[dict(completion_frame=p[1],**stats([x for x in slices if x[6]>=p[6] and (not any(y[0]==23 and y[5]==26 and y[8]==27 and p[6]<y[6]<x[6] for y in complete))])) for p in complete]
(r/'cpu20-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if '--candidate' in sys.argv:
 assert complete and slices and summary,'Candidate did not exercise retirement'
 assert re.search(r'accepted [1-9]\d* nodes [1-9]\d* fallback 0 pending 0 depth 0',summary[-1]),'Unexpected fallback or outstanding memory'
