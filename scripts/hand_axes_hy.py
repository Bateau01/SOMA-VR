from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
R=Path(__file__).resolve().parents[1];ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
r=E.parse(R/'runtime/entities/soma_vr/s26f/hand_diving_right.dae')
def walk(node,parent):
 m=node.find('c:matrix',ns);world=parent@(np.fromstring(m.text,sep=' ').reshape(4,4) if m is not None else np.eye(4))
 if node.get('name') in ['VR_J07','VR_J15','VR_J18','VR_J19','VR_J22']:print(node.get('name'),world[:3,3])
 for c in node.findall('c:node',ns):walk(c,world)
for node in r.findall('.//c:visual_scene/c:node',ns):walk(node,np.eye(4))
