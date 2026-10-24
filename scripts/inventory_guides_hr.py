"""Read authored guide candidates; entity file indices are SECTION-local."""
from pathlib import Path
import xml.etree.ElementTree as E
import json
R=Path(__file__).resolve().parents[1]
G=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
wanted={'BrokenRobotBrain','PowerCube_Inserted','StructureGelTool','chip_unformatted',
 'door_panel_chip_formatted','BrainScanChip','EnvironmentChip','ComputerBrainInBody',
 'PowerSourceInBody','ScanChair','security_chip_unformatted','Replaced_Chip_Target'}
rows=[]
for p in (G/'maps').glob('chapter*/*/*.hpm_Entity'):
 for section in E.parse(p).getroot().findall('Section'):
  table={f.get('Id'):f.get('Path') for f in section.findall('FileIndex_Entities/File')}
  for e in section.iter('Entity'):
   if e.get('Name') not in wanted:continue
   file=table[e.get('FileIndex')];asset=G/file
   mesh=E.parse(asset).find('./ModelData/Mesh')
   rows.append({'map':p.parent.name,'section':section.get('Name'),'entity':dict(e.attrib),
      'file':file,'mesh':dict(mesh.attrib) if mesh is not None else None})
out=R/'docs/v109-evidence/guide_authored_inventory.json'
out.write_text(json.dumps(rows,indent=2))
for r in rows:print(r['map'],r['entity']['Name'],r['file'],r['mesh'])
