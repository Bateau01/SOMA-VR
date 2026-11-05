from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/jb-contact' if '--movement-replay'")
asset='entities/oceanbottom/special/03_03_elevator_tech_parts/03_03_elevator_fuse_box_rod.ent' if '--climber-rod' in sys.argv else 'entities/station/gameplay/substation_powerpanel/substation_powerpanel_flipbutton.ent'
s=s.replace('entities/urban/kitchen/mug_coffee/mug_coffee.ent',asset)
s=s.replace('cVector3f(-10,2.5f,7.5f)','cVector3f(-8,1.35f,8.5f)')
s=s.replace('phase>13','phase>7')
# This acquisition fixture has no locomotion. Pin authored yaw on every Update,
# not only OnStart (the general movement harness deliberately permits turns).
s=s.replace("  else:\n   import re\n   m,n=re.subn", "  if True:\n   import re\n   m,n=re.subn")

s=s.replace('DesktopMirror="true" />','DesktopMirror="true" FingerTrackingEnabled="false" />')
s=s.replace('cpuProp.GetMainBody().SetGravity(false);','cpuProp.WakeUp();')
instrument=r'''
 pp=G/'script/player/PlayerState_Interact_MovingButton.hps';ss=pp.read_text(encoding='utf-8-sig')
 ss=ss.replace('void Update(float afTimeStep)', '[nosave] float mfJBHeldTime=0;\nvoid Update(float afTimeStep)')
 ss=ss.replace('if(CheckShouldUpdate()==false) return;', 'mfJBHeldTime+=afTimeStep;if(CheckShouldUpdate()==false) return;')
 ss=ss.replace('ResetPropInteractVars();','LogNewLine("JB_ROUTER_HELD_SECONDS="+mfJBHeldTime);ResetPropInteractVars();')
 ss=ss.replace('mbStartState = mbCurrentState;', 'LogNewLine("JB_CONTACT_INITIAL state="+mbCurrentState+" direction="+mvInputDirection.x+","+mvInputDirection.y+" minSpeed="+mfMinSpeed);mbStartState = mbCurrentState;')
 ss=ss.replace('// State has changed, so make sure direction must be changed to toggle state.', 'LogNewLine("JB_ROUTER_NATIVE_TOGGLE"); // State has changed, so make sure direction must be changed to toggle state.')
 ss=ss.replace('EnterInteractState(alPrevStateId);','LogNewLine("JB_ROUTER_STATE_ENTER prev="+alPrevStateId);EnterInteractState(alPrevStateId);')
 ss=ss.replace('ResetPropInteractVars();','LogNewLine("JB_ROUTER_STATE_LEAVE next="+alNextStateId);ResetPropInteractVars();')
 ss=ss.replace('if(cInput_IsTriggered(eAction_Interact)==false)','if(cInput_IsTriggered(eAction_Interact)==false)')
 ss=ss.replace('cLux_GetPlayer().ChangeState(mlPreviousState);','LogNewLine("JB_ROUTER_CANCEL held="+cInput_IsTriggered(eAction_Interact)+" distance="+cMath_Vector3Dist(mBaseObj.mpPlayer.GetCamera().GetPosition(),cLux_ID_Body(mBodyID).GetLocalPosition())+" max="+mfMaxDistance);cLux_GetPlayer().ChangeState(mlPreviousState);')
 put(pp,ss)
 pp=G/'script/props/Prop_MovingButton.hps';ss=pp.read_text(encoding='utf-8-sig')
 marker='bool OnInteract(int alType, iPhysicsBody@ apBody, const cVector3f &in avFocusPos, const tString&in asData)'
 at=ss.index('{',ss.index(marker))+1
 ss=ss[:at]+'LogNewLine("JB_ROUTER_PROP name="+mBaseObj.GetName()+" locked="+mbLocked+" disabled="+mbDisabled+" simple="+mbSimplePressInteraction);'+ss[at:]
 put(pp,ss)
 (out/'router-instrumented.hps').write_text(ss)
'''
s=s.replace(" # Replace a leftover old fixture",instrument+"\n # Replace a leftover old fixture")
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))
vr=(out/'hpl3vr.log').read_text(errors='replace')
assert 'JB_ROUTER_ACQUIRED' in vr,'Normal grip never acquired native switch'
assert 'released 1' in vr,'Release failed'

log=(out/'hpl.log').read_text(errors='replace')
assert 'JB_ROUTER_NATIVE_TOGGLE' in log, 'Acquisition alone is insufficient: native switch never toggled'
assert 'JB_ROUTER_STATE_LEAVE' in log, 'Native interaction did not leave its state'

assert 'JB_HAND_SOLID_REGISTERED' in vr, 'Moving body registration missing'
assert 'JB_HAND_SOLID_CONTACT' in vr, 'No physical Newton hand contact observed'

assert vr.index("JB_HAND_SOLID_REGISTERED") < vr.index("JB_ROUTER_READY_GRIP"), "Collision must register before the first grab"
