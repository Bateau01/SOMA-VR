from pathlib import Path
import json,xml.etree.ElementTree as E,numpy as np,re
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA')
p=R/'scripts/ladder_surfaces_hy.py';ns={'__file__':str(p)};exec(p.read_text(encoding='utf-8').split('out=[]\nfor file')[0],ns)
vec=ns['vec'];rotation=ns['rotation'];triangles=ns['triangles']
cov=json.loads((R/'docs/v109-evidence/ladder_coverage_hy.json').read_text())
for entry in cov:
 if (entry['map'],entry['target']) not in [('02_01_ms_curie_outside','LadderArea_3'),('02_02_ms_curie_inside','CrewQuarterLadderArea'),('02_01_ms_curie_outside','Start_Ladder')]:continue
 mapname=entry['map'];target=entry['target'];base=G/'maps/chapter02'/mapname/mapname
 a=next(a for a in E.parse(str(base)+'.hpm_Area').iter('Area') if a.get('Name')==target);origin=vec(a.get('WorldPos'));rot=rotation(vec(a.get('Rotation')));size=vec(a.get('Scale'));faces=[]
 for kind in ['StaticObject','Entity']:
  for sec in E.parse(str(base)+'.hpm_'+kind).iter('Section'):
   fs={f.get('Id'):f.get('Path') for f in sec.iter('File')}
   for o in sec.iter(kind):
    path=fs.get(o.get('FileIndex'),'');op=vec(o.get('WorldPos'))
    if 'ladder' not in path.lower() or np.linalg.norm((op-origin)[[0,2]])>2:continue
    ts=triangles(path)
    if ts is None:continue
    world=(ts*vec(o.get('Scale')))@rotation(vec(o.get('Rotation'))).T+op
    if o.get('Name')=='CrewQuarterLadder':world[:, :, 1]-=4.26755*.9
    local=(world-origin)@rot
    for idx,t in enumerate(local):
     c=t.mean(0);n=np.cross(t[1]-t[0],t[2]-t[0]);ln=np.linalg.norm(n)
     if ln<1e-8 or abs(c[0])>.65 or abs(c[2])>.65 or abs(c[1])>size[1]/2+.75:continue
     n/=ln;faces.append((c,n,o.get('Name'),path,idx))
 points=[]
 for end in ['bottom','top']:
  desired=np.array([.15,-size[1]/2+1.15 if end=='bottom' else size[1]/2-.1,0]);choices=[]
  for c,n,name,path,idx in faces:
   if n[2 if end=='bottom' else 1]<.7:continue
   score=np.linalg.norm((c-desired)*[1,2,1]);choices.append((score,c,n,name,path,idx))
  if choices:
   score,c,n,name,path,idx=min(choices,key=lambda v:v[0]);points.append(dict(end=end,local_contact=c.tolist(),local_normal=n.tolist(),local_fingers=([0,1,0] if end=='bottom' else [0,0,-1]),mesh=name,source=path,triangle=idx,score=float(score)))
 if target=='Start_Ladder':
  # Deployed FBX extender has no COLLADA triangles: inspect this contact against
  # native rendered extended animation before acceptance.
  points=[dict(end='bottom',local_contact=[.15,-2.6,.0],local_normal=[0,0,1],local_fingers=[0,1,0],mesh='ladder_extender',source='native extended FBX placement candidate',triangle=None,score=None),entry['points'][1]]
 assert len(points)==2,(target,points)
 entry.update(points=points,status='candidate; CURIE unit-corrected geometry, awaiting native placement/deployment tests')
 print(target,[(x['end'],x['local_contact'],x['mesh'],x['score']) for x in points])
(R/'docs/v109-evidence/ladder_coverage_hy.json').write_text(json.dumps(cov,indent=2),encoding='utf-8')
# Add only absent entries, preserving previous guides and native map bodies.
for mapname in ['02_01_ms_curie_outside','02_02_ms_curie_inside']:
 p=R/'runtime/maps/chapter02'/mapname/(mapname+'.hps');s=p.read_text(encoding='utf-8-sig');existing='cVRTraversalGuidesHY mVRTraversalHY' in s
 if not existing:
  s='#include "helpers/helper_vr_traversal_hy.hps"\n'+s;i=s.index('{',s.index('class cScrMap'))+1;s=s[:i]+'\n [nosave] cVRTraversalGuidesHY mVRTraversalHY;\n'+s[i:]
 lines='\n'
 for e in cov:
  if e['map']!=mapname or not e['status'].startswith('candidate') or 'mVRTraversalHY.Add("'+e['target']+'"' in s:continue
  for pt in e['points']:
   v=lambda a:'cVector3f('+','.join(f'{x:.7f}f' for x in a)+')'
   lines+='        mVRTraversalHY.Add("'+e['target']+'",'+v(pt['local_contact'])+','+v(pt['local_fingers'])+','+v(pt['local_normal'])+');\n'
 m=re.search(r'void OnEnter\(\)\s*\{',s);assert m
 if existing:i=s.index('mVRTraversalHY.Dispose();',m.end())+len('mVRTraversalHY.Dispose();');s=s[:i]+lines+s[i:]
 else:
  s=s[:m.end()]+'\n mVRTraversalHY.Dispose();'+lines+s[m.end():]
  m=re.search(r'void Update\(float (\w+)\)\s*\{',s);assert m;s=s[:m.end()]+'\n mVRTraversalHY.Update('+m[1]+');'+s[m.end():]
  m=re.search(r'void OnLeave\(\)\s*\{',s)
  if m:s=s[:m.end()]+'\n mVRTraversalHY.Dispose();'+s[m.end():]
  else:i=s.index('{',s.index('class cScrMap'))+1;s=s[:i]+'\n void OnLeave(){mVRTraversalHY.Dispose();}\n'+s[i:]
 p.write_text(s,encoding='utf-8')
