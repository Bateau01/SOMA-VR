from pathlib import Path
import numpy as np,sys,xml.etree.ElementTree as E,json
r=Path.cwd();sys.path.insert(0,str(r/'scripts'));import escape_surface_hy as surfaces; surfaces.tri=np.load(r/'docs/v109-evidence/escape_all_surfaces_hz.npz')['tri']; ray=surfaces.ray
ns={'c':'http://www.collada.org/2005/11/COLLADASchema'};g=E.parse(r/'runtime/entities/soma_vr/s26f/hand_diving_right.dae').find('.//c:geometry',ns);src=g.find('.//c:vertices/c:input',ns).get('source')[1:];v=np.fromstring(g.find('.//c:source[@id="'+src+'"]/c:float_array',ns).text,sep=' ').reshape(-1,3)
# Native area rotation: Rz Ry Rx; world-to-area = transpose.
x,y,z=.216689,-1.28631,-.0437412;cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z);rot=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
n=np.array([-.9876889,0,.1564311]);mat=np.array([[-.1564311,0,-.9876889],[0,-1,0],[-.9876889,0,.1564311]]);at=np.array([19.5139,253.78,-130.3]);rows=[]
for scale in [.75,1,1.25,1.5]:
 world=(v*scale)@mat.T+at+n*.10*scale;local=(world-np.array([19.7302,254.326,-130.45]))@rot;inside=bool((np.abs(local)<np.array([2.94989,4.66361,1.16606])/2).all());clearances=[]
 for p in world[::max(1,len(world)//700)]:
  hits=ray((18,p[1],p[2]),(1,0,0));hits=[18+t for t,k in hits if 19<18+t<21]
  if hits:clearances.append(min(hits)-p[0])
 ok=inside and len(clearances)>100 and min(clearances)>0;rows.append({'scale':scale,'entire_mesh_inside_area':inside,'samples':len(clearances),'minimum_wall_clearance_m':min(clearances),'pass':bool(ok)});assert ok,rows[-1]
(r/'docs/v109-evidence/escape_lower_clearance_hz.json').write_text(json.dumps(rows,indent=2));print(rows)
