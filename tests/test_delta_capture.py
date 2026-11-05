"""Isolated real-OpenXR render test. Native menu methods drive transitions;
fixture map/start avoids story setup. No simulated headset/controller poses."""
from pathlib import Path
import subprocess,sys,ctypes,time,json,uuid,hashlib,math
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert '--movement-replay' not in sys.argv or '--runtime-transitions' in sys.argv, 'Held replay requires the full-duration runtime fixture'
assert '--runtime-short' not in sys.argv or '--runtime-transitions' in sys.argv,'runtime-short requires runtime-transitions; otherwise the selector is not exercised'
payload=R/('build/movement' if '--movement-replay' in sys.argv else 'build/native-runtime' if '--production-payload' in sys.argv else 'build/smaa-test')
assert '--production-payload' not in sys.argv or '--runtime-transitions' in sys.argv, 'Production requires runtime selector fixture'
receipt=json.loads((payload/'build-receipt.json').read_text())
assert bool(receipt['arguments'].get('production')) == ('--production-payload' in sys.argv)
assert receipt['dll_sha256']==hashlib.sha256((payload/'hpl3vr.dll').read_bytes()).hexdigest(),'Candidate differs from successful build receipt'
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in receipt['source_hashes'].items()),'Candidate is stale after source edits; rebuild before testing'
exe_hash=hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest()
assert exe_hash=='7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113','Unverified executable for native renderer probes'
if receipt['arguments'].get('parallel_sse') or receipt['arguments'].get('paired_sse'):assert hashlib.sha256((G/'Newton.dll').read_bytes()).hexdigest()=='1be451fb2e250aded9ddf3771418cee21990e4ef07fa0fefe0a8cfaf55766b74','Unverified Newton for SSE job prototype'
assert not subprocess.run(['powershell','-NoProfile','-Command','Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True).stdout.strip()
nonce=uuid.uuid4().hex[:8];out=R/'audit/delta-integration'/nonce;out.mkdir(parents=True);saved={};proc=None
start_area=sys.argv[sys.argv.index('--start-area')+1] if '--start-area' in sys.argv else 'PlayerStartArea_1'
assert start_area in ('PlayerStartArea_1','StartZeppLanding','PlayerStartArea_Airlock2','StartChair','EndOfSimulation'), 'Use an existing native start area, not an implicit fallback'
fixed_yaw=float(sys.argv[sys.argv.index('--fixed-yaw')+1]) if '--fixed-yaw' in sys.argv else None
assert fixed_yaw is None or (math.isfinite(fixed_yaw) and abs(fixed_yaw)<7)
(out/'identity.json').write_text(json.dumps({'exe_sha256':exe_hash,'dll_sha256':hashlib.sha256((payload/'hpl3vr.dll').read_bytes()).hexdigest(),'start_area':start_area,'fixed_script_camera_yaw_radians':fixed_yaw,'scenario':('Apartment kitchen mechanisms fixture' if '--apartment-mechanisms' in sys.argv else 'Phi fixture' if '--phi' in sys.argv else ('Theta indoor physics fixture' if '--theta-physics' in sys.argv else 'Theta DUNBAT camera fixture' if '--theta-camera' in sys.argv else 'Delta fixture'))+', actual OpenXR; no authored progression; optional scripted body/camera yaw, live headset pose; not a performance benchmark'},indent=2))

(out/'build-receipt.json').write_text(json.dumps(receipt,indent=2))
(out/'test-command.json').write_text(json.dumps(sys.argv,indent=2))

def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 if '--movement-replay' in sys.argv:
  put(G/'cpu6_movement.bin',b'');put(G/'cpu14_events.bin',b'')
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 # Replace a leftover old fixture script only inside this run; restore afterward.
 for p in (R/'runtime/maps').rglob('*.hps'):put(G/'maps'/p.relative_to(R/'runtime/maps'),p.read_bytes())
 put(G/'hpl3vr.dll',(payload/'hpl3vr.dll').read_bytes())
 if '--physics-rate' in sys.argv:
  rate=int(sys.argv[sys.argv.index('--physics-rate')+1]);assert rate in (60,120);put(G/'hpl3vr_simulation_rate.txt',str(rate)+'\n')
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
 menu=menu.replace('void GuiMainMenuSelection()','bool iuStarted=false;uint iuBoot=0;\n void GuiMainMenuSelection()',1)
 needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n mbVRGuideDismissed=true;if(iuBoot==0)iuBoot=cSystem_GetApplicationTime();if(!iuStarted && cSystem_GetApplicationTime()-iuBoot>7000){iuStarted=true;ClickNewGame();}',1)
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
 if '--native-menu-exit' in sys.argv:
  assert '--runtime-transitions' in sys.argv
  menu=menu.replace('if(!iuStarted && cSystem_GetApplicationTime()-iuBoot>7000)', 'if(cLux_GetUserConfig().GetBool("CPU29_Test","Finished",false)){LogNewLine("CPU29_NATIVE_APP_EXIT");cLux_Exit();return;}if(!iuStarted && cSystem_GetApplicationTime()-iuBoot>7000)',1)
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
 if '--gui-widget-regression' in sys.argv:
  widget=r"""
 void IUWidgetProbe(){
 cGuiSet@ set=cGui_CreateSet("CPU16Probe",null);set.SetVirtualSize(cVector2f(512),-1000,1000,cVector2f(0));
 cImGui@ gui=cGui_CreateImGui("CPU16Probe",set);cImGuiButtonData data;
 data.mbUseBackgroundGfx=false;data.mbUseInFocusGfx=false;data.mbUseTriggeredGfx=false;
 data.mFont.SetFile("sansation.fnt");data.mFont.mvSize=cVector2f(16);
 for(int mode=0;mode<2;mode++){
  if(mode==1){cScript_RunGlobalFunc("VRGUI","","R");gui.SendMouseVirtualPosition(cVector2f(0),cVector2f(0));cScript_RunGlobalFunc("VRGUI","","E");}
  gui.ClearStates();int accepted=0;int otherCount=0;
  for(int frame=0;frame<5;frame++){
   gui.Begin(1.0f/60.0f);gui.SetShowMouse(true);cVector2f pos(110,110);
   gui.SendMouseVirtualPosition(pos,cVector2f(1));gui.SendMouseVirtualPosition(pos,cVector2f(1));
   gui.SendAction(eImGuiAction_MouseLeft,frame==1||frame==2,frame==1);
   if(gui.DoButton("ONE",tWString(""),data,cVector3f(100,100,1),cVector2f(80,40)))accepted++;
   if(gui.DoButton("TWO",tWString(""),data,cVector3f(220,100,1),cVector2f(80,40)))otherCount++;
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
 menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)\n    {','    void HPL3VR_UpdateComfort(float dt)\n    {\n IUTick();',1)
 if '--saved-on' in sys.argv: menu=menu.replace('elapsed/5000','elapsed/4000').replace('mbVRSMAA=phase==2','mbVRSMAA=phase==0 || phase==2')
 load_save=Path(sys.argv[sys.argv.index('--load-save')+1]) if '--load-save' in sys.argv else None
 if load_save:
  assert load_save.is_file() and load_save.suffix=='.sav' and '--phi' in sys.argv
  menu=menu.replace('ClickNewGame();','StartSavedGameLoad(tWString("'+load_save.name+'"));',1)
  (out/'save-identity.json').write_text(json.dumps({'path':str(load_save),'sha256':hashlib.sha256(load_save.read_bytes()).hexdigest(),'scope':'Native saved state; OnEnter starts observation, story callbacks retained.'},indent=2))
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
  else:
   import re
   m,n=re.subn(r'(void Update\(float \w+\)\s*\{)',r'\1 IUSetYaw(0);',m,count=1)
   if not n:injection+='void Update(float dt){IUSetYaw(dt); }\n'
  if '--yaw-sweep' in sys.argv:injection=injection.replace(f'{fixed_yaw:.9f}f',f'({fixed_yaw:.9f}f+0.35f*(float(cSystem_GetApplicationTime()%8000)<4000.0f ? float(cSystem_GetApplicationTime()%8000)/2000.0f-1.0f : 3.0f-float(cSystem_GetApplicationTime()%8000)/2000.0f))')
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
  m=m.replace('void IUOriginalOnStart()', (R/'tests/cpu18_route.hps').read_text()+'\nvoid IUOriginalOnStart()',1)
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
 put(G/f'maps/{chapter}/{map_name}/{map_name}.hps',m)
 profile='SOMA_VR_Delta_'+nonce
 if load_save:
  docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
  put(docs/'My Games/Soma'/profile/'IU'/load_save.name,load_save.read_bytes())

 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/iu_user.cfg').replace('vr_pump_lab.hpm','02_03_delta.hpm').replace('maps/vr_pump_lab/','maps/chapter02/02_03_delta/');cfg=cfg.replace('02_03_delta',map_name).replace('maps/chapter02/',f'maps/{chapter}/');cfg=cfg.replace('Pos = "PlayerStartArea_1"', 'Pos = "'+start_area+'"');put(G/'config/iu_init.cfg',cfg)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="180" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" FirstGameStart="false" SaveConfig="false" />\n<SOMA_VR_Comfort SMAA="false" DesktopMirror="true" />\n'
 if '--ssao-off' in sys.argv:
  assert 'SSAOActive="true"' in defaults or 'SSAOActive="false"' in defaults
  defaults=defaults.replace('SSAOActive="true"','SSAOActive="false"')
 selected=defaults.replace('SMAA="false"','SMAA="true"') if '--saved-on' in sys.argv else defaults
 (out/'fixture-user-settings.cfg').write_text(selected)
 put(G/'config/iu_user.cfg',selected)
 put(G/'cpu10_visibility_mode.txt','1' if '--visibility-jobs-on' in sys.argv else '2' if '--visibility-jobs-off' in sys.argv else '0')
 put(G/'cpu9_render_mode.txt','1' if '--render-jobs-on' in sys.argv else '2' if '--render-jobs-off' in sys.argv else '0')
 put(G/'cpu4_texture_storage_trial.txt','3' if '--texture-medium-trial' in sys.argv else '2' if '--texture-latc-trial' in sys.argv else ('1' if '--texture-storage-trial' in sys.argv else '0'))
 (out/'texture-mode.txt').write_text('3' if '--texture-medium-trial' in sys.argv else '2' if '--texture-latc-trial' in sys.argv else ('1' if '--texture-storage-trial' in sys.argv else '0'))
 for p in G.glob('iu_eye_*.rgba'):put(p,b'')
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IU','-cfg','config/iu_init.cfg'],cwd=G,creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
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
 try:proc.wait(timeout=360 if '--xml-lifetime' in sys.argv else 300 if '--delta-route' in sys.argv else 240 if '--reload-streaming' in sys.argv or '--long-replay' in sys.argv else (160 if '--runtime-transitions' in sys.argv else 115))
 except subprocess.TimeoutExpired:timedout=True;proc.terminate();proc.wait(timeout=10)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for src,name in [(docs/'My Games/Soma'/profile/'hpl.log','hpl.log'),(G/'hpl3vr.log','hpl3vr.log')]:
  if src.exists():(out/name).write_bytes(src.read_bytes())
 if '--msaa-samples' in sys.argv:(out/'msaa-probe.txt').write_bytes((G/'msaa_probe.txt').read_bytes())
 for p in G.glob('iu_eye_*.rgba'):
  if p.stat().st_size:(out/p.name).write_bytes(p.read_bytes())
  if p not in saved:saved[p]=None
 if '--movement-replay' in sys.argv and (G/'cpu14_events.bin').exists():(out/'cpu14_events.bin').write_bytes((G/'cpu14_events.bin').read_bytes())
 if '--movement-replay' in sys.argv and (G/'cpu6_movement.bin').exists():(out/'cpu6_movement.bin').write_bytes((G/'cpu6_movement.bin').read_bytes())
 log=(out/'hpl.log').read_text(errors='replace');vr=(out/'hpl3vr.log').read_text(errors='replace')
 result={'scope':('Actual OpenXR session with test-only synthetic controller samples; native acquisition and solver.' if '--movement-replay' in sys.argv else __doc__),'timedout':timedout,'completed':'IU_VR_DONE' in log,'stages':[l for l in log.splitlines() if 'IU_' in l],'render':[l for l in vr.splitlines() if 'IU_' in l or 'SMAA ' in l or 'DFR STATUS' in l],'script_errors':[l for l in log.splitlines() if ' : ERR ' in l or l.startswith('ERROR: Could not find method')],'engine_errors':[l for l in log.splitlines() if l.startswith('ERROR:')]}
 result['process_exit_code']=proc.returncode
 if '--lifetime-native-route' in sys.argv:
  result['native_preloaded_route']=all(x in log for x in ('CPU20_NATIVE_CHANGE_REQUEST','CPU20_THETA_LEAVE','CPU29_TUNNELS_ENTER'))
  result['scope']='Native preloaded Theta-to-Tunnels route gated by Map_IsPreloadCompleted; fixture story setup omitted; no physical-controller validation.'
 if '--production-short-exit' in sys.argv:result['scope']='Installed production DLL in isolated Theta short-exit fixture; no synthetic hands or profiling hooks, no performance assertions.'
 (out/'result.json').write_text(json.dumps(result,indent=2))
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
  assert (out/'cpu6_movement.bin').stat().st_size>0,'Movement capture missing; do not accept empty phase coverage'
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
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('render','engine_errors')},indent=2),flush=True)
 if '--lifetime-native-route' in sys.argv:assert result['native_preloaded_route'],'Native preloaded map transition not completed'
 if '--native-menu-exit' in sys.argv:assert 'CPU29_NATIVE_APP_EXIT' in log,'Native menu exit was not reached'
 assert result['completed'] and proc.returncode==0 and not result['timedout'] and not result['script_errors'] and not any('Failed to start occlusion query' in x for x in result['engine_errors']),'Isolated run did not complete cleanly; inspect preserved evidence'
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)

