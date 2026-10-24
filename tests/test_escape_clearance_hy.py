"""Sample exported bind mesh against native static lip, not headset skinning."""
from pathlib import Path
import sys,json,xml.etree.ElementTree as E,numpy as np
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from escape_surface_hy import ray
ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
d=E.parse(R/'runtime/entities/soma_vr/s26f/hand_diving_right.dae');g=d.find('.//c:geometry',ns)
source=g.find('.//c:vertices/c:input',ns).get('source')[1:]
v=np.fromstring(g.find('.//c:source[@id="'+source+'"]/c:float_array',ns).text,sep=' ').reshape(-1,3)
report=[]
for scale in [.75,1,1.25,1.5]:
 local=v*scale;root=np.array([19.75,254.687,-130.3])+np.array([-.1176,.0441,0])*(scale-1)
 world=np.column_stack((-local[:,1],local[:,2],-local[:,0]))+root;worst=-100.;tested=0
 for p in world[::max(1,len(world)//700)]:
  hits=[256-t for t,k in ray((p[0],256,p[2]),(0,-1,0)) if 253.9<256-t<255.2]
  if hits:worst=max(worst,max(hits)-p[1]);tested+=1
 report.append({'scale':scale,'samples_over_surface':tested,'max_penetration_metres':float(worst),'passed':bool(tested>0 and worst<0)})
(R/'docs/v109-evidence/escape_clearance_scales_hy.json').write_text(json.dumps({'scope':__doc__,'results':report},indent=2))
print(json.dumps(report));assert all(i['passed'] for i in report)
