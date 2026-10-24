"""Source/payload boundaries, not a substitute for native placement tests."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1]
B=R.parent.parent/'SOMA_VR_109_S26HS/repo'
result={}
for folder in ('runtime/maps','runtime/entities'):
 def digest(root):
  return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
 result[folder]={'unchanged':digest(R/folder)==digest(B/folder)}
 assert result[folder]['unchanged']
def outside(s):
 start=s.index('    void VR_ShowItemGuide(')
 end=s.index('    // Guidance evaluates the existing native permission callback only.',start)
 s=s[:start]+s[end:]
 return re.sub(r'\s+','',re.sub(r'//[^\n]*','',s))
assert outside((R/'runtime/script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig'))==outside((B/'runtime/script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig'))
result['tool_handler_outside_guides_unchanged']=True
grips=[]
for p in R.rglob('*'):
 if p.is_file() and ('grips' in p.name or p.name=='item_grips.dat') and p.parts[len(R.parts)] in ('runtime','source'):
  assert p.read_bytes()==(B/p.relative_to(R)).read_bytes(),p
  grips.append(str(p.relative_to(R)))
result['authored_grip_files_unchanged']=grips
d=json.loads((R/'docs/key-item-guide-routes-ht.json').read_text())
names={name for row in d['routes'] for name in row['items']}
expected={'ConfigChipTool','CortexChipTool','KateChip','GoyaChip','EnvironmentChip','BrainScanChip','chip_unformatted','door_panel_chip_formatted','ChipTool_Damaged','ChipTool_Repaired','PowerCubeTool','PowerCube_Inserted','BrokenRobotBrain','StructureGelTool','ARK','powerpack_1'}
assert names==expected and 'Tracer_Fluid' not in names and 'StunRod' not in names
result['coverage']={'names':sorted(names),'key_identities':len(names),'routes':len(d['routes']),'tracer_excluded':True}
(R/'docs/v109-evidence/unchanged_boundaries_ht.json').write_text(json.dumps(result,indent=2))
print('PASS unchanged campaign scripts, entity assets, authored grips and non-guide tool-handler logic; 16 key identities / 24 routes; tracer and baton excluded')
