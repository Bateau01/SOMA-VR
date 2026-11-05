"""Isolated locker replay with authentic map geometry; story setup omitted."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
case=sys.argv[sys.argv.index('--case')+1]
assert case in ('theta','omicron','ladder')
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/movement' if '--movement-replay'")
# Seed the player, not the interaction result. Keep native grip and mechanisms.
needle="if '--apartment-mechanisms' in sys.argv:\n  m=m.replace"
pos='20.5f,2.05f,6.9f' if case=='theta' else '-20.6f,3.05f,-45.8761f'
yaw='3.14159265f' if case=='theta' else '-1.5707963f'
if case=='ladder':pos='7.68505f,126.31f,88.95f';yaw='3.14159265f'
inject='if \'--theta-physics\' in sys.argv:\n  m=m.replace(\'cScript_RunGlobalFunc("MenuHandler","","IUStart");\',\'cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(POS),false);cLux_GetPlayer().GetCharacterBody().SetYaw(YAW);cLux_GetPlayer().GetCamera().SetYaw(YAW);cScript_RunGlobalFunc("MenuHandler","","IUStart");\',1)\n '.replace('POS',pos).replace('YAW',yaw)
s=s.replace(needle,inject+needle,1)
if case=='omicron':
 s=s.replace("'02_05_theta_inside' if '--theta-camera'", "'03_02_omicron_inside' if '--theta-camera'")
 s=s.replace("else 'chapter02'", "else 'chapter03'")
 # Select a normal unlocked locker fixture without claiming the story unlock.
 s=s.replace('void OnStart(){Player_SetActive(true);','void OnStart(){SwingDoor_SetLocked("03_02_diving_suit_locker_door_3",false,false);Entity_SetInteractionDisabled("03_02_diving_suit_locker_door_3",false);Player_SetActive(true);')
if case=='ladder':
 s=s.replace("'02_05_theta_inside' if '--theta-camera'", "'03_03_omicron_descent' if '--theta-camera'")
 s=s.replace("else 'chapter02'", "else 'chapter03'")
 s=s.replace('cScript_RunGlobalFunc("MenuHandler","","IUStart");', 'cScript_RunGlobalFunc("MenuHandler","","IUStart");Map_AddTimer("IZLadder",15.0f,"IZLadder");')
 # Invoke the genuine entity interaction, not a forced final player state.
 # This measures authored ladder entry; it does not certify hand target selection.
 s=s.replace("injection='void OnStart()", r"injection='void IZLadder(const tString &in name){LogNewLine(\"IZ_LADDER_BEFORE \"+Player_GetCurrentStateName());Entity_CallEntityInteract(\"Ladder1_Main\");Map_AddTimer(\"IZLadderCheck\",0.2f,\"IZLadderCheck\");}\nvoid IZLadderCheck(const tString &in name){LogNewLine(\"IZ_LADDER_AFTER \"+Player_GetCurrentStateName());}\nvoid OnStart()")
s=s.replace("'scenario':(", "'fixture_case':"+repr(case)+",'scenario':(")
ns={'__file__':str(r/'tests/test_native_input_capture.py'),'__name__':'__main__'}
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'),ns)
out=ns['out']

vr=(out/'hpl3vr.log').read_text(errors='replace')
import json
observed='CPU14_SAVED ok 1' in vr and ('IZ_TARGET_SURFACE' in vr if case!='ladder' else 'IZ_LADDER_AFTER State_Ladder' in (out/'hpl.log').read_text(errors='replace'))
(out/'iz-acceptance.json').write_text(json.dumps({'target_surface_found': 'IZ_TARGET_SURFACE' in vr,'capture_saved':'CPU14_SAVED ok 1' in vr,'case':case,'scope':('Native ladder callback entry only; physical targeting is not exercised.' if case=='ladder' else __doc__),'authored_door_operation_verified':False},indent=2))
assert observed, 'Target/capture not observed; no locker-interaction validation credit'
