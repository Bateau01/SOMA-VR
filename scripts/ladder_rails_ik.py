from pathlib import Path
import re,json,xml.etree.ElementTree as E,numpy as np
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA')
# Reuse verified Collada/scene transform reader, without regenerating old records.
exec((R/'scripts/ladder_surfaces_hy.py').read_text().split('out=[]\nfor file in sorted')[0])
report=[]
for script in (R/'runtime/maps').rglob('*.hps'):
 s=script.read_text();matches=list(re.finditer(r'mVRTraversalHY.Add\("([^"\n]+)",cVector3f\(([^)]*)\),cVector3f\(([^)]*)\),cVector3f\(([^)]*)\)\);',s))
 if not matches:continue
 areaFile=G/script.relative_to(R/'runtime');areaFile=areaFile.with_suffix('.hpm_Area')
 areas={a.get('Name'):a for a in E.parse(areaFile).iter('Area') if a.get('AreaType')=='Ladder'}
 objs=[]
 for kind in ['StaticObject','Entity']:
  for sec in E.parse(areaFile.with_suffix('.hpm_'+kind)).iter('Section'):
   files={x.get('Id'):x.get('Path') for x in sec.iter('File')}
   for o in sec.iter(kind):
    path=files.get(o.get('FileIndex'),'')
    if 'ladder' in path.lower() and 'holder' not in path.lower():objs.append((o,path))
 edits=[]
 for m in matches:
  name=m[1]
  if name not in areas:continue
  points=[x for x in matches if x[1]==name]
  def cv(x):return np.array([float(v.rstrip('f')) for v in x.split(',')])
  old=cv(m[2]);ys=[cv(x[2])[1] for x in points]
  if len(points)<2 or old[1]!=max(ys):continue
  a=areas[name];origin=vec(a.get('WorldPos'));rot=rotation(vec(a.get('Rotation')));size=vec(a.get('Scale'));candidates=[]
  for o,path in objs:
   op=vec(o.get('WorldPos'))
   if np.linalg.norm((op-origin)[[0,2]])>2:continue
   ts=triangles(path)
   if ts is None:continue
   world=(ts*vec(o.get('Scale')))@rotation(vec(o.get('Rotation'))).T+op
   if o.get('Name')=='CrewQuarterLadder':world[:,:,1]-=4.26755*.9
   local=(world-origin)@rot
   for i,t in enumerate(local):
    c=t.mean(0);n=np.cross(t[1]-t[0],t[2]-t[0]);ln=np.linalg.norm(n)
    if ln<1e-8:continue
    n/=ln
    if n[1]<.7 or abs(c[1]-old[1])>.55 or abs(c[0])>size[0]/2+.12 or abs(c[2])>size[2]/2+.12:continue
    # Native top rail extends toward -Z; prefer accessible near rail top,
    # not far crossbar; retain a real source triangle and area's reach limits.
    if c[2]>old[2]-.08:continue
    score=c[2]+abs(c[1]-old[1])*.7+abs(c[0]-.25)*.15
    candidates.append((score,c,n,path,i))
  if not candidates:
   report.append({'map':script.stem,'target':name,'status':'unresolved geometry','old':old.tolist()});continue
  _,c,n,path,i=min(candidates,key=lambda v:v[0])
  def v(x):return 'cVector3f('+','.join(f'{a:.7f}f' for a in x)+')'
  new='mVRTraversalHY.Add("'+name+'",'+v(c)+','+v([0,0,-1])+','+v(n)+');'
  edits.append((m.start(),m.end(),new));report.append({'map':script.stem,'target':name,'old':old.tolist(),'new':c.tolist(),'normal':n.tolist(),'triangle':i,'source':path,'status':'candidate requires rendered inspection'})
 for a,b,t in reversed(edits):s=s[:a]+t+s[b:]
 if edits:script.write_text(s)
(R/'docs/v109-evidence/ladder_rails_ik.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
