from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_native_input_capture.py').read_text()
s=s.replace("'build/cpu73' if '--movement-replay'", "'build/jb-mechanism' if '--movement-replay'")
s=s.replace('entities/urban/kitchen/mug_coffee/mug_coffee.ent','entities/station/tech/control_board_pplant/control_board_pplant_knob.ent')
s=s.replace('cVector3f(-10,2.5f,7.5f)','cVector3f(-9,1.35f,8.5f)')
s=s.replace('cpuProp.GetMainBody().SetGravity(false);','cpuProp.WakeUp();')
exec(compile(s,str(r/'tests/test_native_input_capture.py'),'exec'))
vr=(out/'hpl3vr.log').read_text(errors='replace')
assert 'JB_MECHANISM_ACQUIRED' in vr,'Normal grip never acquired native knob; fixture is not motor validation'
assert 'released 1' in vr,'Release failed'
