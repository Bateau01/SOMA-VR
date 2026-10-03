from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'runtime/script/modules/MenuHandler.hps').read_text()
checks=['p.GetBool("SOMA_VR_Comfort","FingerTrackingEnabled",true)', 'p.SetBool("SOMA_VR_Comfort","FingerTrackingEnabled",mbVRFingerTracking)', 'cScript_RunGlobalFunc("VRCOMFORT","F",mbVRFingerTracking ? "1" : "0")', 'HPL3VR_Toggle("FINGER TRACKING",5,mbVRFingerTracking)', 'HPL3VR_Option("BUTTON BINDINGS",7)', 'HPL3VR_Option("BACK",mlVRComfortCategory==0 ? 7 : (mlVRComfortCategory==2 ? 10 : ((mlVRComfortCategory==3 || mlVRComfortCategory==7) ? 9 : (mlVRComfortCategory==1 ? 8 : (mlVRComfortCategory<0 ? 6 : 5)))))', 'size.y=440;',
 'HPL3VR_Option("HANDS AND HAPTICS",5)', 'if(mlVRComfortCategory==7) { size.y=430;', 'if(mlVRComfortCategory<0) size.y=400;']
for key,cls,label,row,default in [('SmartGrip','U','SMART GRIP',0,'true'),('GripPressure','Z','GRIP PRESSURE',1,'true'),('PointToPress','P','POINT TO PRESS',2,'true'),('AnyFingerKeypads','K','ANY FINGER ON KEYPADS',3,'false'),('CreatureHaptics','X','CREATURE HAPTICS',4,'true'),('ButtonHints','I','BUTTON HINTS',5,'true'),
                                  ('HeadTapFlashlight','H','HEAD TAP FLASHLIGHT',6,'true'),('LadderClimb','L','CLIMB LADDERS WITH HANDS',7,'true')]:
    var='mbVR'+key
    checks+=[f'{var}=p.GetBool("SOMA_VR_Hands","{key}",{default})',f'p.SetBool("SOMA_VR_Hands","{key}",{var})',f'cScript_RunGlobalFunc("VRCOMFORT","{cls}",{var} ? "1" : "0")',f'HPL3VR_Toggle("{label}",{row},{var})']
for c in checks: assert c in s,c
assert 275+8*38+38<=260+440
assert 275+6*38+38<=260+400 # top level: BACK on row 6
# S26ED rows. Body is script-only (PlayerHandsHandler pulls it); the VIDEO
# options publish to the DLL. Render scale is a 60..150% slider in 5% steps.
checks=['mbVRShowBody=p.GetBool("SOMA_VR_Hands","ShowBody",false)','p.SetBool("SOMA_VR_Hands","ShowBody",mbVRShowBody)','HPL3VR_Toggle("SHOW BODY (EXPERIMENTAL)",8,mbVRShowBody)',
 'void HPL3VR_GetShowBody() { cScript_SetGlobalReturnBool(gbHPL3VRRuntimeActive && mbVRShowBody); }',
 'mlVRRenderScale=p.GetInt("SOMA_VR_Video","RenderScaleIndex",8);if(mlVRRenderScale<0 || mlVRRenderScale>18) mlVRRenderScale=8;',
 'p.SetInt("SOMA_VR_Video","RenderScaleIndex",mlVRRenderScale)','cScript_RunGlobalFunc("VRCOMFORT","O",""+mlVRRenderScale)',
 'bool scaleActive=cScript_RunGlobalFunc("VRCOMFORT","O","A"+mlVRRenderScale);',
 'HPL3VR_Slider("RENDER SCALE",7,mlVRRenderScale,18,""+(60+5*mlVRRenderScale)+"%"+(scaleActive ? "" : " (RESTART)"))',
 'size.y=450; }']
for key,cls,label,row in [('DepthLayer','Q','DEPTH FOR REPROJECTION',8),('TextureBudget','Y','TEXTURE BUDGET BOOST',9)]:
    var='mbVR'+key
    checks+=[f'{var}=p.GetBool("SOMA_VR_Video","{key}",false)',f'p.SetBool("SOMA_VR_Video","{key}",{var})',f'cScript_RunGlobalFunc("VRCOMFORT","{cls}",{var} ? "1" : "0")',f'HPL3VR_Toggle("{label}",{row},{var})']
for c in checks: assert c in s,c
assert 275+9*38+38<=260+430 # HANDS AND HAPTICS: BACK on row 9
assert 275+10*38+38<=260+450 # VIDEO: BACK on row 10
h=(R/'runtime/script/modules/PlayerHandsHandler.hps').read_text()
for c in ['cScript_RunGlobalFunc("VRLADDER", "", bLadder ? "1" : "0")','bool bLadderHands = bLadder && cScript_RunGlobalFunc("VRLADDER", "", "Q");',
          '(bLadder && !bLadderHands)','cScript_RunGlobalFunc("VRLADDER", "", "0")','HPL3VR_UpdateBody(afTimeStep);','HPL3VR_DestroyBody(apMap);',
          'cScript_RunGlobalFunc("MenuHandler", "cScrMenuHandler", "HPL3VR_GetShowBody")','pBody.SetCollideCharacter(false); pBody.SetCollide(false);',
          'eRenderableFlag_VisibleInReflection, false','pEnt.GetName()!="VR_PlayerBody"']:
    assert c in h,c
p=(R/'source/controller_policy_u.inc').read_text(); assert '__atomic_load_n(&g_s26djFingerTracking' in p
p=(R/'source/skeletal_q.inc').read_text(); assert '__atomic_store_n(&g_s26qRootInput[h][f],0ULL' in p
assert 's26dj_set_finger_tracking' in (R/'source/s26n.c').read_text()
print('PASS: menu load/save/publish wiring (incl. S26ED video/hands rows, ladder publish and body hooks), toggle/bindings/back row separation and panel bounds; tracking gate and authored root pose source contracts. Static checks, not script-VM execution.')


