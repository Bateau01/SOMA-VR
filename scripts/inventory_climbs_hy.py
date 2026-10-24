from pathlib import Path
import xml.etree.ElementTree as E,json
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA')
out=[]
for p in sorted((G/'maps').glob('chapter*/*/*.hpm_Area')):
 for a in E.parse(p).iter('Area'):
  vs={v.get('Name'):v.get('Value') for v in a.findall('./UserVariables/Var')}
  cb=vs.get('PlayerInteractCallback','') or vs.get('PlayerInteractCallbackFunc','')
  if a.get('AreaType')=='Ladder' or (cb and any(x in (cb+' '+a.get('Name','')).lower() for x in ('climb','ladder','stair','vent'))):
   out.append({'map':p.stem,'area':a.attrib,'vars':{k:v for k,v in vs.items() if v not in ('','false','0')}})
(R/'docs/v109-evidence').mkdir(parents=True,exist_ok=True)
(R/'docs/v109-evidence/climb_inventory_hy.json').write_text(json.dumps(out,indent=2))
for a in out:print(a['map'],a['area']['Name'],a['area']['AreaType'],a['area']['WorldPos'],a['vars'])
