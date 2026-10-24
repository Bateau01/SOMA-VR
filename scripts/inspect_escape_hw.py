from pathlib import Path
import xml.etree.ElementTree as E,json
root=Path('D:/SteamLibrary/steamapps/common/SOMA')
p=root/'static_objects/oceanbottom/building/communication_dome/communication_dome_inside_combined.dae'
r=E.parse(p).getroot();ns={'c':r.tag.split('}')[0][1:]};tri=[]
for mesh in r.findall('.//c:geometry/c:mesh',ns):
 sources={s.attrib['id']:[float(x) for x in s.find('c:float_array',ns).text.split()] for s in mesh.findall('c:source',ns) if s.find('c:float_array',ns) is not None}
 vertices={v.attrib['id']:v.find('c:input',ns).attrib['source'][1:] for v in mesh.findall('c:vertices',ns)}
 for prim in mesh.findall('c:triangles',ns):
  ins=prim.findall('c:input',ns);stride=1+max(int(i.attrib.get('offset','0')) for i in ins);v=next(i for i in ins if i.attrib['semantic']=='VERTEX');off=int(v.attrib.get('offset','0'));pts=sources[vertices[v.attrib['source'][1:]]]
  pts=[(12.25-pts[i+2],253.75+pts[i+1],-128.5+pts[i]) for i in range(0,len(pts),3)]
  ix=[int(x) for x in prim.find('c:p',ns).text.split()][off::stride]
  tri.extend([[pts[ix[j+k]] for k in range(3)] for j in range(0,len(ix),3)])
def hits(x,z):
 out=[]
 for a,b,c in tri:
  d=(b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2])
  if abs(d)<1e-10:continue
  u=((x-a[0])*(c[2]-a[2])-(c[0]-a[0])*(z-a[2]))/d;v=((b[0]-a[0])*(z-a[2])-(x-a[0])*(b[2]-a[2]))/d
  if u>=0 and v>=0 and u+v<=1:
   y=a[1]+u*(b[1]-a[1])+v*(c[1]-a[1])
   if 251<y<256:out.append(round(y,5))
 return sorted(set(out))
for x in [17,17.5,18,18.5,19,19.5,20,20.5,21]:
 print(x,[(z,hits(x,z)) for z in [-132,-131.5,-131,-130.5,-130,-129.5,-129]])

# Confirm the selected lip triangle and its outward normal.
import math
x,z=20.5,-130.5
for a,b,c in tri:
 d=(b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2])
 if abs(d)<1e-10:continue
 u=((x-a[0])*(c[2]-a[2])-(c[0]-a[0])*(z-a[2]))/d;v=((b[0]-a[0])*(z-a[2])-(x-a[0])*(b[2]-a[2]))/d
 if min(u,v)>=0 and u+v<=1:
  y=a[1]+u*(b[1]-a[1])+v*(c[1]-a[1])
  if 252<y<253:
   q=[b[i]-a[i] for i in range(3)];s=[c[i]-a[i] for i in range(3)];n=[q[1]*s[2]-q[2]*s[1],q[2]*s[0]-q[0]*s[2],q[0]*s[1]-q[1]*s[0]];l=math.sqrt(sum(t*t for t in n));n=[t/l for t in n]
   result={'point':[x,y,z],'normal':n,'triangle':[a,b,c],'mesh':str(p),'scope':'Static DAE triangle intersection; final visual pose unverified'}
   print(result);Path('docs/v109-evidence/escape_surface_hw.json').write_text(json.dumps(result,indent=2))
