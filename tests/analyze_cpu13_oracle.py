import json,re,sys
from pathlib import Path
r=Path(sys.argv[1]);s=(r/'hpl3vr.log').read_text(errors='replace')
rows=[dict(phase=int(p),queries=int(n),mismatches=int(m),skips=int(k),fallbacks=int(f),baseline_ms=float(b),candidate_ms=float(c)) for p,n,m,k,f,b,c in re.findall(r'CPU13_ORACLE phase (\d+) queries (\d+) mismatches (\d+) skips (\d+) fallbacks (\d+) baseline_ms ([0-9.]+) candidate_ms ([0-9.]+)',s)]
assert len(rows)==11 and sum(x['queries'] for x in rows)>0,'Missing comparison coverage'
for x in rows:
 if x['queries']:x['baseline_per_query_ms']=x['baseline_ms']/x['queries'];x['candidate_per_query_ms']=x['candidate_ms']/x['queries']
steady=[x for x in rows if 5<=x['phase']<=9];base=sum(x['baseline_ms'] for x in steady);cand=sum(x['candidate_ms'] for x in steady);n=sum(x['queries'] for x in steady)
report={'scope':'Alternating paired same-query comparison; baseline always authoritative. Does not prove candidate gameplay regression coverage. Timer excludes comparison/cache-copy overhead.','steady_queries':n,'steady_baseline_per_query_ms':base/n,'steady_candidate_per_query_ms':cand/n,'steady_change_percent':100*(cand/base-1),'mismatches':sum(x['mismatches'] for x in rows),'phases':rows}
(r/'query-oracle-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='phases'},indent=2));assert report['mismatches']==0,'Candidate differs from baseline'
