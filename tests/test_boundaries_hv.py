from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];B=R.parent.parent/'SOMA_VR_109_S26HU/repo';changed=[]
for folder in ['runtime/script','runtime/maps','runtime/entities','source']:
 for p in (R/folder).rglob('*'):
  if not p.is_file():continue
  q=B/p.relative_to(R)
  if not q.exists() or p.read_bytes()!=q.read_bytes():changed.append(p.relative_to(R).as_posix())
assert set(changed)=={'runtime/script/modules/PlayerToolHandler.hps','runtime/script/modules/MenuHandler.hps','source/s26n.c'},changed
for name in ['runtime/script/modules/MenuHandler.hps','source/s26n.c']:
 assert (R/name).read_bytes().replace(b'S26HV',b'S26HU')==(B/name).read_bytes()
def stripguide(s):
 a=s.index('    tString VR_ResolveOmniGuideTarget(') if '    tString VR_ResolveOmniGuideTarget(' in s else s.index('    void _Global_VRCanGuideOmniSlot()')
 b=s.index('void _Global_VRPhysicalOmniUseSlot()',a)
 return s[:a]+s[b:]
assert stripguide((R/'runtime/script/modules/PlayerToolHandler.hps').read_text())==stripguide((B/'runtime/script/modules/PlayerToolHandler.hps').read_text())
for p in (R/'runtime').rglob('item_grips.dat'):assert p.read_bytes()==(B/p.relative_to(R)).read_bytes()
d=json.loads((R/'docs/key-item-guide-routes-ht.json').read_text());names={n for x in d['routes'] for n in x['items']}
assert len(names)==16 and len(d['routes'])==24 and not {'Tracer_Fluid','StunRod'}&names
(R/'docs/v109-evidence/boundaries_hv.json').write_text(json.dumps({'changed':changed,'outside_guide_function_identical':True,'key_identity_count':len(names),'key_route_count':len(d['routes']),'excluded':['Tracer_Fluid','StunRod'],'maps_entities_holster_physics_renderer_unchanged':True},indent=2))
print('PASS guide-only code change plus version labels; 16 key identities/24 routes; authored grips unchanged')
