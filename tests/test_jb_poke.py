from pathlib import Path
import json, sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/jb-poke' if '--movement-replay'")
s=s.replace('entities/urban/kitchen/mug_coffee/mug_coffee.ent','entities/urban/utility/light_switch/light_switch.ent')
s=s.replace('cVector3f(-10,2.5f,7.5f)','cVector3f(-8,1.35f,8.5f)')
s=s.replace('phase>13','phase>7')
s=s.replace("  else:\n   import re\n   m,n=re.subn", "  if True:\n   import re\n   m,n=re.subn")
s=s.replace('DesktopMirror="true" />','DesktopMirror="true" FingerTrackingEnabled="false" />')
s=s.replace('cpuProp.GetMainBody().SetGravity(false);','cpuProp.WakeUp();')
instrument=r'''
 if '--occluded-poke' in sys.argv:
  import xml.etree.ElementTree as ET
  # Test-only solid plate, not a game asset or a replacement interaction surface.
  tree=ET.parse(G/'entities/urban/utility/light_switch/light_switch.ent');root=tree.getroot()
  shapes=root.find('ModelData/Shapes');shapes.clear()
  ET.SubElement(shapes,'Shape',{'ID':'2','Name':'JB_BlockerShape','RelativeRotation':'0 0 0','RelativeScale':'1 1 1','RelativeTranslation':'0 0 0','Rotation':'0 0 0','Scale':'0.3 0.3 0.01','ShapeType':'Box','WorldPos':'0 0 0'})
  bodies=root.find('ModelData/Bodies');body=bodies[0];bodies.clear();bodies.append(body)
  body.set('Name','JB_BlockerBody');body.set('WorldPos','0 0 0')
  for child in list(body):body.remove(child)
  ET.SubElement(body,'Shape',{'ID':'2'})
  variables=root.find('UserDefinedVariables');variables.set('EntityType','Prop_Grab')
  put(G/'entities/jb_poke_blocker.ent',ET.tostring(root,encoding='utf-8'))
 pp=G/'script/props/Prop_MovingButton.hps';ss=pp.read_text(encoding='utf-8-sig')
 ss=ss.replace('SetSwitchedOn(!mbSwitchedOn, true);','SetSwitchedOn(!mbSwitchedOn, true);if(mBaseObj.GetName()=="CPU6Cup")LogNewLine("JB_POKE_NATIVE_TOGGLE state="+mbSwitchedOn);')
 if '--locked-poke' in sys.argv:
  lock='SetLocked(apInstanceVars.GetVarBool("Locked",false), false);'
  assert ss.count(lock)==1
  ss=ss.replace(lock,lock+'if(mBaseObj.GetName()=="CPU6Cup"){SetLocked(true,false);LogNewLine("JB_POKE_LOCKED_SETUP");}')
 put(pp,ss)
'''
s=s.replace(" # Replace a leftover old fixture",instrument+"\n # Replace a leftover old fixture")
if '--occluded-poke' in sys.argv:
 marker='cpuProp.WakeUp();'
 assert marker in s
 s=s.replace(marker,marker+'cMatrixf jbPlate=cMatrixf_Identity;jbPlate.SetTranslation(cVector3f(-8,1.35f,8.58f));cLux_GetCurrentMap().CreateEntity("JB_PokeBlocker","entities/jb_poke_blocker.ent",jbPlate,cVector3f(1));LogNewLine("JB_POKE_BLOCKER_CREATED");')
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))
vr=(out/'hpl3vr.log').read_text(errors='replace');log=(out/'hpl.log').read_text(errors='replace')
report={'scope':'Actual OpenXR synthetic fingertip motion, authentic isolated light switch, slow touch and fast crossing, no direct callback injection. Omits lamp connection wiring.','toggles':log.count('JB_POKE_NATIVE_TOGGLE'),'accepted_touch':[x for x in vr.splitlines() if 'S26Y EXPERIMENTAL ROCKER NEAR:' in x and 'native result 1' in x]}
report['hand']=receipt['arguments'].get('jb_poke_hand',1);report['finger']=receipt['arguments'].get('jb_poke_finger',1)
report['locked']='--locked-poke' in sys.argv
report['occluded']='--occluded-poke' in sys.argv
report['variant']=receipt['arguments'].get('jb_swept_controls','see DLL identity')
(out/'poke-result.json').write_text(json.dumps(report,indent=2))
base=json.loads((out/'result.json').read_text());base['scope']=report['scope'];(out/'result.json').write_text(json.dumps(base,indent=2))
expected=0 if '--locked-poke' in sys.argv else 2
if '--locked-poke' in sys.argv:assert 'JB_POKE_LOCKED_SETUP' in log
if '--occluded-poke' in sys.argv:
 assert 'JB_POKE_BLOCKER_CREATED' in log
 assert any('S26HF RAY BODY' in line and 'name JB_PokeBlocker_JB_BlockerBody' in line for line in vr.splitlines()), 'No proof the tested ray actually hit the blocker'
 assert 'JB_SWEEP_RAY distance 0.140000' in vr, 'Fast crossing was not exercised'
 assert 'JB_WORLD_SWEEP hit' not in vr, 'Crossing path passed through the solid blocker'
 # Existing endpoint contact can reach behind a plate; compare native toggle
 # count with baseline separately rather than calling this whole-path proof.
else:
 assert report['toggles']==expected, 'Unexpected native toggle count for slow/fast poke and permission state'
