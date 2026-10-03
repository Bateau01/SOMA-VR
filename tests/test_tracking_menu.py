from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'runtime/script/modules/MenuHandler.hps').read_text()
checks=['p.GetBool("SOMA_VR_Comfort","FingerTrackingEnabled",true)', 'p.SetBool("SOMA_VR_Comfort","FingerTrackingEnabled",mbVRFingerTracking)', 'cScript_RunGlobalFunc("VRCOMFORT","F",mbVRFingerTracking ? "1" : "0")', 'HPL3VR_Toggle("FINGER TRACKING",5,mbVRFingerTracking)', 'HPL3VR_Option("BUTTON BINDINGS",7)', '(mlVRComfortCategory==1 ? 8 : ((mlVRComfortCategory<0 || mlVRComfortCategory==7) ? 6 : 5))', 'size.y=440;',
 'HPL3VR_Option("HANDS AND HAPTICS",5)', 'if(mlVRComfortCategory==7) { size.y=400;', 'if(mlVRComfortCategory<0) size.y=400;']
for key,cls,label,row,default in [('SmartGrip','U','SMART GRIP',0,'true'),('GripPressure','Z','GRIP PRESSURE',1,'true'),('PointToPress','P','POINT TO PRESS',2,'true'),('AnyFingerKeypads','K','ANY FINGER ON KEYPADS',3,'false'),('CreatureHaptics','X','CREATURE HAPTICS',4,'true'),('ButtonHints','I','BUTTON HINTS',5,'true')]:
    var='mbVR'+key
    checks+=[f'{var}=p.GetBool("SOMA_VR_Hands","{key}",{default})',f'p.SetBool("SOMA_VR_Hands","{key}",{var})',f'cScript_RunGlobalFunc("VRCOMFORT","{cls}",{var} ? "1" : "0")',f'HPL3VR_Toggle("{label}",{row},{var})']
for c in checks: assert c in s,c
assert 275+8*38+38<=260+440
assert 275+6*38+38<=260+400 # top level and HANDS AND HAPTICS: BACK on row 6
p=(R/'source/controller_policy_u.inc').read_text(); assert '__atomic_load_n(&g_s26djFingerTracking' in p
p=(R/'source/skeletal_q.inc').read_text(); assert '__atomic_store_n(&g_s26qRootInput[h][f],0ULL' in p
assert 's26dj_set_finger_tracking' in (R/'source/s26n.c').read_text()
print('PASS: menu load/save/publish wiring, toggle/bindings/back row separation and panel bounds; tracking gate and authored root pose source contracts. Static checks, not script-VM execution.')


