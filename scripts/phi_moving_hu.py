from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'runtime/script/props/Prop_Button.hps';s=p.read_text();a=s.index('    bool VR_PhiLaunchAllowed()');b=s.index('\tbool CanInteract',a);helper=s[a:b];s=s[:a]+s[b:];s=s.replace('        if(!VR_PhiLaunchAllowed())return false;\n','');p.write_text(s)
p=r/'runtime/script/props/Prop_MovingButton.hps';s=p.read_text();i=s.index('\tbool CanInteract');s=s[:i]+helper+s[i:];s=s.replace('        if(VRPowerPump() && (apBody is null || apBody !is mpMoveBody)) return false;','        if(!VR_PhiLaunchAllowed())return false;\n        if(VRPowerPump() && (apBody is null || apBody !is mpMoveBody)) return false;');p.write_text(s)
p=r/'tests/test_welcome_layout_hs.py';s=p.read_text().replace('10901','10902').replace('welcome_layout_hs.json','welcome_layout_hu.json');(r/'tests/test_welcome_layout_hu.py').write_text(s)

