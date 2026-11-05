from pathlib import Path
import struct,sys,json,collections,statistics
p=Path(sys.argv[1]);raw=(p/'cpu14_events.bin').read_bytes();_,freq,n,dropped,skipped,filtered=struct.unpack_from('<6Q',raw);assert not dropped
sizes=collections.defaultdict(lambda:collections.defaultdict(list))
for kind,frame,step,phase,state,detail,a,b,size in struct.iter_unpack('<6I3Q',raw[48:]):
 if kind==14 and size>=2*1024*1024:sizes[size][detail].append((b-a)*1000/freq)
rows=[]
for size,modes in sorted(sizes.items()):
 if not modes[0] or not modes[1]:continue
 rows.append(dict(bytes=size,native_count=len(modes[0]),candidate_count=len(modes[1]),native_mean_ms=statistics.mean(modes[0]),candidate_mean_ms=statistics.mean(modes[1]),native_max_ms=max(modes[0]),candidate_max_ms=max(modes[1])))
assert rows,'No comparable native/candidate allocation sizes'
(p/'cleanup-comparison.json').write_text(json.dumps({'scope':'Alternating eligible bitmap cleanup within one run, grouped by allocation size. Different allocations, not duplicated freeing; not whole-frame speedup.','sizes':rows},indent=2))
for r in rows:print(r)
