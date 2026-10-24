from pathlib import Path
import re,json,math
r=Path('.');b=r.resolve().parent.parent/'SOMA_VR_109_S26HW/repo'
s=(r/'source/s26n.c').read_text().replace('S26HX','S26HW')
a=s.index('    if(h5748t_sso_eq(objectName,"VRESCAPE",8u)){');z=s.index('    if(h5748t_sso_eq(objectName,"VRGUIDEH",8u)){',a);s=s[:a]+s[z:]
old=(b/'source/s26n.c').read_text();a=old.index('// HW: observation only');z=old.index('static i32 h5755fm_refresh_subtitle_final_translation',a);old=old[:a]+old[z:];old=old.replace('\n    s26hw_subtitle_compare(M);','');assert s==old
assert 'SUBTITLE FINAL PASS PAIR' not in (r/'source/s26n.c').read_text()
for rel in ['runtime/script/modules/PlayerToolHandler.hps','runtime/maps/chapter01/01_03_upsilon_outside/01_03_upsilon_outside.hps']:
 assert (r/rel).read_bytes()==(b/rel).read_bytes()
log=(r/'docs/v109-evidence/user-hw.log').read_bytes().decode(errors='replace');pairs=re.findall(r'rotation-max-delta ([\d.]+) translation-delta\(([^)]+)\)',log)
report={'subtitle_diagnostics_removed':True,'subtitles_and_interactions_unchanged':True,'sample_count':len(pairs),'maximum_rotation_component_delta':max(float(x[0]) for x in pairs),'maximum_translation_world_units':max(math.sqrt(sum(float(v)**2 for v in x[1].split())) for x in pairs),'eye_identity_not_established':True}
(r/'docs/v109-evidence/boundaries_hx.json').write_text(json.dumps(report,indent=2));print(report)
p=r/'scripts/package_hx.py';s=p.read_text().replace("['escape_hw.json','escape_surface_hw.json','text_hw.json','hint_anchor_hs.json','installer_delivery_hw.json']","['escape_hx.json','boundaries_hx.json','installer_delivery_hx.json']");p.write_text(s)
