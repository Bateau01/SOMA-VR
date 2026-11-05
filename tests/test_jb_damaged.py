"""Actual saved Omicron chip, synthetic controller one-grip pickup. Player is positioned by fixture; no native chip flags/callbacks bypassed."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/jb-damaged' if '--movement-replay'")
s=s.replace('00_01_apartment','03_02_omicron_inside').replace("'chapter00'","'chapter03'")
s=s.replace("expected_save_map='05-01-phi-inside'", "expected_save_map='03-02-omicron-inside' if '--apartment-mechanisms' in sys.argv else '05-01-phi-inside'")
s=s.replace('phase>13','phase>7')
s=s.replace("  else:\n   import re\n   m,n=re.subn", "  if True:\n   import re\n   m,n=re.subn")

s=s.replace('DesktopMirror="true" />','DesktopMirror="true" FingerTrackingEnabled="false" />')
s=s.replace('int iuNativePhase=0;', 'int iuNativePhase=0;if(phase==0){mbVRFingerTracking=false;cScript_RunGlobalFunc("VRCOMFORT","F","0");cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-1.7f,3.2f,49.4f),false);LogNewLine("JB_CHIP_PLAYER_PLACED");}')
# Do not spawn the normal synthetic mug; retain the actual saved native chip.
a=s.index(" if '--movement-replay' in sys.argv:\n  marker='void OnEnter()'")
b=s.index(" if '--theta-physics'",a)
s=s[:a]+s[b:]
# Place only player near saved chip. Native scene eligibility is retained.
needle=" put(G/f'maps/{chapter}/{map_name}/{map_name}.hps',m)"
s=s.replace(needle, " m=m.replace('cScript_RunGlobalFunc(\"MenuHandler\",\"\",\"IUStart\");','cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-1.7f,3.2f,49.4f),false);cScript_RunGlobalFunc(\"MenuHandler\",\"\",\"IUStart\");',1)\n"+needle)

# Setup is explicitly separate from chip acquisition: invoke the native gel
# button's connection callback, await its authored unlock, then position ONLY
# the cover open. This does not certify opening the cover with VR hands.
setup=r"""
 [nosave] float mfJBSetup=0;[nosave] bool mbJBStarted=false,mbJBCoverSetup=false;
 void JBSetup(float dt){mfJBSetup+=dt;if(mfJBSetup<2)return;
 if(!mbJBStarted){mbJBStarted=true;button_GelContainer_OnConnectionStateChange("button_GelContainer",1);LogNewLine("JB_SETUP_NATIVE_FAILURE_STARTED");}
 if(!mbJBCoverSetup&&mfJBSetup>5&&mbBioMechChipExploded&&!SwingDoor_GetLocked("FluidContainerFuseBox")){
  SwingDoor_SetOpenAmount("FluidContainerFuseBox",1);Map_GetProp("FluidContainerFuseBox").SetStaticPhysics(true);mbJBCoverSetup=true;
  LogNewLine("JB_SETUP_COVER_POSITIONED nativeUnlock=true exploded="+mbBioMechChipExploded+" open="+SwingDoor_GetOpenAmount("FluidContainerFuseBox"));
 }
 }
"""
inject="\n import re\n jbFixture="+repr(setup)+"\n jbAt=m.index('{',m.index('class cScrMap'));m=m[:jbAt+1]+jbFixture+m[jbAt+1:]\n jbUpdate=re.search(r'void Update\\(float (\\w+)\\)\\s*\\{',m);assert jbUpdate\n m=m[:jbUpdate.end()]+'JBSetup('+jbUpdate[1]+');'+m[jbUpdate.end():]\n"
s=s.replace(needle if False else " put(G/f'maps/{chapter}/{map_name}/{map_name}.hps',m)", inject+" put(G/f'maps/{chapter}/{map_name}/{map_name}.hps',m)")

exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))
vr=(out/'hpl3vr.log').read_text(errors='replace')
import json
report={'scope':'Actual OpenXR with synthetic wrist/grip/trigger input; saved Omicron map. Native failure callback and fixture-positioned static-open cover. Tests chip acquisition only, not VR cover opening or later repair/use.','acquired':'JB_DAMAGED_ACQUIRED' in vr,
        'released':'released 1' in vr,
        'setup_caveat':'Native failure callback exercised; cover positioned and held static-open by fixture after native unlock. Not a VR cover-opening test.',
        'cover_setup_confirmed':'JB_SETUP_COVER_POSITIONED' in (out/'hpl.log').read_text(errors='replace'),
        'one_grip_attempt':sum('JB_DAMAGED_FIXED_GRIP' in x or 'JB_DAMAGED_READY_GRIP' in x for x in vr.splitlines())==1,
        'native_rejections':[x for x in vr.splitlines() if 'NATIVE CanInteract' in x and 'FALSE' in x]}
(out/'damaged-chip-result.json').write_text(json.dumps(report,indent=2))
base_result=json.loads((out/'result.json').read_text());base_result['scope']=report['scope'];(out/'result.json').write_text(json.dumps(base_result,indent=2))
assert report['cover_setup_confirmed'], 'Native prerequisite setup not confirmed'
assert report['one_grip_attempt'], 'Expected one grip attempt'
if '--expect-early-miss' in sys.argv:
 assert receipt['arguments'].get('jb_early_grip'), 'Expected early-grip fixture identity'
 assert 'JB_CLOSURE_OBSERVE' in vr, 'No closure observation'
 assert 'JB_DAMAGED_ACQUIRED' not in vr, 'Baseline unexpectedly acquired; revisit hypothesis'
else:
 assert 'JB_DAMAGED_ACQUIRED' in vr, 'Damaged chip not held after ordinary grip'
assert 'released 1' in vr, 'Damaged chip release failed'
