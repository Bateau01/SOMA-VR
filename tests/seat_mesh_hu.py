from pathlib import Path
import xml.etree.ElementTree as E
g=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
for f in ['entities/station/furniture/chair_scan/chair_scan.dae','entities/oceanbottom/special/05_01_phi_pilotseat/05_01_phi_pilotseat_chair.dae']:
 root=E.parse(g/f).getroot();ns={'c':root.tag.split('}')[0][1:]}; mesh=root.find('.//c:mesh',ns);v=mesh.find('c:vertices/c:input',ns).get('source')[1:]
 src=next(x for x in mesh.findall('c:source',ns) if x.get('id')==v);vals=list(map(float,src.find('c:float_array',ns).text.split()));pts=[vals[i:i+3] for i in range(0,len(vals),3)]
 print(f,'bounds',[(min(p[k] for p in pts),max(p[k] for p in pts))for k in range(3)])
 for n in root.findall('.//c:visual_scene//c:node',ns):print('node',n.get('name'),[(x.tag.split('}')[-1],x.text.strip()) for x in n if x.tag.split('}')[-1] in ['matrix','translate','rotate','scale']])
 print('sample armregion', sorted(set(tuple(round(x,4) for x in p) for p in pts if .25<p[0]<.6 and .65<p[1]<1.2))[:35])

