from pathlib import Path
import xml.etree.ElementTree as E
g=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
for f,xs,zs in [('entities/station/furniture/chair_scan/chair_scan.dae',[.4,-.4,-.5],[-.4,-.2,0]),('entities/oceanbottom/special/05_01_phi_pilotseat/05_01_phi_pilotseat_chair.dae',[.4,.5,-.4],[-.8,-.6,-.4])]:
 root=E.parse(g/f).getroot();n={'c':root.tag.split('}')[0][1:]};mesh=root.find('.//c:mesh',n)
 vs=mesh.find('c:vertices/c:input',n).get('source')[1:]
 src=next(x for x in mesh.findall('c:source',n) if x.get('id')==vs);a=list(map(float,src.find('c:float_array',n).text.split()));pts=[a[i:i+3] for i in range(0,len(a),3)]
 m=list(map(float,root.find('.//c:visual_scene/c:node/c:matrix',n).text.split()))
 pts=[[sum(m[k*4+j]*v[j] for j in range(3))+m[k*4+3] for k in range(3)] for v in pts]
 tris=[]
 for t in mesh.findall('c:triangles',n)+mesh.findall('c:polylist',n):
  inp=t.findall('c:input',n);stride=max(int(x.get('offset')) for x in inp)+1;off=int(next(x for x in inp if x.get('semantic')=='VERTEX').get('offset'));a=list(map(int,t.find('c:p',n).text.split()));ids=a[off::stride]
  counts=list(map(int,t.find('c:vcount',n).text.split())) if t.find('c:vcount',n) is not None else [3]*(len(ids)//3)
  at=0
  for count in counts:
   poly=ids[at:at+count];at+=count
   for k in range(1,count-1):tris.append([pts[poly[0]],pts[poly[k]],pts[poly[k+1]]])
 print(f)
 for x in xs:
  for z in zs:
   ys=[]
   for a,b,c in tris:
    d=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
    if abs(d)<1e-9:continue
    u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/d;v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/d
    if min(u,v,1-u-v)>=-1e-5:ys.append(u*a[1]+v*b[1]+(1-u-v)*c[1])
   print(x,z,sorted(set(round(y,5) for y in ys)))

 from PIL import Image,ImageDraw
 image=Image.new('RGB',(900,800),(24,30,35));draw=ImageDraw.Draw(image)
 def project(v):return (v[0]*.866+v[2]*.5,-v[1]*.90+v[2]*.433-v[0]*.25)
 pp=[project(v) for v in pts];lo=[min(p[k] for p in pp)for k in range(2)];hi=[max(p[k] for p in pp)for k in range(2)]
 scale=min(780/(hi[0]-lo[0]),650/(hi[1]-lo[1]))
 def screen(v):
  q=project(v);return ((q[0]-lo[0])*scale+60,(q[1]-lo[1])*scale+75)
 def depth(tri):return sum(v[0]*.45-v[2]*.78-v[1]*.4 for v in tri)/3
 for tri in sorted(tris,key=depth):
  a,b,c=tri;u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)];normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=sum(q*q for q in normal)**.5
  shade=int(95+95*abs(normal[1])/length) if length else 95
  draw.polygon([screen(v)for v in tri],fill=(shade,shade,shade))
 y,z=(.94729,-.25)if 'chair_scan/' in f else (1.08857,-.6)
 for x in [-.4,.4]:
  p=screen([x,y,z]);draw.ellipse((p[0]-7,p[1]-7,p[0]+7,p[1]+7),fill=(0,255,200))
 draw.text((30,25),'Native mesh projection - cyan: added armrest contact/guide anchors',fill='white')
 dest=Path(__file__).resolve().parents[1]/'docs/v109-evidence'/('seat_'+Path(f).stem+'_hu.png');image.save(dest)



