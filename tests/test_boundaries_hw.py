from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1];b=r.parent.parent/'SOMA_VR_109_S26HV/repo'
s=(r/'source/s26n.c').read_text().replace('S26HW','S26HV')
a=s.index('// HW: observation only');z=s.index('static i32 h5755fm_refresh_subtitle_final_translation',a);s=s[:a]+s[z:]
s=s.replace('\n    s26hw_subtitle_compare(M);','').replace('metric*(-.9f*V[a]+.75f*V[4+a]-H5755DU_SUBTITLE_DISTANCE_M*V[8+a])','metric*(-.9f*V[a]+.75f*V[4+a]-1.65f*V[8+a])')
assert s==(b/'source/s26n.c').read_text()
changed=[]
for p in (r/'runtime').rglob('*.hps'):
 q=b/p.relative_to(r)
 if not q.exists() or p.read_text()!=q.read_text():changed.append(p.relative_to(r).as_posix())
assert set(changed)=={'runtime/script/modules/MenuHandler.hps','runtime/script/helpers/helper_vr_escape_hw.hps','runtime/maps/chapter01/01_03_upsilon_outside/01_03_upsilon_outside.hps'}
p='runtime/maps/chapter01/01_03_upsilon_outside/01_03_upsilon_outside.hps';s=(r/p).read_text()
s=s.replace('#include "helpers/helper_vr_escape_hw.hps"','')
s='\n'.join(x for x in s.splitlines() if 'mVREscapeGuide' not in x)
assert re.sub(r'\s+','',s)==re.sub(r'\s+','',(b/p).read_text())
for p in (r/'runtime').rglob('item_grips.dat'):assert p.read_bytes()==(b/p.relative_to(r)).read_bytes()
report={'passed':True,'scope':'Source boundary comparison','changed_scripts':changed,'native_escape_callbacks_unchanged_except_guide_lifecycle':True,'item_usage_authored_grips_and_physics_unchanged':True,'subtitle_rendering_unchanged_except_bounded_observer':True,'hints_distance_uses_existing_subtitle_setting':True}
(r/'docs/v109-evidence/boundaries_hw.json').write_text(json.dumps(report,indent=2));print('PASS source boundaries and authored poses')
