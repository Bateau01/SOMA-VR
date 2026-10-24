from pathlib import Path
import xml.etree.ElementTree as E
g=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
for mapname in ['03_02_omicron_inside','05_01_phi_inside']:
 p=next((g/'maps').rglob(mapname+'.hpm_Entity'));root=E.parse(p).getroot()
 files={x.get('Id',x.get('ID')):x.get('Path') for x in root.iter('File')}
 for x in root.iter('Entity'):
  pos=[float(v) for v in x.get('WorldPos','0 0 0').split()]
  if (mapname.startswith('03') and sum((a-b)**2 for a,b in zip(pos,[-23.7461,4.10419,-54.1613]))<6) or x.get('Name')=='pilot_seat':
   print(mapname,x.attrib,files.get(x.get('FileIndex')))
 p=p.with_suffix('.hpm_Area')
 for x in E.parse(p).getroot().iter('Area'):
  if x.get('Name')=='Area_ScanChair': print('AREA',x.attrib,E.tostring(x).decode())

