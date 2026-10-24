from pathlib import Path
import xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
for p in (R/'runtime/entities/soma_vr/s26f').glob('hand*.dae'):
 root=E.parse(p)
 a=root.find('.//c:source[@id="Handpositions"]/c:float_array',ns)
 v=list(map(float,a.text.split()))
 print(p.name,[(round(min(v[i::3]),4),round(max(v[i::3]),4)) for i in range(3)])
