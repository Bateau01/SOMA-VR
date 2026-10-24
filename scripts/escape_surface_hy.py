from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
G=Path('D:/SteamLibrary/steamapps/common/SOMA');ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
tris=[]
for name in ['communication_dome_inside_combined','communication_dome_plates_insides_version']:
 r=E.parse(G/f'static_objects/oceanbottom/building/communication_dome/{name}.dae')
 for mesh in r.findall('.//c:geometry/c:mesh',ns):
  sources={s.get('id'):np.fromstring(s.find('c:float_array',ns).text,sep=' ') for s in mesh.findall('c:source',ns) if s.find('c:float_array',ns) is not None}
  vertices={v.get('id'):v.find('c:input',ns).get('source')[1:] for v in mesh.findall('c:vertices',ns)}
  for p in mesh.findall('c:triangles',ns):
   ins=p.findall('c:input',ns);stride=max(int(i.get('offset','0')) for i in ins)+1
   i=next(i for i in ins if i.get('semantic')=='VERTEX');v=sources[vertices[i.get('source')[1:]]].reshape(-1,3)
   v=np.stack([12.25-v[:,2],253.75+v[:,1],-128.5+v[:,0]],axis=1)
   idx=np.fromstring(p.find('c:p',ns).text,sep=' ',dtype=int).reshape(-1,stride)[:,int(i.get('offset','0'))]
   tris.extend(v[idx].reshape(-1,3,3))
tri=np.array(tris)
def ray(origin,dir):
 a=tri[:,0];u=tri[:,1]-a;v=tri[:,2]-a;h=np.cross(np.array(dir),v);det=np.sum(u*h,axis=1)
 good=np.abs(det)>1e-8;inv=np.zeros_like(det);inv[good]=1/det[good];s=np.array(origin)-a
 b=np.sum(s*h,axis=1)*inv;q=np.cross(s,u);c=np.sum(q*dir,axis=1)*inv;t=np.sum(v*q,axis=1)*inv
 ix=np.where(good&(b>=0)&(c>=0)&(b+c<=1)&(t>=0))[0]
 return sorted([(float(t[k]),k) for k in ix])
if __name__=='__main__':
 for y in [252.5,253,253.25,253.5,253.75,254,254.25]:
  print(y,[(z,[(round(t+18,3),k) for t,k in ray((18,y,z),(1,0,0)) if t<4]) for z in [-130.6,-130.3,-130,-129.7]])
 for x in [18.8,19,19.2,19.4,19.6]:
  print('down',x,[(z,[(round(255-t,3),k) for t,k in ray((x,255,z),(0,-1,0)) if t<2]) for z in [-130.6,-130.3,-130,-129.7]])
