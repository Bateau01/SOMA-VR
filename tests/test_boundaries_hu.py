"""Payload/source boundaries and native asset identity checks, not a headset test."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E,re
r=Path(__file__).resolve().parents[1];b=r.parent.parent/'SOMA_VR_109_S26HT/repo'
unchanged=['runtime/script/modules/PlayerToolHandler.hps','runtime/script/custom_depth/prop_omnitool_slot.hps','source/authored_grips_el.inc','source/item_grips_ej.inc']
for f in unchanged:assert (r/f).read_bytes()==(b/f).read_bytes(),f
changed=[]
for p in (r/'runtime').rglob('*'):
 if not p.is_file() or p.suffix.lower() not in ['.hps','.hpm_area']:continue
 old=b/p.relative_to(r)
 if not old.exists() or p.read_bytes()!=old.read_bytes():changed.append(p.relative_to(r).as_posix())
allowed={'runtime/script/modules/MenuHandler.hps','runtime/script/player/PlayerState_Interact_Terminal.hps','runtime/script/props/Prop_MovingButton.hps','runtime/script/areas/Area_InteractAux.hps','runtime/script/helpers/helper_vr_seat_hu.hps','runtime/maps/chapter03/03_02_omicron_inside/03_02_omicron_inside.hps','runtime/maps/chapter05/05_01_phi_inside/05_01_phi_inside.hps','runtime/maps/chapter03/03_02_omicron_inside/03_02_omicron_inside.hpm_Area','runtime/maps/chapter05/05_01_phi_inside/05_01_phi_inside.hpm_Area'}
# Whitespace-only Prop_Button intermediate edit is normalized back to baseline.
assert set(changed)==allowed,changed
g=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
variants=['omnitool','omnitool_with_securitychip','omnitool_with_cortexchip','omnitool_with_securitychip_cortexchip']
for v in variants:
 p=g/'entities/station/gameplay/omnitool'/f'{v}.ent'
 root=E.parse(p).getroot();mesh=root.find('.//Mesh').get('Filename')
 assert Path(mesh).stem.lower()==v and (g/mesh).is_file(),v
for p in (r/'runtime/maps').rglob('*.hpm_Area'):
 old=E.parse(g/p.relative_to(r/'runtime')).getroot();new=E.parse(p).getroot()
 original={x.get('Name'):E.tostring(x) for x in old.iter('Area')};candidate={x.get('Name'):E.tostring(x) for x in new.iter('Area')}
 assert len(candidate)==len(original)+2
 for name,v in original.items():assert v.strip()==candidate[name].strip(),name
 for name in ['VRSeatArm_0','VRSeatArm_1']:assert 'Active="false"' in candidate[name].decode()
s=(r/'runtime/script/modules/MenuHandler.hps').read_text()
assert 'HPL3VR_Toggle("120HZ PHYSICS",7,' in s and 'HPL3VR_Toggle("TEXTURE BUDGET BOOST",9,' in s
assert '"NEXT PAGE" : "CONTINUE"' in s
result={'scope':__doc__,'unchanged':unchanged,'changed_scripts_and_areas':changed,'omni_variants':variants,'existing_area_definitions_unchanged':True,'settings_pagination':True}
(r/'docs/v109-evidence/boundaries_hu.json').write_text(json.dumps(result,indent=2));print('PASS usage/grip boundaries, four Omni-Tool model assets, added-only seat regions and menu pagination')

