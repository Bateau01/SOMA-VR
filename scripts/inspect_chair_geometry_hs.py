from pathlib import Path
import xml.etree.ElementTree as E
p=Path('D:/SteamLibrary/steamapps/common/SOMA/entities/urban/special/00_04_scan_chair/00_04_scan_chair.dae')
r=E.parse(p).getroot();ns={'c':r.tag.split('}')[0][1:]}
print('unit',r.find('c:asset/c:unit',ns).attrib)
for mesh in r.findall('.//c:geometry/c:mesh',ns):
 sources={s.attrib['id']:[float(x) for x in s.find('c:float_array',ns).text.split()] for s in mesh.findall('c:source',ns) if s.find('c:float_array',ns) is not None}
 vertices={v.attrib['id']:v.find('c:input',ns).attrib['source'][1:] for v in mesh.findall('c:vertices',ns)}
 for prim in list(mesh):
  if prim.tag.split('}')[-1] not in ('triangles','polylist'):continue
  ins=prim.findall('c:input',ns); stride=1+max(int(i.attrib.get('offset','0')) for i in ins)
  vertex=next(i for i in ins if i.attrib['semantic']=='VERTEX');off=int(vertex.attrib.get('offset','0'));pts=sources[vertices[vertex.attrib['source'][1:]]]
  pts=[tuple(1.625*v for v in pts[i:i+3]) for i in range(0,len(pts),3)]
  indices=[int(x) for x in prim.find('c:p',ns).text.split()][off::stride]
  counts=prim.find('c:vcount',ns);counts=[int(x) for x in counts.text.split()] if counts is not None else [3]*(len(indices)//3)
  print('bounds',[(min(p[i] for p in pts),max(p[i] for p in pts)) for i in range(3)])
  cursor=0;hits=[]
  for count in counts:
   poly=indices[cursor:cursor+count];cursor+=count
   for k in range(1,count-1):
    a,b,c=[pts[j] for j in (poly[0],poly[k],poly[k+1])]; x,z=.40625,.08447
    det=(b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2])
    if abs(det)<1e-10:continue
    u=((x-a[0])*(c[2]-a[2])-(c[0]-a[0])*(z-a[2]))/det
    v=((b[0]-a[0])*(z-a[2])-(x-a[0])*(b[2]-a[2]))/det
    if u>=0 and v>=0 and u+v<=1:hits.append(a[1]+u*(b[1]-a[1])+v*(c[1]-a[1]))
  print('vertical intersections at authored armrest xz',sorted(hits))
for n in r.findall('.//c:visual_scene/c:node',ns):print('node',n.attrib,[(x.tag.split('}')[-1],x.text) for x in n if x.tag.split('}')[-1] in ('matrix','translate','rotate','scale')])
