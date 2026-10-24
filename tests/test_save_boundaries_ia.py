from pathlib import Path
import re,json
r=Path.cwd();b=r.parents[1]/'SOMA_VR_109_S26HZ/repo';rows=[]
for p in (r/'runtime/maps').rglob('*.hps'):
 s=p.read_text(encoding='utf-8-sig');q=b/p.relative_to(r)
 if 'EnsureVRTraversalIA' not in s:assert p.read_bytes()==q.read_bytes();continue
 t=q.read_text(encoding='utf-8-sig');calls=re.findall(r'mVRTraversalHY.Add\([^;]+\);',s);assert calls==re.findall(r'mVRTraversalHY.Add\([^;]+\);',t)
 def stripped(x):
  x=re.sub(r'void EnsureVRTraversalIA\(\)\s*\{.*?\}','',x,flags=re.S)
  x=x.replace('EnsureVRTraversalIA();','')
  x=re.sub(r'mVRTraversalHY.Add\([^;]+\);','',x)
  x=re.sub(r'//[^\n]*|/\*.*?\*/','',x,flags=re.S)
  return re.sub(r'\s+','',x)
 assert stripped(s)==stripped(t),p
 assert s.count('EnsureVRTraversalIA();')==2
 rows.append({'map':p.stem,'native_statements_unchanged':True,'placement_definitions_unchanged':len(calls)})
for folder in ['source','runtime/script','runtime/entities']:
 for p in (r/folder).rglob('*'):
  if p.is_file():assert p.read_bytes().replace(b'S26IA',b'S26HZ')==(b/p.relative_to(r)).read_bytes(),p
(r/'docs/v109-evidence/boundaries_ia.json').write_text(json.dumps(rows,indent=2));print('PASS',len(rows),'map transformations; all native code, helper gates, hand poses and entity assets identical')
