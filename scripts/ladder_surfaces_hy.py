"""Offline candidate geometry, NOT runtime/visual acceptance.

Read scene transforms and section-local file tables. Keep source triangle and
entity identity so a candidate can be checked against native rendered output.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import json, math
import numpy as np
R=Path(__file__).resolve().parents[1]
G=Path('D:/SteamLibrary/steamapps/common/SOMA')
N={'c':'http://www.collada.org/2005/11/COLLADASchema'}
def rotation(v):
 x,y,z=v;cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def vec(s):return np.fromstring(s,sep=' ')
def resolve(s):
 s=s.replace('\\','/')
 for root in ['entities/','static_objects/']:
  if root in s:return G/s[s.index(root):]
 return G/s
cache={}
def triangles(file):
 file=resolve(file)
 if file.suffix=='.ent':file=resolve(E.parse(file).find('.//Mesh').get('Filename'))
 if file.suffix!='.dae':return None
 if file in cache:return cache[file]
 doc=E.parse(file);geos={}
 for g in doc.findall('.//c:geometry',N):
  sources={s.get('id'):vec(s.find('c:float_array',N).text).reshape(-1,int(s.find('.//c:accessor',N).get('stride','3'))) for s in g.findall('c:mesh/c:source',N)}
  vertices={v.get('id'):v.find('c:input[@semantic="POSITION"]',N).get('source')[1:] for v in g.findall('c:mesh/c:vertices',N)}
  parts=[]
  for t in g.findall('c:mesh/c:triangles',N)+g.findall('c:mesh/c:polylist',N):
   inputs=t.findall('c:input',N);stride=max(int(i.get('offset')) for i in inputs)+1
   v=next(i for i in inputs if i.get('semantic')=='VERTEX')
   ix=np.fromstring(t.find('c:p',N).text,sep=' ',dtype=int).reshape(-1,stride)[:,int(v.get('offset'))]
   if t.tag.endswith('polylist'):
    counts=np.fromstring(t.find('c:vcount',N).text,sep=' ',dtype=int);polys=[];offset=0
    for count in counts:
     for j in range(1,count-1):polys.extend([ix[offset],ix[offset+j],ix[offset+j+1]])
     offset+=count
    ix=np.array(polys,dtype=int)
   parts.append(sources[vertices[v.get('source')[1:]]][ix,:3].reshape(-1,3,3))
  if parts:geos[g.get('id')]=np.concatenate(parts)
 out=[]
 def walk(node,parent):
  m=parent.copy()
  for child in node:
   tag=child.tag.split('}')[-1];a=vec(child.text or '')
   t=np.eye(4)
   if tag=='matrix':t=a.reshape(4,4)
   elif tag=='translate':t[:3,3]=a
   elif tag=='scale':t[:3,:3]=np.diag(a)
   elif tag=='rotate':
    axis=a[:3];axis=axis/np.linalg.norm(axis);x,y,z=axis;c=np.cos(np.deg2rad(a[3]));s=np.sin(np.deg2rad(a[3]));t[:3,:3]=c*np.eye(3)+(1-c)*np.outer(axis,axis)+s*np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
   else:continue
   m=m@t
  for inst in node.findall('c:instance_geometry',N):
   geo=geos.get(inst.get('url')[1:])
   if geo is not None:out.append(geo@m[:3,:3].T+m[:3,3])
  for ch in node.findall('c:node',N):walk(ch,m)
 for node in doc.findall('.//c:visual_scene/c:node',N):walk(node,np.eye(4))
 unit=doc.find('c:asset/c:unit',N)
 meter=float(unit.get('meter','1')) if unit is not None else 1.0
 cache[file]=np.concatenate(out)*meter if out else None
 return cache[file]
out=[]
for file in sorted((G/'maps').glob('chapter*/*/*.hpm_Area')):
 objects=[]
 for kind in ['StaticObject','Entity']:
  for section in E.parse(file.with_suffix('.hpm_'+kind)).iter('Section'):
   files={x.get('Id'):x.get('Path') for x in section.iter('File')}
   for o in section.iter(kind):
    path=files.get(o.get('FileIndex'),'')
    if 'ladder' in path.lower() and 'holder' not in path.lower():objects.append((o,path))
 for a in E.parse(file).iter('Area'):
  if a.get('AreaType')!='Ladder':continue
  origin=vec(a.get('WorldPos'));rot=rotation(vec(a.get('Rotation')));size=vec(a.get('Scale'))
  faces=[];omitted=[]
  for obj,path in objects:
   op=vec(obj.get('WorldPos'))
   if np.linalg.norm((op-origin)[[0,2]])>2:continue
   ts=triangles(path)
   if ts is None:omitted.append(path);continue
   world=(ts*vec(obj.get('Scale')))@rotation(vec(obj.get('Rotation'))).T+op
   local=(world-origin)@rot
   for i,t in enumerate(local):
    center=t.mean(axis=0)
    if abs(center[0])>size[0]/2+.2 or abs(center[2])>.65 or abs(center[1])>size[1]/2+.75:continue
    n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
    if length<1e-8:continue
    n/=length
    faces.append((t,center,n,obj.get('Name'),path,i))
  points=[]
  for end in ['bottom','top']:
   desired=np.array([.15,-size[1]/2+1.15 if end=='bottom' else size[1]/2-.1,0])
   candidates=[]
   for t,c,n,name,path,index in faces:
    if n[2 if end=='bottom' else 1]<.9:continue
    score=np.linalg.norm((c-desired)*np.array([1,2,1]))
    candidates.append((score,c,n,name,path,index))
   if candidates:
    score,c,n,name,path,index=min(candidates,key=lambda x:x[0])
    points.append({'end':end,'local_contact':c.tolist(),'local_normal':n.tolist(),'local_fingers':([0,1,0] if end=='bottom' else [0,0,-1]),'mesh':name,'source':path,'triangle':index,'score':float(score)})
  out.append({'map':file.stem,'target':a.get('Name'),'points':points,'omitted_meshes':omitted,'status':'candidate only; requires rendered inspection, moving-instance audit and native eligibility tests'})
(R/'docs/v109-evidence/ladder_surface_candidates_hy.json').write_text(json.dumps(out,indent=2))
print('Candidate surfaces:',len(out),'areas;',sum(len(x['points']) for x in out),'points')
