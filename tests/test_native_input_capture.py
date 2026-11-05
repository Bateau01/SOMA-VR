"""Isolated real-OpenXR render test. Native menu methods drive transitions;
fixture map/start avoids story setup. No simulated headset/controller poses."""
from pathlib import Path
import subprocess,sys,ctypes,time,json,uuid,hashlib,math
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert '--movement-replay' not in sys.argv or '--runtime-transitions' in sys.argv, 'Held replay requires the full-duration runtime fixture'
assert '--runtime-short' not in sys.argv or '--runtime-transitions' in sys.argv,'runtime-short requires runtime-transitions; otherwise the selector is not exercised'
store65='--store-cpu65' in sys.argv
payload=R/('build/store-cpu65' if store65 else 'build/cpu73' if '--movement-replay' in sys.argv else 'build/native-runtime' if '--production-payload' in sys.argv else 'build/smaa-test')
if store65:
 assert '--production-payload' in sys.argv and '--movement-replay' not in sys.argv
 raw=json.loads((payload/'result.json').read_text())
 assert raw['arguments']['cpu_optimisations']
 import shutil
 shutil.copyfile(payload/'hpl3vr-store.dll',payload/'hpl3vr.dll')
 (payload/'build-receipt.json').write_text(json.dumps({'dll_sha256':raw['sha256'],'source_hashes':raw['source_hashes'],'arguments':dict(raw['options'],production=True),'store_port':True}))
assert '--production-payload' not in sys.argv or '--runtime-transitions' in sys.argv, 'Production requires runtime selector fixture'
receipt=json.loads((payload/'build-receipt.json').read_text())
assert bool(receipt['arguments'].get('production')) == ('--production-payload' in sys.argv)
assert receipt['dll_sha256']==hashlib.sha256((payload/'hpl3vr.dll').read_bytes()).hexdigest(),'Candidate differs from successful build receipt'
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in receipt['source_hashes'].items()),'Candidate is stale after source edits; rebuild before testing'
store_exe=Path('C:/Program Files/GOG Galaxy/Games/SOMA/Soma.exe' if '--gog' in sys.argv else 'C:/Program Files/Epic Games/SOMA/Soma.exe')
exe_hash=hashlib.sha256((store_exe if store65 else G/'Soma.exe').read_bytes()).hexdigest()
assert exe_hash==('395cd54830c8e66e22166e71ac6fe95fd3bb5433b898737836744a6d178a0a6a' if store65 else '7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113'),'Unverified executable for native renderer probes'
if receipt['arguments'].get('parallel_sse') or receipt['arguments'].get('paired_sse'):assert hashlib.sha256((G/'Newton.dll').read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74','Unverified Newton for SSE job prototype'
assert not subprocess.run(['powershell','-NoProfile','-Command','Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True).stdout.strip()
input_mode=int(sys.argv[sys.argv.index('--input-mode')+1]);assert input_mode in (0,1,2)
nonce=uuid.uuid4().hex[:8];out=R/'audit/delta-integration'/nonce;out.mkdir(parents=True);saved={};proc=None
start_area=sys.argv[sys.argv.index('--start-area')+1] if '--start-area' in sys.argv else 'PlayerStartArea_1'
assert start_area in ('PlayerStartArea_1','StartZeppLanding','PlayerStartArea_Airlock2','StartChair','EndOfSimulation'), 'Use an existing native start area, not an implicit fallback'
fixed_yaw=float(sys.argv[sys.argv.index('--fixed-yaw')+1]) if '--fixed-yaw' in sys.argv else None
assert fixed_yaw is None or (math.isfinite(fixed_yaw) and abs(fixed_yaw)<7)
(out/'identity.json').write_text(json.dumps({'exe_sha256':exe_hash,'dll_sha256':hashlib.sha256((payload/'hpl3vr.dll').read_bytes()).hexdigest(),'start_area':start_area,'fixed_script_camera_yaw_radians':fixed_yaw,'scenario':('Apartment kitchen mechanisms fixture' if '--apartment-mechanisms' in sys.argv else 'Phi fixture' if '--phi' in sys.argv else ('Theta indoor physics fixture' if '--theta-physics' in sys.argv else 'Theta DUNBAT camera fixture' if '--theta-camera' in sys.argv else 'Delta fixture'))+', actual OpenXR; no authored progression; optional scripted body/camera yaw, live headset pose; not a performance benchmark'},indent=2))

(out/'build-receipt.json').write_text(json.dumps(receipt,indent=2))
(out/'test-command.json').write_text(json.dumps(sys.argv,indent=2))

def put(p,b):
 if p not in saved:
  saved[p]=p.read_bytes() if p.exists() else None
  backup=out/'restore';backup.mkdir(exist_ok=True)
  if saved[p] is not None:(backup/str(len(saved)-1)).write_bytes(saved[p])
  (out/'restore-map.json').write_text(json.dumps([{'path':str(k),'backup':str(i) if v is not None else None,'sha256':hashlib.sha256(v).hexdigest() if v is not None else None} for i,(k,v) in enumerate(saved.items())],indent=2))
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 if store65:put(G/'Soma.exe',store_exe.read_bytes())
 if receipt['arguments'].get('gpu_native'):
  from cpu58_shader_fixture import patch
  cache=G/'_shadersource'
  sx,sb,changed=patch((cache/'shadercache.xml').read_bytes(),(cache/'shadersource.hpss').read_bytes())
  put(cache/'shadercache.xml',sx);put(cache/'shadersource.hpss',sb)
  (out/'gpu-shader-fixture.json').write_text(json.dumps({'changed':changed,'scope':'private GPU object-selection vertex variants'}))
 if '--movement-replay' in sys.argv:
  put(G/'cpu6_movement.bin',b'');put(G/'cpu14_events.bin',b'')
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 if '--native-icon-audit' in sys.argv:
  p=G/'script/player/Player.hps';s=p.read_text()
  s=s.replace('bool NI_DrawIcon(cGuiGfxElement@ icon)','uint niIconAuditNext=0;\n    bool NI_DrawIcon(cGuiGfxElement@ icon)',1)
  s=s.replace('cGuiSet@ set=cGui_GetSetFromName("VR_NativeIcons");if(set is null)return true;', 'cGuiSet@ set=cGui_GetSetFromName("VR_NativeIcons");if(set is null)return true;\n        if(cSystem_GetApplicationTime()>niIconAuditNext){niIconAuditNext=cSystem_GetApplicationTime()+2000;LogNewLine("NI_ICON_DRAW focus="+mbNIIconFocus+" state="+meCrossHairState);}',1)
  if '--native-icon-large-fixture' in sys.argv:s=s.replace('distance*0.07f','distance*0.35f')
  put(p,s)
 # Replace a leftover old fixture script only inside this run; restore afterward.
 for p in (R/'runtime/maps').rglob('*.hps'):put(G/'maps'/p.relative_to(R/'runtime/maps'),p.read_bytes())
 put(G/'hpl3vr.dll',(payload/'hpl3vr.dll').read_bytes())
 if '--physics-rate' in sys.argv:
  rate=int(sys.argv[sys.argv.index('--physics-rate')+1]);assert rate in (60,120);put(G/'hpl3vr_simulation_rate.txt',str(rate)+'\n')
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
 menu=menu.replace('void GuiMainMenuSelection()','bool iuStarted=false;uint iuBoot=0;\n void GuiMainMenuSelection()',1)
 needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n mbVRGuideDismissed=true;',1)
 probe='''
 uint iuStart=0;int iuPhase=-1;
 void IUStart(){iuStart=cSystem_GetApplicationTime();LogNewLine("IU_MAP_ENTER");}
 void IUTick(){
  if(iuStart==0)return;uint elapsed=cSystem_GetApplicationTime()-iuStart;
  int phase=int(elapsed/5000);if(phase>1){LogNewLine("IU_VR_DONE");cEngine_Exit();return;}
  if(phase==iuPhase)return;iuPhase=phase;
  bool aaEnabled=phase==2 || phase==3 || phase==4 || phase==5 || phase==6 || phase==8;
  HPL3VR_SetAA(aaEnabled ? 2 : (phase==1 ? 1 : 0));
  mbVRDynamicFoveation=phase==3;
  

  HPL3VR_PublishComfort();
  cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);
  if(phase==4){cScript_RunGlobalFunc("VRLIFE","","P");SetMenuActive(true);mCurrentGroup=eMainMenuGroup_Options_Video_Display;msSelectedVideoDisplayButton="AA";}
  if(phase==5){mCurrentGroup=eMainMenuGroup_VRSettings;mbVRComfortOpen=true;mlVRComfortCategory=2;mvVRSettingsPages[2]=0;msVRSettingsSelected="ANTI-ALIASING";}
  if(phase==6){mbVRComfortOpen=false;cScript_RunGlobalFunc("VRLIFE","","R");SetMenuActive(false);}
  if(phase==8){cScript_RunGlobalFunc("VRLIFE","","P");SetMenuActive(true);mCurrentGroup=eMainMenuGroup_VRSettings;mbVRComfortOpen=true;mlVRComfortCategory=2;mvVRSettingsPages[2]=1;msVRSettingsSelected="VIGNETTE";}
  LogNewLine("IU_STAGE|"+phase+"|SMAA="+mbVRSMAA+"|DFR="+mbVRDynamicFoveation+"|runtime="+gbHPL3VRRuntimeActive);
 }
 '''
 if '--stereo-comparison' in sys.argv:
  probe=probe.replace('phase>1','phase>3').replace('elapsed/5000','elapsed/7000').replace('HPL3VR_SetAA(aaEnabled ? 2 : (phase==1 ? 1 : 0));','HPL3VR_SetAA(0);').replace('mbVRDynamicFoveation=phase==3;','mbVRDynamicFoveation=false;')
 if '--stereo-warmup' in sys.argv:
  assert '--stereo-comparison' in sys.argv and '--runtime-transitions' not in sys.argv
  probe=probe.replace('int phase=int(elapsed/7000);if(phase>3)', 'if(elapsed<7000)return;int phase=int((elapsed-7000)/7000);if(phase>3)')
 if '--runtime-transitions' in sys.argv:
  probe='''
 uint iuStart=0;int iuPhase=-1;
 void IUStart(){iuStart=cSystem_GetApplicationTime();LogNewLine("IU_MAP_ENTER");}
 void IUTick(){
  if(iuStart==0)return;int phase=int((cSystem_GetApplicationTime()-iuStart)/5000);
  if(phase>7){LogNewLine("IU_VR_DONE");cEngine_Exit();return;}
  if(phase==iuPhase)return;iuPhase=phase;
  int iuNativePhase=0;
  HPL3VR_SetAA(phase>=5 && phase<=6?2:0);mbVRDynamicFoveation=phase==3;
  HPL3VR_PublishComfort();cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);
  if(phase==2 || phase==6){cScript_RunGlobalFunc("VRLIFE","","P");SetMenuActive(true);mCurrentGroup=eMainMenuGroup_VRSettings;mbVRComfortOpen=true;mlVRComfortCategory=2;mvVRSettingsPages[2]=1;msVRSettingsSelected="DESKTOP MIRROR";}
  if(phase==3 || phase==7){mbVRComfortOpen=false;cScript_RunGlobalFunc("VRLIFE","","R");SetMenuActive(false);}
  LogNewLine("IU_STAGE|"+phase+"|NATIVE_PHASE="+iuNativePhase+"|SMAA="+mbVRSMAA+"|DFR="+mbVRDynamicFoveation+"|runtime="+gbHPL3VRRuntimeActive);
 }
 '''
 if '--gamepad-icons' in sys.argv:
  assert '--runtime-transitions' in sys.argv
  probe=probe.replace('LogNewLine("IU_STAGE|"+phase', 'NIGlyphAudit(phase);LogNewLine("IU_STAGE|"+phase')
  probe+=r'''
 void NIGlyphAudit(int phase){
  cLuxInputHandler@ input=cLux_GetInputHandler();
  tString oldPreset=cLux_GetKeyConfig().GetString("GamepadMapping","Preset","Right");
  bool equal=true;
  for(int preset=0;preset<2;preset++){
   tString p=preset==0?"Right":"Left";
   input.SetGamepadMapping("X360 Controller",p);
   int count=input.GetGamepadMappingActionNum();
   array<tString> expected;
   for(int i=0;i<count;i++){int action;tString bind;bool analog;input.GetGamepadMappingAction(i,action,bind,analog);expected.push_back(""+action+":"+bind+":"+analog);}
   input.SetGamepadMapping("PS4 Controller",p);
   equal=equal && count==input.GetGamepadMappingActionNum() && count>20;
   for(int i=0;i<count;i++){int action;tString bind;bool analog;input.GetGamepadMappingAction(i,action,bind,analog);equal=equal && expected[i]==(""+action+":"+bind+":"+analog);}
  }
  int style=phase%3;
  cLux_GetUserConfig().SetInt("SOMA_VR_Comfort","GamepadIcons",style);
  NI_ApplyGamepadIcons();
  tString prefix,icon;
  input.FetchGamepadInputLayoutString("Gamepad.0.Button.0",prefix,icon);
  LogNewLine("NI_GLYPH phase="+phase+" style="+style+" prefix="+prefix+" icon="+icon+" presetsEqual="+equal);
  if(phase==2 || phase==6){mbVRComfortOpen=false;mCurrentGroup=eMainMenuGroup_Options_Input_GamepadMapping;}
 }
 '''
 if '--movement-replay' in sys.argv:
  probe=probe.replace('phase>7','phase>13').replace('HPL3VR_SetAA(phase>=5 && phase<=6?2:0);mbVRDynamicFoveation=phase==3;','HPL3VR_SetAA(0);mbVRDynamicFoveation=false;').replace('if(phase==2 || phase==6)','if(false)').replace('if(phase==3 || phase==7)','if(false)').replace('cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);','cScript_RunGlobalFunc("VRCOMFORT","IUTEST","-1");')
 if '--production-short-exit' in sys.argv:
  assert '--production-payload' in sys.argv and '--movement-replay' not in sys.argv
  assert 'phase>7' in probe
  probe=probe.replace('phase>7','phase>2').replace('if(phase==2 || phase==6)','if(false)').replace('if(phase==3 || phase==7)','if(false)')
 if '--long-replay' in sys.argv:
  assert '--movement-replay' in sys.argv and '--delta-route' not in sys.argv
  probe=probe.replace('phase>13','phase>23')
 if '--delta-route' in sys.argv:
  assert '--movement-replay' in sys.argv and '--theta-camera' not in sys.argv and '--theta-physics' not in sys.argv and '--phi' not in sys.argv and '--apartment-mechanisms' not in sys.argv
  probe=probe.replace('phase>13','phase>41')
 if '--input-trace-short' in sys.argv:
  assert '--delta-route' in sys.argv and '--scripted-route-transition' not in sys.argv
  assert receipt['arguments'].get('route_input_trace')
  probe=probe.replace('phase>41','phase>16')
 if '--scripted-arms-cpu67' in sys.argv:
  from cpu67_arm_fixture import prepare
  probe,arms=prepare((G/'script/modules/PlayerHandsHandler.hps').read_text(encoding='utf-8-sig'))
  put(G/'script/modules/PlayerHandsHandler.hps',arms)
 if '--scripted-arms-cpu66' in sys.argv:
  from cpu66_arm_fixture import prepare
  probe,arms=prepare((G/'script/modules/PlayerHandsHandler.hps').read_text(encoding='utf-8-sig'))
  put(G/'script/modules/PlayerHandsHandler.hps',arms)
 if '--native-menu-exit' in sys.argv:
  assert '--runtime-transitions' in sys.argv
  # Completion is persistent across MenuHandler recreation; evaluated below
  # before the fixture's startup action, not only while drawing one GUI group.
  # Exercise the native accepted Exit-to-menu action, then application exit.
  # The confirmation click is automated, not a physical-controller/UI test.
  probe=probe.replace('cEngine_Exit();return;','IUFinish();return;')
  probe=probe.replace('void IUTick(){','void IUTick(){if(iuFinishing){if(mbMainMenuActive&&!Map_IsChanging()){if(iuTitleAt==0){iuTitleAt=cSystem_GetApplicationTime();LogNewLine("CPU29_NATIVE_TITLE_READY");}if(cSystem_GetApplicationTime()-iuTitleAt>2000){LogNewLine("CPU29_NATIVE_APP_EXIT");cLux_Exit();}}return;}',1)
  probe+='''
 bool iuFinishing=false;uint iuTitleAt=0;
 void IUFinish(){
  if(iuFinishing)return;iuFinishing=true;mbVRComfortOpen=false;
  cLux_GetUserConfig().SetBool("CPU29_Test","Finished",true);
  SetMenuActive(true);mCurrentGroup=eMainMenuGroup_Main;mbSaveAndExit=false;
  LogNewLine("CPU29_NATIVE_MENU_EXIT_REQUEST");
  LoadScreen_SetUseSmallIcon(false);cLux_GetGuiHandler().SetGameHudInputFocus(false);
  ImGui_AddTimer("ExitToMainMenu",mfFadeLength);Map_FadeOut(mfFadeLength);
  Music_StopAll(mfFadeLength);Sound_Stop("MenuBGNoise",mfFadeLength);
 }
 '''
 if '--movement-visual' in sys.argv:
  assert '--movement-replay' in sys.argv
  probe=probe.replace('cScript_RunGlobalFunc("VRCOMFORT","IUTEST","-1");','cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);')
 if '--reload-streaming' in sys.argv:
  assert '--runtime-transitions' in sys.argv and '--theta-camera' not in sys.argv
  probe=probe.replace('uint iuStart=0;int iuPhase=-1;', 'uint iuStart=0;int iuPhase=-1;bool iuReloaded=false;')
  probe=probe.replace('void IUStart(){iuStart=', 'void IUStart(){iuPhase=-1;iuStart=')
  probe=probe.replace('if(phase>7){LogNewLine("IU_VR_DONE");', 'if(phase>7 && !iuReloaded){iuReloaded=true;iuStart=0;LogNewLine("IU_STREAM_RELOAD");Map_ChangeMap("02_03_delta.hpm","PlayerStartArea_1","","");return;}if(phase>7){LogNewLine("IU_VR_DONE");')
 if '--native-map-transition' in sys.argv:
  assert '--theta-camera' in sys.argv and input_mode in (1,2) and '--load-save' not in sys.argv
  probe=probe.replace('uint iuStart=0;int iuPhase=-1;','uint iuStart=0;int iuPhase=-1;bool niChangedMap=false;')
  probe=probe.replace('void IUStart(){iuStart=', 'void IUStart(){iuPhase=-1;iuStart=')
  probe=probe.replace('if(phase>7){LogNewLine("IU_VR_DONE");', 'if(phase>7&&!niChangedMap&&Map_IsPreloadCompleted()){niChangedMap=true;iuStart=0;LogNewLine("NI_THETA_TRANSITION");Map_ChangeMap("02_06_theta_tunnels.hpm","PlayerStartArea_1","","");return;}if(niChangedMap&&phase>7){LogNewLine("IU_VR_DONE");')
  probe=probe.replace('if(phase==iuPhase)return;iuPhase=phase;','if(phase==iuPhase)return;iuPhase=phase;if(phase==0&&!niChangedMap){LogNewLine("NI_PRELOAD_TUNNELS");Map_Preload("02_06_theta_tunnels.hpm");}',1)
 if '--xml-lifetime' in sys.argv:
  assert '--xml-observer' in sys.argv and '--theta-physics' in sys.argv and '--reload-streaming' not in sys.argv
  assert receipt['arguments'].get('xml_lifetime'),'Wrong lifetime payload'
  probe=probe.replace('uint iuStart=0;int iuPhase=-1;','uint iuStart=0;int iuPhase=-1;bool iuReloaded=false;')
  probe=probe.replace('void IUStart(){iuStart=','void IUStart(){iuPhase=-1;iuStart=')
  needle='if(phase>23){LogNewLine("IU_VR_DONE");'
  assert probe.count(needle)==1
  transition_phase=int(sys.argv[sys.argv.index('--lifetime-transition-phase')+1]) if '--lifetime-transition-phase' in sys.argv else 1
  assert 1<=transition_phase<=20
  transition_ready='&&Map_IsPreloadCompleted()' if '--lifetime-native-route' in sys.argv else ''
  probe=probe.replace(needle,f'if(phase>={transition_phase}&&!iuReloaded{transition_ready}){{iuReloaded=true;iuStart=0;LogNewLine("CPU20_NATIVE_CHANGE_REQUEST");Map_ChangeMap("02_03_delta.hpm","PlayerStartArea_1","","");return;}}'+needle,1)
 if '--lifetime-native-route' in sys.argv:
  assert '--xml-lifetime' in sys.argv
  probe=probe.replace('Map_ChangeMap("02_03_delta.hpm","PlayerStartArea_1","","")','Map_ChangeMap("02_06_theta_tunnels.hpm","PlayerStartArea_1","","")')
 if '--lifetime-native-route' in sys.argv:
  probe=probe.replace('if(phase>23){LogNewLine("IU_VR_DONE");','if((iuReloaded&&phase>5)||phase>23){LogNewLine("IU_VR_DONE");',1)
 if '--xml-exit-hold' in sys.argv or '--xml-short-exit' in sys.argv:
  assert '--xml-lifetime' not in sys.argv
  if '--xml-exit-hold' in sys.argv:assert receipt['arguments'].get('xml_exit_hold')
  assert 'if(phase>23)' in probe;probe=probe.replace('if(phase>23)','if(phase>2)',1)
 if '--settle-ms' in sys.argv:
  delay=int(sys.argv[sys.argv.index('--settle-ms')+1]);assert 0<=delay<=20000
  probe=probe.replace('if(iuStart==0)return;',f'if(iuStart==0)return;if(cSystem_GetApplicationTime()-iuStart<{delay})return;')
  probe=probe.replace('int phase=int((cSystem_GetApplicationTime()-iuStart)/5000);',f'int phase=int((cSystem_GetApplicationTime()-iuStart-{delay})/5000);')
  probe=probe.replace('uint elapsed=cSystem_GetApplicationTime()-iuStart;',f'uint elapsed=cSystem_GetApplicationTime()-iuStart-{delay};')
 if '--dfr-always' in sys.argv:
  probe=probe.replace('mbVRDynamicFoveation=phase==3;','mbVRDynamicFoveation=true;').replace('mbVRDynamicFoveation=false;','mbVRDynamicFoveation=true;')
 if '--profile-only' in sys.argv:probe=probe.replace('cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);','cScript_RunGlobalFunc("VRCOMFORT","IUTEST","-1");')
 if '--runtime-short' in sys.argv:probe=probe.replace('phase>7','phase>1')
 if '--no-hints' in sys.argv:probe=probe.replace('HPL3VR_PublishComfort();','cLux_GetUserConfig().SetInt("SOMA_VR_Hints","Mode",2);HPL3VR_PublishComfort();')
 if '--native-ui-window' in sys.argv:
  probe=probe.replace('/5000)', '/15000)').replace('if(phase==2 || phase==6)', 'if(false)').replace('if(phase==3 || phase==7)', 'if(false)')
  probe=probe.replace('  int iuNativePhase=0;', '  int iuNativePhase=0; cVector3f niPos=cLux_GetPlayer().GetCharacterBody().GetFeetPosition(); LogNewLine("NI_UI_POSITION "+niPos.x+","+niPos.y+","+niPos.z+" paused="+cLux_GetGamePaused());')
 if '--gui-widget-regression' in sys.argv:
  widget=r"""
 void IUWidgetProbe(){
 cGuiSet@ set=cGui_CreateSet("CPU16Probe",null);set.SetVirtualSize(cVector2f(512),-1000,1000,cVector2f(0));
 cImGui@ gui=cGui_CreateImGui("CPU16Probe",set);cImGuiButtonData data;
 cImGuiGfx cursor("gui/gui_def_pointer_normal.tga",eImGuiGfx_Texture);
 gui.SetDefaultMouse(cursor);
 data.mbUseBackgroundGfx=false;data.mbUseInFocusGfx=false;data.mbUseTriggeredGfx=false;
 data.mFont.SetFile("sansation_medium.fnt");data.mFont.mvSize=cVector2f(16);
 for(int mode=0;mode<2;mode++){
  if(mode==1){cScript_RunGlobalFunc("VRGUI","","R");gui.SendMouseVirtualPosition(cVector2f(0),cVector2f(0));cScript_RunGlobalFunc("VRGUI","","E");}
  gui.ClearStates();int accepted=0;int otherCount=0;
  for(int frame=0;frame<5;frame++){
   gui.Begin(1.0f/60.0f);gui.SetShowMouse(true);cVector2f pos(110,110);
   gui.SendMouseVirtualPosition(pos,cVector2f(1));gui.SendMouseVirtualPosition(pos,cVector2f(1));
   gui.SendAction(eImGuiAction_MouseLeft,frame==1||frame==2,frame==1);
   if(gui.DoButton("ONE",tWString(""),data,cVector3f(100,100,1),cVector2f(80,40)))accepted++;
   if(gui.DoButton("TWO",tWString(""),data,cVector3f(220,100,1),cVector2f(80,40)))otherCount++;
   if(frame==3)gui.DoMouse(cursor,cVector3f(0),cVector2f(24));
   gui.End();
  }
  LogNewLine("CPU16_WIDGET|mode="+mode+"|accepted="+accepted+"|other="+otherCount);
 }
 // Keep the synthetic registered GUI alive until world/process teardown; do not
 // leave a destroyed pointer in the production registration inventory.
 }
 """
  probe=widget+probe.replace('if(phase==iuPhase)return;iuPhase=phase;', 'if(phase==iuPhase)return;iuPhase=phase;if(phase==0)IUWidgetProbe();',1)
 menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)',probe+'\n    void HPL3VR_UpdateComfort(float dt)',1)
 menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)\n    {','    void HPL3VR_UpdateComfort(float dt)\n    {\n mbVRGuideDismissed=true;if(iuBoot==0)iuBoot=cSystem_GetApplicationTime();if(!iuStarted && mbMainMenuActive && cSystem_GetApplicationTime()-iuBoot>7000){LogNewLine("NI_TEST_START group="+mCurrentGroup);iuStarted=true;ClickNewGame();}\n IUTick();',1)
 if '--native-menu-exit' in sys.argv:
  menu=menu.replace('mbVRGuideDismissed=true;if(iuBoot==0)', 'if(cLux_GetUserConfig().GetBool("CPU29_Test","Finished",false) && mbMainMenuActive && !Map_IsChanging()){LogNewLine("CPU29_NATIVE_APP_EXIT");cLux_Exit();return;}mbVRGuideDismissed=true;if(iuBoot==0)',1)
 if '--saved-on' in sys.argv: menu=menu.replace('elapsed/5000','elapsed/4000').replace('mbVRSMAA=phase==2','mbVRSMAA=phase==0 || phase==2')
 load_save=Path(sys.argv[sys.argv.index('--load-save')+1]) if '--load-save' in sys.argv else None
 if load_save:
  assert load_save.is_file() and load_save.suffix=='.sav'
  expected_save_map='05-01-phi-inside' if '--phi' in sys.argv else '02-05-theta-inside' if '--theta-camera' in sys.argv else '02-03-delta'
  assert expected_save_map in load_save.name, 'Save must match the instrumented map'
  assert 'iuStarted=true;ClickNewGame();' in menu
  menu=menu.replace('iuStarted=true;ClickNewGame();','iuStarted=true;StartSavedGameLoad(tWString("'+load_save.name+'"));',1)
  (out/'save-identity.json').write_text(json.dumps({'path':str(load_save),'sha256':hashlib.sha256(load_save.read_bytes()).hexdigest(),'scope':'Native saved state; OnEnter starts observation, story callbacks retained.'},indent=2))
 if load_save:
  # Dismiss the native recap at its existing key-consumption point. This is a
  # synthetic key result, not hardware-input proof or a direct final-state set.
  menu=menu.replace('tString sKeyPress = cLux_GetInputHandler().GetLatestKeyPressed();','tString sKeyPress = cLux_GetInputHandler().GetLatestKeyPressed(); if(mbLoading_LoadScreenHidden){sKeyPress="NI_TEST_CONTINUE";LogNewLine("NI_RECAP_DISMISS");}')
  menu=menu.replace('cLux_GetSaveHandler().StartLoadedGame();','cLux_GetSaveHandler().StartLoadedGame(); cScript_RunGlobalFunc("MenuHandler","","NILoadStarted");')
  menu=menu.replace(' uint iuStart=0;int iuPhase=-1;',' bool niLoadStarted=false; void NILoadStarted(){niLoadStarted=true;} uint iuStart=0;int iuPhase=-1;')
  saved_map=expected_save_map.replace('-','_')
  menu=menu.replace(' IUTick();',' if(niLoadStarted && iuStart==0 && cLux_GetCurrentMap() !is null && cLux_GetCurrentMap().GetName()=="'+saved_map+'" && !cLux_IsLoadingScreenVisible()){LogNewLine("NI_SAVE_READY '+saved_map+'");IUStart();} IUTick();',1)
 if '--inventory-audit' in sys.argv:
  assert load_save and input_mode in (1,2)
  menu=menu.replace('LogNewLine("IU_STAGE|"+phase', 'cScript_RunGlobalFunc("PlayerToolHandler","cScrPlayerToolHandler","NIInventoryAudit");LogNewLine("IU_STAGE|"+phase')
  tool=(G/'script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig')
  probe_inventory=r'''[nosave] int niInventoryAuditPhase=0;
  void NIInventoryAudit(){
   if((niInventoryAuditPhase==1 || niInventoryAuditPhase==3) && CanPickOrUseTool()){int ix=niInventoryAuditPhase==1?0:1;if(ix<int(mvInventory.length()))LogNewLine("NI_EQUIP index="+ix+" accepted="+EquipTool(ix,""));}
   if(niInventoryAuditPhase==4)UnequipCurrentTool(false);
   niInventoryAuditPhase++;
   for(int h=0;h<2;h++){tString name=h==0?"vrhand_L":"vrhand_R";iPhysicsBody@ body=cLux_GetCurrentMap().GetPhysicsWorld().GetBody(name);LogNewLine("NI_SAVED_PROXY "+name+" present="+(body !is null)+" active="+(body !is null && body.IsActive())+" collide="+(body !is null && body.GetCollide())+" saved="+(body !is null && body.GetScriptableIsSaved()));}
   LogNewLine("NI_INVENTORY count="+mvInventory.length()+" current="+mlCurrentToolIndex+" prepared="+mbNIInventoryPrepared);
   for(uint i=0;i<mvInventory.length();i++){
    cToolData@ tool=mvInventory[i];iLuxEntity@ hud=cLux_ID_Entity(tool.m_idHudObject);

    LogNewLine("NI_INVENTORY_ITEM "+tool.msPickedEntityName+" file="+tool.msHudObjFile+" eligible="+tool.mbVRShoulderEligible+" carrier="+tool.msVRPhysicalCarrierName+" hud="+(hud is null ? "MISSING" : hud.GetName()));
   }
  }
  '''
  if '--missing-owner' in sys.argv:
   probe_inventory=probe_inventory.replace('  void NIInventoryAudit(){','  void NIInventoryAudit(){\n    if(niInventoryAuditPhase==0){cToolData missing;missing.m_idHudObject=tID_Invalid;missing.msPickedEntityName="NI_Missing";missing.mbVRShoulderEligible=true;mvInventory.insertLast(missing);mbNIInventoryPrepared=false;}\n    if(niInventoryAuditPhase==4){int before=mlCurrentToolIndex;bool ok=EquipTool(2,"");bool named=EquipTool("NI_Missing","");LogNewLine("NI_MISSING_NAMED accepted="+named+" preserved="+(before==mlCurrentToolIndex));LogNewLine("NI_MISSING_REJECT accepted="+ok+" preserved="+(before==mlCurrentToolIndex));}\n    if(niInventoryAuditPhase==7){LogNewLine("NI_RETRY attempts="+mlNIInventoryAttempts);mvInventory.removeAt(2);}\n')
  if '--native-chip-use' in sys.argv:
   assert '--missing-owner' not in sys.argv
   probe_inventory=probe_inventory.replace('if(niInventoryAuditPhase==4)UnequipCurrentTool(false);','if(niInventoryAuditPhase==4)niChipTesting=true;')
   probe_inventory+=r'''
  [nosave] bool niChipTesting=false;[nosave] bool niChipUsed=false;[nosave] int niChipAngle=0;[nosave] float niChipTimer=0;
  void NIChipTick(float dt){
   if(!niChipTesting || niChipUsed)return;niChipTimer-=dt;if(niChipTimer>0)return;niChipTimer=0.6f;
   LogNewLine("NI_CHIP_FOCUS target="+mPickBasics.msFocusedEntityName+" permitted="+mbCanInteract);
   if(mbCanInteract && (mPickBasics.msFocusedEntityName=="CatherineSlotInteract" || mPickBasics.msFocusedEntityName=="CathTool" || mPickBasics.msFocusedEntityName=="ZeppelinCathTerminal")){
    niChipUsed=true;OnAction(eAction_Interact,true);LogNewLine("NI_CHIP_USE_DISPATCH");return;
   }
   if(niChipAngle>=16)return;
   iLuxEntity@ target=cLux_GetCurrentMap().GetEntityByName("CatherineSlotInteract",eLuxEntityType_LastEnum,"");if(target is null)return;
   cVector3f pos=target.GetPosition();float angle=float(niChipAngle++)*0.392699f;
   cLux_GetPlayer().GetCharacterBody().SetFeetPosition(pos+cVector3f(cMath_Sin(angle)*0.8f,-1.1f,cMath_Cos(angle)*0.8f),false);
   cLux_GetPlayer().RotateCameraTowards(100,100,100,pos,false);
  }
'''
   tool=tool.replace('void Update(float afTimeStep)\n\t{','void Update(float afTimeStep)\n\t{\n NIChipTick(afTimeStep);',1)
   assert 'NIChipTick(afTimeStep)' in tool
  tool=tool.replace('    bool NI_PrepareInventory(float dt)',probe_inventory+'    bool NI_PrepareInventory(float dt)',1)
  # Observe the unchanged production global callback route, not a replacement.
  for name in ('_Global_OnEquip','_Global_UpdateLookEntities'):
   tool=tool.replace('cScript_RunGlobalFunc(pCurrentTool.msPickedEntityName, "", "'+name+'")', 'NIObserveCallback(pCurrentTool.msPickedEntityName, "'+name+'")')
  tool=tool.replace('cScript_RunGlobalFunc(msPreviousTool, "", "_Global_OnUnequip")','NIObserveCallback(msPreviousTool, "_Global_OnUnequip")')
  tool=tool.replace('    bool NI_PrepareInventory(float dt)','''    bool NIObserveCallback(const tString &in name,const tString &in callback){
    bool ok=cScript_RunGlobalFunc(name,"",callback);LogNewLine("NI_CALLBACK_EXECUTED "+name+" "+callback+" ok="+ok);return ok;
   }
    bool NI_PrepareInventory(float dt)''',1)
  put(G/'script/modules/PlayerToolHandler.hps',tool)
 if '--native-tool-scale' in sys.argv:
  hands=(G/'script/modules/PlayerHandsHandler.hps').read_text(encoding='utf-8-sig')
  hands=hands.replace('void PostUpdate(float afTimeStep)','[nosave] float niScaleLast=-1; void PostUpdate(float afTimeStep)',1)
  hands=hands.replace('cVector3f vCamRot(pCam.GetPitch()', 'if(fScale!=niScaleLast){niScaleLast=fScale;LogNewLine("NI_TOOL_SCALE value="+fScale+" custom="+mbUseCustomPosition+" attached="+mbCameraAttachActive); }\n\t\t\tcVector3f vCamRot(pCam.GetPitch()',1)
  put(G/'script/modules/PlayerHandsHandler.hps',hands)
 if '--save-mode-handoff' in sys.argv:
  assert '--inventory-audit' in sys.argv and input_mode in (1,2)
  menu=menu.replace('  int iuNativePhase=0;', '  int iuNativePhase=0;if(phase==2){LogNewLine("NI_HANDOFF_SAVE_REQUEST");cLux_GetSaveHandler().AutoSave(false,false);}')
 if '--motion-save-audit' in sys.argv:
  assert load_save and input_mode==0
  menu=menu.replace('  int iuNativePhase=0;', '  int iuNativePhase=0;cScript_RunGlobalFunc("PlayerToolHandler","","NIMotionSaveAudit");')
  tool=(G/'script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig')
  code=r'''void NIMotionSaveAudit(){
   LogNewLine("NI_MOTION_INVENTORY count="+mvInventory.length()+" current="+mlCurrentToolIndex+" reconciled="+mbVRShoulderReconciled);
   for(uint i=0;i<mvInventory.length();i++){
    cToolData@ t=mvInventory[i];iLuxEntity@ hud=cLux_ID_Entity(t.m_idHudObject);
    iLuxEntity@ carrier=cLux_GetCurrentMap().GetEntityByName(VR_GetPhysicalCarrierName(t),eLuxEntityType_LastEnum,"");
    LogNewLine("NI_MOTION_ITEM name="+t.msPickedEntityName+" stowed="+t.mbVRShoulderStowed+" hudActive="+(hud !is null && hud.IsActive())+" carrier="+(carrier !is null)+" carrierActive="+(carrier !is null && carrier.IsActive()));
   }
  }
'''
  tool=tool.replace('    bool NI_PrepareInventory(float dt)',code+'    bool NI_PrepareInventory(float dt)',1);put(G/'script/modules/PlayerToolHandler.hps',tool)
 if '--native-tool-acquisition' in sys.argv:
  assert '--native-acquisition' in sys.argv
  tool=(G/'script/modules/PlayerToolHandler.hps').read_text(encoding='utf-8-sig')
  tool=tool.replace('void CreateHudObject(cToolData@ aToolData)\n\t{','[nosave] int niFreshCreates=0; void NIFreshCheck(){LogNewLine("NI_FRESH count="+mvInventory.length()+" current="+mlCurrentToolIndex+" creates="+niFreshCreates); }\n\tvoid CreateHudObject(cToolData@ aToolData)\n\t{\n if(aToolData.msPickedEntityName=="NI_Cup")niFreshCreates++;',1)
  put(G/'script/modules/PlayerToolHandler.hps',tool)
 if '--native-handheld' in sys.argv:
  from native_handheld_fixture import prepare
  menu=prepare(G,put,menu,sys.argv[sys.argv.index('--native-handheld')+1])
 if '--native-animation-batch' in sys.argv:
  from native_animation_fixture import prepare
  batch=int(sys.argv[sys.argv.index('--native-animation-batch')+1]);family=sys.argv[sys.argv.index('--hand-family')+1]
  menu,animation_cases=prepare(R,G,put,menu,batch,family)
  (out/'animation-cases.json').write_text(json.dumps({'cases':animation_cases,'family':family,'scope':'authentic entity pickup and native animation/attachment playback; no authored map use callbacks'},indent=2))
 put(G/'script/modules/MenuHandler.hps',menu)
 # Preserve the native map class, Setup, GUI callbacks and helpers. Only the
 # story intro is skipped for this rendering fixture; this is not progression QA.
 map_name='00_01_apartment' if '--apartment-mechanisms' in sys.argv else '05_01_phi_inside' if '--phi' in sys.argv else ('02_05_theta_inside' if '--theta-camera' in sys.argv or '--theta-physics' in sys.argv else '02_03_delta')
 chapter='chapter00' if '--apartment-mechanisms' in sys.argv else 'chapter05' if '--phi' in sys.argv else 'chapter02'
 m=(R/f'runtime/maps/{chapter}/{map_name}/{map_name}.hps').read_text(encoding='utf-8-sig')
 if '--theta-physics' in sys.argv:
  assert ('--movement-replay' in sys.argv or '--production-short-exit' in sys.argv) and '--theta-camera' not in sys.argv
 if '--movement-replay' in sys.argv:
  marker='void OnEnter()';a=m.index('{',m.index(marker))+1
  m=m[:a]+'cMatrixf cpuPose=cMatrixf_Identity;cpuPose.SetTranslation(cVector3f(0,100,0));cLux_GetCurrentMap().CreateEntity("CPU6Cup","entities/urban/kitchen/mug_coffee/mug_coffee.ent",cpuPose,cVector3f(1));cLuxProp@ cpuProp=Map_GetProp("CPU6Cup");if(cpuProp !is null && cpuProp.GetMainBody() !is null){LogNewLine("CPU12_CREATED_BODY "+cpuProp.GetMainBody().GetName());cpuProp.GetMainBody().SetGravity(false);}else LogNewLine("CPU12_CREATE_FAILED");'+m[a:]
 if '--theta-physics' in sys.argv or '--theta-camera' in sys.argv:
  m=m.replace('cpuPose.SetTranslation(cVector3f(0,100,0))','cpuPose.SetTranslation(Player_GetFeetPosition()+cVector3f(0,3,0))')
 assert 'void OnStart()' in m and 'void OnEnter()' in m
 m=m.replace('void OnStart()', 'void IUOriginalOnStart()', 1)
 injection='void OnStart(){Player_SetActive(true);Player_SetHealth(100);Player_SetFallDamageActive(false);Player_ChangeStateToNormal();PlayerHands_SetHandModel_Human();}\n'
 if fixed_yaw is not None:
  injection+=f'void IUSetYaw(float dt){{cLux_GetPlayer().GetCharacterBody().SetYaw({fixed_yaw:.9f}f);cLux_GetPlayer().GetCamera().SetYaw({fixed_yaw:.9f}f);cLux_GetPlayer().GetCamera().SetPitch(0);}}\n'
  if '--movement-replay' in sys.argv:
   injection=injection.replace('Player_SetActive(true);','IUSetYaw(0);Player_SetActive(true);',1)
   if '--recovery-static-phase' in sys.argv:
    # Fault-injection setup only: hold the native camera heading until the
    # free-hand stall experiment ends. Later held movement remains ordinary.
    injection+='int iuRecoveryStart=-1; void IURecoveryHeading(){if(iuRecoveryStart<0)iuRecoveryStart=cSystem_GetApplicationTime();if(cSystem_GetApplicationTime()-iuRecoveryStart<20000)IUSetYaw(0); }\n'
    import re
    m,n=re.subn(r'(void Update\(float \w+\)\s*\{)',r'\1 IURecoveryHeading();',m,count=1)
    if not n:injection+='void Update(float dt){IURecoveryHeading(); }\n'

  else:
   import re
   m,n=re.subn(r'(void Update\(float \w+\)\s*\{)',r'\1 IUSetYaw(0);',m,count=1)
   if not n:injection+='void Update(float dt){IUSetYaw(dt); }\n'
  if '--yaw-sweep' in sys.argv:injection=injection.replace(f'{fixed_yaw:.9f}f',f'({fixed_yaw:.9f}f+0.35f*(float(cSystem_GetApplicationTime()%8000)<4000.0f ? float(cSystem_GetApplicationTime()%8000)/2000.0f-1.0f : 3.0f-float(cSystem_GetApplicationTime()%8000)/2000.0f))')
 if '--arm-playback' in sys.argv:injection+='void CPU66AnimationOver(const tString& in name){LogNewLine("CPU66_CALLBACK "+name); }\n'
 m=m.replace('void IUOriginalOnStart()',injection+'void IUOriginalOnStart()',1)
 import re
 m,n=re.subn(r'(void OnEnter\(\)\s*\{)',r'\1\n cScript_RunGlobalFunc("MenuHandler","","IUStart");',m,count=1);assert n==1
 if '--theta-camera' in sys.argv:
  assert '--runtime-transitions' in sys.argv, 'Auxiliary fixture needs runtime renderer transitions'
  # Rendering fixture: native Setup/camera/GUI callbacks retained; story startup
  # omitted and player positioned by script, not a progression/controller test.
  m=m.replace('cScript_RunGlobalFunc("MenuHandler","","IUStart");','cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(28.3f,1.5f,3.5f),false);cLux_GetPlayer().GetCamera().SetYaw(0);Map_AddTimer("IUCameraReady",2.0f,"IUCameraReady");',1)
  m=m.replace('void IUOriginalOnStart()', 'void IUCameraReady(const tString &in name){SetupDunbatCamera();StartDunbatCamera();Terminal_SetGuiActive("ControlRoomTerminal_8",true);cScript_RunGlobalFunc("MenuHandler","","IUStart");}\nvoid IUOriginalOnStart()',1)
  needle='void OnGuiDunbatCamera(const tString&in asEntityName, float afTimeStep)'
  assert needle in m
  m=m.replace(needle,'int iuAuxCalls=0;\n'+needle,1)
  a=m.index('{',m.index(needle))+1
  m=m[:a]+'if(iuAuxCalls++<4)LogNewLine("IU_NATIVE_DUNBAT_GUI");'+m[a:]
 if '--apartment-mechanisms' in sys.argv:
  m=m.replace('cpuPose.SetTranslation(cVector3f(0,100,0))','cpuPose.SetTranslation(cVector3f(-10,2.5f,7.5f))')
  assert '--movement-replay' in sys.argv and '--reload-streaming' not in sys.argv
  m=m.replace('cScript_RunGlobalFunc("MenuHandler","","IUStart");','cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-8.7f,0.05f,9.25f),false);LogNewLine("CPU12_KITCHEN near sink drawers and cupboard doors; story intro omitted");cScript_RunGlobalFunc("MenuHandler","","IUStart");',1)
 if '--delta-route' in sys.argv:
  assert 'void Update(' not in m
  route=(R/'tests/cpu18_route.hps').read_text()
  if '--vr-route-input' in sys.argv:
   assert receipt['arguments'].get('vr_route_input'),'VR route inputs missing from build'
   route=route.replace('body.SetYaw(yaw);cLux_GetPlayer().GetCamera().SetYaw(yaw);','')
   route=route.replace('body.Move(eCharDir_Forward,cMath_Vector3Dot(delta,body.GetForward())*0.65f);','')
   route=route.replace('body.Move(eCharDir_Right,cMath_Vector3Dot(delta,body.GetRight())*0.65f);','')
  if '--native-route-placement' in sys.argv:
   import xml.etree.ElementTree as ET,copy
   area_path=G/f'maps/{chapter}/{map_name}/{map_name}.hpm_Area'
   tree=ET.fromstring(area_path.read_bytes());objects=tree.find('.//Objects')
   template=tree.find(".//Area[@Name='delta_platform']");assert template is not None and objects is not None
   all_ids={x.get('ID') for x in tree.iter()};positions=['5.603922 131.5 24.711344','21.2501 130.376 49.167','4.25 131.25 68.75']
   for i,pos in enumerate(positions):
    uid=str(1900000000+i);assert uid not in all_ids
    area=copy.deepcopy(template);area.set('ID',uid);area.set('UID','16 9000 '+uid);area.set('Name','CPU53Route'+str(i));area.set('WorldPos',pos);objects.append(area)
   put(area_path,ET.tostring(tree,encoding='utf-8'))
   needle='body.SetFeetPosition(anchor,false);';assert route.count(needle)==1
   route=route.replace(needle,'Player_Teleport("CPU53Route"+region,false);')
  if '--scripted-route-transition' in sys.argv:
   assert '--native-route-placement' in sys.argv and '--vr-route-input' in sys.argv
   needle53='Player_Teleport("CPU53Route"+region,false);';assert route.count(needle53)==1
   route=route.replace(needle53,'cpu53RouteHandActive=PlayerHands_IsActive();PlayerHands_SetActive(false);Map_AddTimer("CPU53RouteMove",0.15f,"CPU53RouteMove");LogNewLine("CPU53_ROUTE_HIDE "+region);')
   route+='\n'+(R/'tests/cpu53_route_transition.hps').read_text()
  m=m.replace('void IUOriginalOnStart()',route+'\nvoid IUOriginalOnStart()',1)
 if '--native-map-transition' in sys.argv:
  dest=G/'maps/chapter02/02_06_theta_tunnels/02_06_theta_tunnels.hps'
  dm=dest.read_text(encoding='utf-8-sig')
  dm=dm.replace('void OnStart()', 'void OnStart(){Player_SetActive(true);Player_SetHealth(100);Player_SetFallDamageActive(false);Player_ChangeStateToNormal();}\nvoid NIOriginalStart()',1)
  dm,n=re.subn(r'(void OnEnter\(\)\s*\{)',r'\1 LogNewLine("NI_TUNNELS_ENTER");cScript_RunGlobalFunc("MenuHandler","","IUStart");',dm,count=1);assert n==1
  put(dest,dm)
 if '--xml-lifetime' in sys.argv:
  m,n=re.subn(r'(void OnLeave\(\)\s*\{)',r'\1 LogNewLine("CPU20_THETA_LEAVE");',m,count=1);assert n==1
  target_map='02_06_theta_tunnels' if '--lifetime-native-route' in sys.argv else '02_03_delta'
  dest=G/f'maps/chapter02/{target_map}/{target_map}.hps'
  dm=dest.read_text(encoding='utf-8-sig')
  assert 'void OnStart()' in dm and 'void OnEnter()' in dm
  dm=dm.replace('void OnStart()','void OnStart(){Player_SetActive(true);Player_SetHealth(100);Player_SetFallDamageActive(false);Player_ChangeStateToNormal();PlayerHands_SetHandModel_Human();}\nvoid CPU20OriginalStart()',1)
  dm,n=re.subn(r'(void OnEnter\(\)\s*\{)',r'\1 LogNewLine("CPU20_DELTA_ENTER");cScript_RunGlobalFunc("MenuHandler","","IUStart");',dm,count=1);assert n==1
  if '--lifetime-native-route' in sys.argv:dm=dm.replace('CPU20_DELTA_ENTER','CPU29_TUNNELS_ENTER')
  put(dest,dm)
 if '--native-acquisition' in sys.argv:
  assert input_mode in (1,2) and '--production-payload' not in sys.argv
  m=m.replace('cScript_RunGlobalFunc("MenuHandler","","IUStart");','cScript_RunGlobalFunc("MenuHandler","","IUStart");Map_AddTimer("NI_SPAWN",8.0f,"NIAcquire");',1)
  extra=r'''
 void NIAcquire(const tString &in name){
  if(name=="NI_SPAWN"){
   cCamera@ cam=cLux_GetPlayer().GetCamera();cMatrixf pose=cMatrixf_Identity;
   pose.SetTranslation(cam.GetPosition()+cam.GetForward()*0.75f);
   cLux_GetCurrentMap().CreateEntity("NI_Cup","entities/urban/kitchen/mug_coffee/mug_coffee.ent",pose,cVector3f(1));
   cLuxProp@ prop=Map_GetProp("NI_Cup");
   if(prop is null || prop.GetMainBody() is null){LogNewLine("NI_CREATE_FAILED");return;}
   prop.GetMainBody().SetGravity(false);
   cVector3f centre=prop.GetMainBody().GetBoundingVolume().GetWorldCenter();
   prop.GetMainBody().SetPosition(prop.GetMainBody().GetWorldPosition()+cam.GetPosition()+cam.GetForward()*0.75f-centre);
   cVector3f created=prop.GetMainBody().GetBoundingVolume().GetWorldCenter();
   cVector3f origin=cam.GetPosition();cVector3f aim=cam.GetForward();
   LogNewLine("NI_CREATED "+prop.GetName()+" centre="+created.x+","+created.y+","+created.z+" camera="+origin.x+","+origin.y+","+origin.z+" aim="+aim.x+","+aim.y+","+aim.z);
   Map_AddTimer("NI_PRESS",0.5f,"NIAcquire");
  }else if(name=="NI_PRESS"){
   cScript_RunGlobalFunc("State_Normal","","_Global_GetFocusEntityName");
   LogNewLine("NI_FOCUS "+cScript_GetGlobalReturnString());
   cCamera@ cam=cLux_GetPlayer().GetCamera();cVector3f dir=cam.GetForward();cVector3f pos=cam.GetPosition();
   cLuxClosestEntityData hit;bool found=cLux_GetClosestEntity(pos,dir,3.0f,0,false,hit);
   LogNewLine("NI_RAY pos="+pos.x+","+pos.y+","+pos.z+" dir="+dir.x+","+dir.y+","+dir.z+" hit="+found);
   if(found && hit.mpEntity !is null)LogNewLine("NI_HIT "+hit.mpEntity.GetName()+" allowed="+hit.mpEntity.CanInteract(0,hit.mpBody)+" distance="+hit.mfDistance);

   cLuxProp@ prop=Map_GetProp("NI_Cup");
   if(prop !is null && prop.GetMainBody() !is null){
    cVector3f centre=prop.GetMainBody().GetBoundingVolume().GetWorldCenter();
    cVector3f toward=cMath_Vector3Normalize(centre-pos);cLuxClosestEntityData target;
    bool direct=cLux_GetClosestEntity(pos,toward,3.0f,0,false,target);
    LogNewLine("NI_BODY centre="+centre.x+","+centre.y+","+centre.z+" directHit="+direct+" disabled="+prop.GetInteractionDisabled()+" allowed="+prop.CanInteract(0,prop.GetMainBody()));
    if(direct && target.mpEntity !is null)LogNewLine("NI_DIRECT "+target.mpEntity.GetName());
   }
   cScript_RunGlobalFunc("NITEST","","PRESS");Map_AddTimer("NI_HELD",0.5f,"NIAcquire");
  }else if(name=="NI_HELD"){
   cScript_RunGlobalFunc("NITEST","","CHECK");Map_AddTimer("NI_RELEASE",0.5f,"NIAcquire");
  }else if(name=="NI_RELEASE"){
   cScript_RunGlobalFunc("NITEST","","RELEASE");Map_AddTimer("NI_DONE",0.5f,"NIAcquire");
  }else if(name=="NI_DONE"){cScript_RunGlobalFunc("NITEST","","CHECK");LogNewLine("NI_ACQUISITION_DONE");}
 }
'''
  if '--native-tool-acquisition' in sys.argv:
   entity=sys.argv[sys.argv.index('--native-tool-acquisition')+1]
   assert entity in [i['entity'] for i in json.loads((R/'reference/native_input_animation_inventory.json').read_text())['items']]
   extra=extra.replace('entities/urban/kitchen/mug_coffee/mug_coffee.ent',entity)
   extra=extra.replace('LogNewLine("NI_ACQUISITION_DONE");','cScript_RunGlobalFunc("PlayerToolHandler","","NIFreshCheck");LogNewLine("NI_ACQUISITION_DONE");')
  if '--native-sdl-acquisition' in sys.argv:extra=extra.replace('\"NITEST\",\"\",\"PRESS\"','\"NITEST\",\"\",\"SDL_PRESS\"').replace('\"NITEST\",\"\",\"RELEASE\"','\"NITEST\",\"\",\"SDL_RELEASE\"')
  marker='void IUOriginalOnStart()';assert marker in m;m=m.replace(marker,extra+'\n'+marker,1)
 if '--native-chip-use' in sys.argv:
  assert '--inventory-audit' in sys.argv
  m=m.replace('SequenceInsertCatherineChip("");\n\t\treturn true;','LogNewLine("NI_CHIP_AUTHORED_USE");SequenceInsertCatherineChip("");\n\t\treturn true;',1)
  m=m.replace('mbCatherineFixed = true;','mbCatherineFixed = true;LogNewLine("NI_CHIP_AUTHORED_COMPLETE");')
 put(G/f'maps/{chapter}/{map_name}/{map_name}.hps',m)
 profile='SOMA_VR_Delta_'+nonce
 if load_save:
  docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
  put(docs/'My Games/Soma'/profile/'IU'/load_save.name,load_save.read_bytes())

 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/iu_user.cfg').replace('vr_pump_lab.hpm','02_03_delta.hpm').replace('maps/vr_pump_lab/','maps/chapter02/02_03_delta/');cfg=cfg.replace('02_03_delta',map_name).replace('maps/chapter02/',f'maps/{chapter}/');cfg=cfg.replace('Pos = "PlayerStartArea_1"', 'Pos = "'+start_area+'"');put(G/'config/iu_init.cfg',cfg)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="180" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" FirstGameStart="false" SaveConfig="false" />\n<SOMA_VR_Comfort SMAA="false" DesktopMirror="true" />\n'
 if '--neutral-desktop-mouse' in sys.argv:
  assert '--movement-replay' in sys.argv or input_mode in (1,2)
  defaults=defaults.replace('SmoothMouse="true"','SmoothMouse="false" MouseSensitivity="0"')
 if '--ssao-off' in sys.argv:
  assert 'SSAOActive="true"' in defaults or 'SSAOActive="false"' in defaults
  defaults=defaults.replace('SSAOActive="true"','SSAOActive="false"')
 defaults=defaults.replace('<SOMA_VR_Comfort SMAA=', '<SOMA_VR_Comfort InputMode="'+str(input_mode)+'" SMAA=')
 selected=defaults.replace('SMAA="false"','SMAA="true"') if '--saved-on' in sys.argv else defaults
 (out/'fixture-user-settings.cfg').write_text(selected)
 put(G/'config/iu_user.cfg',selected)
 put(G/'cpu10_visibility_mode.txt','1' if '--visibility-jobs-on' in sys.argv else '2' if '--visibility-jobs-off' in sys.argv else '0')
 put(G/'cpu9_render_mode.txt','2' if receipt['arguments'].get('iw_reference') else '1' if '--render-jobs-on' in sys.argv else '2' if '--render-jobs-off' in sys.argv else '0')
 put(G/'cpu4_texture_storage_trial.txt','4' if '--cpu51-baseline' in sys.argv else '3' if '--texture-medium-trial' in sys.argv else '2' if '--texture-latc-trial' in sys.argv else ('1' if '--texture-storage-trial' in sys.argv else '0'))
 (out/'texture-mode.txt').write_text('4' if '--cpu51-baseline' in sys.argv else '3' if '--texture-medium-trial' in sys.argv else '2' if '--texture-latc-trial' in sys.argv else ('1' if '--texture-storage-trial' in sys.argv else '0'))
 for p in G.glob('iu_eye_*.rgba'):put(p,b'')
 priority=subprocess.NORMAL_PRIORITY_CLASS if '--normal-priority' in sys.argv else subprocess.BELOW_NORMAL_PRIORITY_CLASS
 (out/'process-priority.json').write_text(json.dumps({'priority':'normal' if '--normal-priority' in sys.argv else 'below_normal','scope':'test launch only'},indent=2))
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IU','-cfg','config/iu_init.cfg'],cwd=G,creationflags=4|priority)
 if '--msaa-samples' in sys.argv:
  samples=int(sys.argv[sys.argv.index('--msaa-samples')+1]);assert samples in (2,4,8)
  put(G/'msaa_probe.dll',(R/'build/msaa_observer_is.dll').read_bytes())
  put(G/'msaa_request.txt',str(samples));put(G/'msaa_ready.txt','');put(G/'msaa_probe.txt','')
  check=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma.exe','msaa_probe.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25)
  assert 'SUCCESS' in check.stdout,check.stdout+check.stderr
  for attempt in range(50):
   if (G/'msaa_ready.txt').read_text()=='1 1':break
   time.sleep(.1)
  assert (G/'msaa_ready.txt').read_text()=='1 1','MSAA observer not installed'
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma.exe','hpl3vr.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25);assert 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0
 print('VR test PID',proc.pid,'evidence',out,flush=True)
 timedout=False
 try:proc.wait(timeout=360 if '--xml-lifetime' in sys.argv or '--native-map-transition' in sys.argv else 300 if '--delta-route' in sys.argv else 240 if '--reload-streaming' in sys.argv or '--long-replay' in sys.argv or '--arm-playback' in sys.argv else (160 if '--runtime-transitions' in sys.argv else 115))
 except subprocess.TimeoutExpired:timedout=True;proc.terminate();proc.wait(timeout=10)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for src,name in [(docs/'My Games/Soma'/profile/'hpl.log','hpl.log'),(G/'hpl3vr.log','hpl3vr.log')]:
  if src.exists():(out/name).write_bytes(src.read_bytes())
 if '--save-mode-handoff' in sys.argv:
  saves=list((docs/'My Games/Soma'/profile).rglob('*.sav'))
  created=[s for s in saves if not load_save or s.name!=load_save.name]
  assert created, 'Native save request produced no new save file'
  (out/'saved').mkdir()
  for s in created:(out/'saved'/s.name).write_bytes(s.read_bytes())
 if '--msaa-samples' in sys.argv:(out/'msaa-probe.txt').write_bytes((G/'msaa_probe.txt').read_bytes())
 for p in G.glob('iu_eye_*.rgba'):
  if p.stat().st_size:(out/p.name).write_bytes(p.read_bytes())
  if p not in saved:saved[p]=None
 if '--movement-replay' in sys.argv and (G/'cpu14_events.bin').exists():(out/'cpu14_events.bin').write_bytes((G/'cpu14_events.bin').read_bytes())
 if '--movement-replay' in sys.argv and (G/'cpu6_movement.bin').exists():(out/'cpu6_movement.bin').write_bytes((G/'cpu6_movement.bin').read_bytes())
 log=(out/'hpl.log').read_text(errors='replace');vr=(out/'hpl3vr.log').read_text(errors='replace')
 result={'scope':('Actual OpenXR session with test-only synthetic controller samples; native acquisition and solver.' if '--movement-replay' in sys.argv else __doc__),'input_mode':input_mode,'mode_latched':('NI01 INPUT MODE '+str(input_mode)+':') in vr,'timedout':timedout,'completed':'IU_VR_DONE' in log,'stages':[l for l in log.splitlines() if 'IU_' in l or 'NI_' in l],'render':[l for l in vr.splitlines() if 'IU_' in l or 'SMAA ' in l or 'DFR STATUS' in l],'script_errors':[l for l in log.splitlines() if ' : ERR ' in l or l.startswith('ERROR: Could not find method')],'engine_errors':[l for l in log.splitlines() if l.startswith('ERROR:')]}
 result['process_exit_code']=proc.returncode
 result['script_callback_errors']=[l for l in log.splitlines() if "ERROR: Could not find script object" in l]
 if load_save:result['scope']='Actual OpenXR and copied existing save; readiness-based observation. Inventory audit equips saved records through native EquipTool; no physical input or authored use/destination assertion.'
 if '--scripted-route-transition' in sys.argv:
  result['scripted_route_hides']=log.count('CPU53_ROUTE_HIDE ');result['scripted_route_restores']=log.count('CPU53_ROUTE_RESTORE ')

 # Preserve every occurrence in hpl.log, but avoid repeating identical errors
 # hundreds of thousands of times in the summary. Failure gates remain intact.
 from collections import Counter
 result['engine_error_counts']=dict(Counter(result['engine_errors']))
 result['engine_errors']=list(result['engine_error_counts'])
 if '--lifetime-native-route' in sys.argv:
  result['native_preloaded_route']=all(x in log for x in ('CPU20_NATIVE_CHANGE_REQUEST','CPU20_THETA_LEAVE','CPU29_TUNNELS_ENTER'))
  result['scope']='Native preloaded Theta-to-Tunnels route gated by Map_IsPreloadCompleted; fixture story setup omitted; no physical-controller validation.'
 if '--production-short-exit' in sys.argv:result['scope']='Installed production DLL in isolated Theta short-exit fixture; no synthetic hands or profiling hooks, no performance assertions.'
 (out/'result.json').write_text(json.dumps(result,indent=2))
 if '--scripted-route-transition' in sys.argv:assert result['scripted_route_hides']==3 and result['scripted_route_restores']==3,'Scripted hand transition missing'
 if '--xml-exit-hold' in sys.argv:
  import re
  assert re.search(r'CPU20_SHUTDOWN pending_before [1-9]\d* pending_after 0 nodes [1-9]\d*',vr),'Pending retirement did not drain at native shutdown'
  result['scope']='Native exit while retirement intentionally held; no performance or hand assertions.'
 elif '--xml-short-exit' in sys.argv:
  result['scope']='Native short-exit reference; no performance or hand assertions.'
 elif '--xml-observer' in sys.argv:
  assert receipt['arguments'].get('xml_observer'),'Wrong capture mode'
  assert (out/'cpu14_events.bin').stat().st_size>48 and 'CPU20_OBSERVER_SAVED' in vr,'Loader observation missing'
  if '--lifetime-native-route' not in sys.argv:result['scope']='Actual OpenXR, native loader observation only. No synthetic movement or held-object assertions.'
 elif '--movement-replay' in sys.argv:
  assert '--input-trace-short' in sys.argv or (out/'cpu6_movement.bin').stat().st_size>0,'Movement capture missing; do not accept empty phase coverage'
 if receipt['arguments'].get('wait_overlap_trial'):
  assert 'CPU53 WAIT lifecycle slots verified' in vr and 'CPU53 WAIT CONTRACT FAILURE' not in vr,'Runtime candidate did not activate or violated wait contract'
 if '--cpu51-baseline' in sys.argv and not receipt['arguments'].get('iw_reference'):
  assert receipt['arguments'].get('cpu51_baseline'),'Private builder must select CPU51 allocation policy'
  assert 'minimum_base_bytes 0' in vr and 'exact LATC2 1' in vr,'CPU51 allocation policy not active'
 if '--texture-latc-trial' in sys.argv or '--texture-medium-trial' in sys.argv:
  if '--production-payload' in sys.argv:
   assert receipt['arguments']['cpu_texture_min_bytes']==(65536 if '--texture-medium-trial' in sys.argv else 2097152),'Wrong production allocation policy'
   assert 'exact LATC2 1' in vr,'Native exact-format support unavailable'
  else:
   assert ('minimum_base_bytes 65536' if '--texture-medium-trial' in sys.argv else 'minimum_base_bytes 2097152') in vr,'Wrong allocation policy'
   assert 'exact LATC2 1' in vr and 'CPU4_STORAGE decision immutable' in vr,'Requested optimized texture path not verified in capture'
 if '--gui-widget-regression' in sys.argv:
  result['native_widget_pass']=all(('CPU16_WIDGET|mode='+str(i)+'|accepted=1|other=0') in log for i in range(2))
  assert result['native_widget_pass'],'Native widget acceptance differs with preinstalled hooks or registration'
 if '--native-chip-use' in sys.argv:result['scope']='Actual OpenXR with copied Delta save; synthetic native equip/action and test repositioning; native ray/CanUse, authored chip insertion and inventory removal asserted. Not physical device input.'
 if '--native-animation-batch' in sys.argv:result['scope']='Actual OpenXR with authentic Tool assets; synthetic global pickup, native draw/idle/holster and attachment. Authored map use callbacks and physical device input omitted.'
 if '--native-handheld' in sys.argv:result['scope']='Actual OpenXR with authentic handheld entity; direct native OnInteract and cancel action, native state transitions. Authored GUI contents and physical device input omitted.'
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('render','engine_errors')},indent=2),flush=True)
 if '--lifetime-native-route' in sys.argv:assert result['native_preloaded_route'],'Native preloaded map transition not completed'
 if '--inventory-audit' in sys.argv:
  assert 'AUTHORED GAME CANDIDATE LATCH' in vr and 'TITLE -> GAMEPLAY SAFETY RELEASE' in vr, 'Saved-game VR handoff missing'
  assert 'NI_RECAP_DISMISS' in log, 'Recap dismissal was not exercised'
  assert 'NI_SAVE_READY ' in log, 'Saved-world readiness was not observed'
  assert 'NI_INVENTORY_ITEM ' in log, 'Empty inventory cannot validate migration'
  assert 'Could not find script object' not in log, 'Native callback routing failed'
  assert 'NI_CALLBACK_EXECUTED StunRod _Global_OnEquip ok=true' in log and 'NI_CALLBACK_EXECUTED GoyaChip _Global_OnEquip ok=true' in log, 'Saved entity callback execution failed'
  assert not any('NI_SAVED_PROXY' in line and ('active=true' in line or 'collide=true' in line or 'saved=true' in line) for line in log.splitlines()), 'Saved physical hand remains enabled in native-input mode'
  assert 'available context' not in log, 'Script contexts exhausted'
  assert 'NI_EQUIP index=0 accepted=true' in log and 'NI_EQUIP index=1 accepted=true' in log, 'Native inventory equip did not accept both entries'
  assert '--native-chip-use' in sys.argv or not any('hud=MISSING' in line and 'NI_Missing' not in line for line in log[log.index('IU_STAGE|4|'):].splitlines()), 'Equipped inventory HUD restoration failed'
 if '--motion-save-audit' in sys.argv:
  assert 'Could not find script object' not in log, 'Save return callback dispatch failed'
  settled=log[log.index('IU_STAGE|4|'):]
  assert 'NI_MOTION_INVENTORY count=2 current=-1 reconciled=true' in settled, 'Saved native equip ownership not retired'
  assert not any('NI_MOTION_ITEM' in x and 'hudActive=true' in x for x in settled.splitlines()), 'Native HUD still visible in motion mode'
  assert 'NI_MOTION_ITEM name=StunRod stowed=true hudActive=false carrier=true carrierActive=false' in settled and 'NI_MOTION_ITEM name=GoyaChip stowed=true hudActive=false carrier=true carrierActive=false' in settled, 'Shoulder inventory/carriers changed'
 if '--native-tool-scale' in sys.argv:assert 'NI_TOOL_SCALE value=1' in log, 'Native tool presentation stayed quarter scale'
 if '--native-chip-use' in sys.argv:assert log.count('NI_CHIP_AUTHORED_USE')==1 and 'NI_CHIP_AUTHORED_COMPLETE' in log, 'Native chip use sequence incomplete'
 if '--native-chip-use' in sys.argv:assert 'NI_INVENTORY count=1 current=-1' in log, 'Accepted chip was not removed from inventory'
 if '--native-map-transition' in sys.argv:assert 'NI_THETA_TRANSITION' in log and 'NI_TUNNELS_ENTER' in log, 'Native map transfer did not complete'
 if '--missing-owner' in sys.argv:assert 'NI_MISSING_NAMED accepted=false preserved=true' in log, 'Named equip reported success after rejection'
 if '--missing-owner' in sys.argv:assert 'NI_MISSING_REJECT accepted=false preserved=true' in log, 'Missing item changed equipped ownership'
 if '--native-animation-batch' in sys.argv:
  for i in range(len(animation_cases)):assert ('callback=true current='+str(i)+' inventory='+str(i+1)) in log, 'Animation pickup failed for case '+str(i)
  assert 'NI_ANIM_POSE name=MISSING' not in log and 'scale=0.250000' not in log, 'Animation missing or incorrectly scaled'
 if '--native-handheld' in sys.argv:
  assert 'NI_HANDHELD_ENTER physical=false' in log and 'NI_HANDHELD_CANCEL allowed=true entering=false' in log and 'NI_HANDHELD_LEAVE physical=false' in log, 'Native handheld enter/cancel/leave incomplete'
  assert log.index('NI_HANDHELD_ENTER physical=false') < log.index('NI_HANDHELD_CANCEL') < log.index('NI_HANDHELD_LEAVE physical=false'), 'Handheld left before the requested cancellation; investigate rather than count as cancel success'
 if '--native-tool-acquisition' in sys.argv:assert 'NI_FRESH count=1 current=0 creates=1' in log, 'Fresh item not equipped exactly once'
 if '--native-acquisition' in sys.argv and '--native-tool-acquisition' not in sys.argv:
  assert 'NI_FOCUS NI_Cup' in log and 'NI_TEST CHECK state player/PlayerState_Interact_Grab.hps' in vr,'Native target selection/acquisition was not proven'
 if '--native-menu-exit' in sys.argv:assert 'CPU29_NATIVE_APP_EXIT' in log,'Native menu exit was not reached'
 if '--native-icon-audit' in sys.argv:
  assert 'NI_ICON_DRAW' in log,'Native icon surface was not reached; visual verification cannot be claimed'
  # The bounded two-second log can miss a brief crossing during a yaw sweep.
  if '--native-acquisition' in sys.argv and '--yaw-sweep' not in sys.argv:assert 'NI_ICON_DRAW focus=true' in log,'No accepted target reached the icon surface'
 if '--gamepad-icons' in sys.argv:
  glyphs=[line for line in log.splitlines() if 'NI_GLYPH phase=' in line]
  assert len(glyphs)>=8 and all('presetsEqual=true' in line for line in glyphs), 'Native profiles differ or fixture incomplete'
  assert any('style=2 prefix=ps4' in line and 'but_x' in line for line in glyphs),'PlayStation artwork not selected'
  assert any('style=1 prefix=x360' in line and 'but_a' in line for line in glyphs),'Xbox artwork not selected'
 assert result['mode_latched'],'Requested native mode was not latched'
 assert result['completed'] and proc.returncode==0 and not result['timedout'] and not result['script_errors'] and not any('Failed to start occlusion query' in x for x in result['engine_errors']),'Isolated run did not complete cleanly; inspect preserved evidence'
 assert not any('#IND' in x and 'Body ' in x for x in result['engine_errors']),'Non-finite physics body: route recording cannot certify later physics/performance'
 if '--native-route-placement' in sys.argv:
  assert not any('CPU53Route' in x for x in result['engine_errors']),'Native fixture start position was unavailable'
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)


 (out/"restored.json").write_text(json.dumps({"restored":True,"files":len(saved)}))

