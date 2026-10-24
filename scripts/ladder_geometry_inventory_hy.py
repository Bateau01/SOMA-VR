from inventory_climbs_hy import G,R
import xml.etree.ElementTree as E,json,math
out=[]
for p in sorted((G/'maps').glob('chapter*/*/*.hpm_Area')):
 candidates=[]
 for kind,tag in [('Entity','Entity'),('StaticObject','StaticObject')]:
  file=p.with_suffix('.hpm_'+kind)
  if not file.exists():continue
  doc=E.parse(file)
  for section in doc.iter('Section'):
   files={a.get('Id'):a.get('Path') for a in section.iter('File')}
   for obj in section.iter(tag):
    path=files.get(obj.get('FileIndex'),'')
    if any(x in (path+' '+obj.get('Name','')).lower() for x in ['ladder','stair']):candidates.append({**obj.attrib,'file':path,'kind':kind})
 for area in E.parse(p).iter('Area'):
  if area.get('AreaType')!='Ladder':continue
  pos=list(map(float,area.get('WorldPos').split()))
  c=sorted(candidates,key=lambda o:math.dist(pos,list(map(float,o.get('WorldPos').split()))))[:2]
  out.append({'map':p.stem,'ladder':area.attrib,'meshes':c})
(R/'docs/v109-evidence/ladder_geometry_hy.json').write_text(json.dumps(out,indent=2))
for a in out:print(a['map'],a['ladder']['Name'],[(x['Name'],x['file'],x['WorldPos']) for x in a['meshes']])
