"""Campaign instance inventory and source-preservation audit; not gameplay validation."""
from pathlib import Path
import json,re,zipfile,hashlib,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA');rows=[];empty=0
for p in sorted((G/'maps').rglob('*.hpm_Entity')):
 root=E.parse(p).getroot()
 for sec in root.iter('Section'):
  files={x.get('Id'):x.get('Path') for x in sec.iter('File')}
  for e in sec.iter('Entity'):
   v={x.get('Name'):x.get('Value') for x in e.iter('Var')}
   if 'LeaveCallback' not in v:continue
   if not v['LeaveCallback']:empty+=1;continue
   mp=p.relative_to(G).as_posix().replace('.hpm_Entity','.hps');src=R/'runtime'/mp
   if not src.exists():src=G/mp
   text=src.read_text(encoding='utf-8-sig');name=v['LeaveCallback'];exists=bool(re.search(r'void\s+'+re.escape(name)+r'\(',text))
   rows.append(dict(map=mp,entity=e.get('Name'),asset=files.get(e.get('FileIndex')),leave=name,method_exists=exists))
policies=json.loads((R/'docs/v109-evidence/terminal_policies_io.json').read_text())
for policy in policies:
 path=Path(policy['file']).as_posix();now=(R/path).read_text(encoding='utf-8-sig')
 assert hashlib.sha256(now.replace(policy['policy'],'',1).encode()).hexdigest()==policy['baseline_sha256'],path
checks=json.loads((R/'tests/fixtures/in_baseline/terminal_preservation_io.json').read_text())
for path,expected in checks.items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==expected,path
for row in rows:
 key='runtime/'+row['map'];found=next((x for x in policies if Path(x['file']).as_posix()==key and row['entity'] in x['allow']),None)
 if found:row['decision']='explicit fixed-terminal world-controls permission; native exit retained'
 elif '02_05_theta_inside' in key:row['decision']='existing IN policy; running simulation restriction retained'
 elif not row['method_exists']:row['decision']='callback not implemented; existing shared gate treats it as no sequence owner'
 else:row['decision']='unchanged restrictive policy: handheld/phone or shuttle ownership'
 assert found or '02_05_theta_inside' in key or not row['method_exists'] or row['entity'] in ['CellPhoneArm','Cellphone','TrainTerminal','AmyCargoPad','CathPad','ToBeFlesherPad','CrewPad'],row
hits=[]
for p in (G/'maps').rglob('*.hps'):
 if 'Terminal_SetLeaveCallback(' in p.read_text(encoding='utf-8-sig'):hits.append(str(p))
assert not hits,hits
result={'scope':__doc__,'callback_owned_instances':len(rows),'empty_callback_instances':empty,'dynamic_map_leave_setters':hits,'preserved':'shared terminal state byte-identical; new map methods are the sole map changes vs IN; all original callbacks preserved','instances':rows}
(R/'docs/v109-evidence/terminal_audit_io.json').write_text(json.dumps(result,indent=2));print('PASS',len(rows),'named callbacks,',empty,'empty callbacks; every named instance classified; callbacks/tapping/laser/exit source unchanged')
