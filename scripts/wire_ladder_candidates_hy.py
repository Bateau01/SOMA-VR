"""Wire only explicitly inventoried candidates. Not a release acceptance test.
Run once on HY; dynamic/special unresolved cases remain listed as deferred.
"""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA')
items=json.loads((R/'docs/v109-evidence/ladder_surface_candidates_hy.json').read_text())
groups={};coverage=[]
def vector(v):return 'cVector3f('+','.join(f'{x:.7f}f' for x in v)+')'
for item in items:
 points=item['points']
 eligible=len(points)==2 and all(p['score']<.7 for p in points)
 eligible=eligible and item['map']!='03_03_omicron_descent'
 eligible=eligible and all('/special/' not in p['source'] and 'relay_station' not in p['source'] for p in points)
 status='candidate; requires native rendered and eligibility checks' if eligible else 'deferred: incomplete/moving surface geometry needs inspection'
 coverage.append({'map':item['map'],'target':item['target'],'status':status,'points':points})
 if eligible:groups.setdefault(item['map'],[]).append(item)
for mapname,items in groups.items():
 native=next((G/'maps').rglob(mapname+'.hps'));p=R/'runtime'/native.relative_to(G)
 s=p.read_text(encoding='utf-8-sig') if p.exists() else native.read_text(encoding='utf-8-sig')
 existing='cVRTraversalGuidesHY mVRTraversalHY' in s
 if not existing:
  s='#include "helpers/helper_vr_traversal_hy.hps"\n'+s
  i=s.index('{',s.index('class cScrMap'))+1;s=s[:i]+'\n [nosave] cVRTraversalGuidesHY mVRTraversalHY;\n'+s[i:]
 lines='\n        // HY ladder surfaces: source triangles recorded in ladder_coverage_hy.json.\n'
 if not existing:lines+='        mVRTraversalHY.Dispose();\n'
 for item in items:
  for point in item['points']:
   lines+='        mVRTraversalHY.Add("'+item['target']+'",'+vector(point['local_contact'])+','+vector(point['local_fingers'])+','+vector(point['local_normal'])+');\n'
 m=re.search(r'void OnEnter\(\)\s*\{',s);assert m
 # Existing climb initialization disposes first: append ladders AFTER that call.
 if existing:
  i=s.index('mVRTraversalHY.Dispose();',m.end())+len('mVRTraversalHY.Dispose();');s=s[:i]+lines+s[i:]
 else:s=s[:m.end()]+lines+s[m.end():]
 if not existing:
  clean=re.sub(r'/\*.*?\*/',lambda m:' '*len(m[0]),s,flags=re.S)
  m=re.search(r'void Update\(float (\w+)\)\s*\{',clean)
  if m:s=s[:m.end()]+'\n mVRTraversalHY.Update('+m[1]+');'+s[m.end():]
  else:
   i=s.index('{',s.index('class cScrMap'))+1;s=s[:i]+'\n void Update(float dt){mVRTraversalHY.Update(dt);}\n'+s[i:]
  m=re.search(r'void OnLeave\(\)\s*\{',s)
  if m:s=s[:m.end()]+'\n mVRTraversalHY.Dispose();'+s[m.end():]
  else:
   i=s.index('{',s.index('class cScrMap'))+1;s=s[:i]+'\n void OnLeave(){mVRTraversalHY.Dispose();}\n'+s[i:]
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
(R/'docs/v109-evidence/ladder_coverage_hy.json').write_text(json.dumps(coverage,indent=2))
print('Wired candidate areas:',sum(len(x) for x in groups.values()),'maps:',len(groups))
