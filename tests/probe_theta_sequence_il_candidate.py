"""Isolated native saved-game sequence probe. Script-driven interact requests and waypoint relocation replace controller input/walking. Real OpenXR path, scripted checkpoints; no physical grip or haptics validation."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid,ctypes
from ctypes import wintypes
R=Path(__file__).resolve().parents[1]
W=R.parents[1];G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/IK-theta-sequence-xr';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 live=Path(r'D:\SteamLibrary\steamapps\common\SOMA')
 for name in ['hpl3vr_vr_settings.ini','hpl3vr_hand_calibration.ini','item_grips.dat','openxr_loader.dll','hpl3vr_inject.exe']:
  if (live/name).exists():put(G/name,(live/name).read_bytes())
 put(G/'hpl3vr.dll',(R/'build/il-probe/hpl3vr.dll').read_bytes())
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 p=G/'script/props/Prop_EnergySource.hps';fs=p.read_text(encoding='utf-8-sig')
 fs=fs.replace('[nosave] int mlVRHealEvidence=0;','[nosave] int mlVRHealEvidence=0; [nosave] int mlILGuideLog=0;')
 fs=fs.replace('mVRHealGuide.ShowFlower(', 'bool ilShown=mVRHealGuide.ShowFlower(')
 anchor='rim,axis,1,stage>=2);'
 fs=fs.replace(anchor,anchor+'if(mlILGuideLog++<4)LogNewLine("IL_FLOWER|name="+mBaseObj.GetName()+"|shown="+ilShown+"|stage="+stage+"|gate="+cScript_RunGlobalFunc("VRGUIDE","","ACTIVE"));')
 put(p,fs)
 mp=Path('maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')
 fixture='''
 [nosave] float mfILClock=0;
 [nosave] float mfILStageClock=0;
 [nosave] int mlILStage=0;
 [nosave] int mlILPrevState=-999;
 void ILProbe(float dt){
 mfILClock+=dt;mfILStageClock+=dt;
 if(mfILStageClock<dt*1.5f){cScript_RunGlobalFunc("VRIL","","Q");LogNewLine("IL_GUIDE_GATE|stage="+mlILStage+"|active="+cScript_RunGlobalFunc("VRGUIDE","","ACTIVE"));}
 int st=cLux_GetPlayer().GetCurrentStateId();
 if(st!=mlILPrevState){mlILPrevState=st;LogNewLine("IL_STATE|"+mfILClock+"|stage="+mlILStage+"|state="+st+"|active="+cLux_GetPlayer().IsActive());}
 if(mlILStage==0 && mfILClock>12){
 LogNewLine("IL_BEGIN|NONCE|cath="+mbCathPluggedIn+"|camera="+mbDunbatCameraActive);
 CollisionEnteredControlRoom("Player","ControlRoomWindowTrigger_1",1);LogNewLine("IL_CAMERA_STARTED|"+mbDunbatCameraActive);LogNewLine("IL_SLOT_DISABLED|"+Map_GetEntity("cath_terminal_1").GetInteractionDisabled());InteractCathTerminal("cath_terminal_1");mlILStage=1;mfILStageClock=0;
 }
 else if(mlILStage==1 && mfILStageClock>12 && st==ePlayerState_Normal && mbCathPluggedIn){
 LogNewLine("IL_AFTER_DIALOG|camera="+mbDunbatCameraActive);CollisionEnteredControlRoom("Player","ControlRoomWindowTrigger_1",-1);
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-23.9f,-9.65f,-10.27f),false);
 cLux_GetPlayer().GetCamera().SetYaw(1.55967f);
 mlILStage=2;mfILStageClock=0;
 }
 else if(mlILStage==2 && mfILStageClock>2){LogNewLine("IL_CLIMB_REQUEST");Entity_CallEntityInteract("ClimbArea_2");mlILStage=3;mfILStageClock=0;}
 else if(mlILStage==3 && mfILStageClock>8 && st==ePlayerState_Normal){
 LogNewLine("IL_AFTER_CLIMB|active="+cLux_GetPlayer().IsActive());OnStateChangeDoorSeal("HandleDoorSeal_1",1);
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-55.6f,10.2f,-18.5f),false);
 mlILStage=6;mfILStageClock=0;
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-31.5f,2.3f,2.1f),false);
 }
 else if(mlILStage==6 && mfILStageClock>8){
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(-55.6f,10.2f,-18.5f),false);mlILStage=4;mfILStageClock=0;
 }
 else if(mlILStage==4 && mfILStageClock>8){
 LogNewLine("IL_SEAL|open="+Entity_IsActive("OpenDoorSeal_1"));Entity_CallEntityInteract("box_simulation_assets_1");
 LogNewLine("IL_BEFORE_DEVICE|permission="+OnCanUseChip("EnvironmentChip","ScanRoomSlot")+"|active="+Entity_IsActive("EnvironmentChip"));
 Entity_CallEntityInteract("EnvironmentChip");mlILStage=5;mfILStageClock=0;
 }
 else if(mlILStage==5 && mfILStageClock>5){LogNewLine("IL_DONE|NONCE|permission="+OnCanUseChip("EnvironmentChip","ScanRoomSlot"));cLux_Exit();}
 if(mfILClock>180){LogNewLine("IL_TIMEOUT|stage="+mlILStage);cLux_Exit();}
 }
'''.replace('NONCE',nonce)
 # Use the actual native permission function name.
 name='CanUseChip'
 fixture=fixture.replace('OnCanUseChip(',name+'(')
 i=s.index('{',s.index('class cScrMap'));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r'void Update\(float (\w+)\)\s*\{',s);s=s[:m.end()]+'ILProbe('+m[1]+');'+s[m.end():];put(G/mp,s)
 # Record the publisher's computed state even without XR; no hidden/show writes or runtime eligibility forced.
 p=G/'script/modules/PlayerHandsHandler.hps';h=p.read_text(encoding='utf-8-sig')
 needle='void HPL3VR_PublishSceneHands()\n\t{'
 # Additional observation method duplicates the exact bHide calculation, without invoking VR callbacks.
 a=h.index('int lPlayerState =',h.index(needle));b=h.index('int lState =',a)
 calc=h[a:b]
 method='\n int mlILHide=-1;\n void ILObserve(){'+calc+'int n=bHide?1:0;if(n!=mlILHide){mlILHide=n;LogNewLine("IL_HAND_GATE|hidden="+n+"|state="+lPlayerState+"|active="+mbActive+"|custom="+mbUseCustomPosition+"|attach="+mbCameraAttachActive);}}\n'
 i=h.index('{',h.index('class cScrPlayerHandsHandler'));h=h[:i+1]+method+h[i+1:]
 h=h.replace('HPL3VR_PublishSceneHands();\n        HPL3VR_UpdateNativeHands();','ILObserve();HPL3VR_PublishSceneHands();\n        HPL3VR_UpdateNativeHands();');put(p,h)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbILStarted=false;\nvoid GuiMainMenuSelection()',1)
 save=D/'Main/mirror_force_11000016B11BA91/AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav';assert save.exists()
 menu=menu.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\nif(!mbILStarted){mbILStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1).replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 put(D/'SOMA_VR_IL/IL'/save.name,save.read_bytes())
 cfg=(G/'config/main_init.cfg').read_text().replace('MainSaveFolder = "Main"','MainSaveFolder = "SOMA_VR_IL"').replace('config/default_user_settings.cfg','config/il_user.cfg');put(G/'config/il_init.cfg',cfg)
 settings=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/il_user.cfg',settings)
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|4)
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma.exe','hpl3vr.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25)
 assert inj.returncode==0 and 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 resume=ctypes.windll.ntdll.NtResumeProcess;resume.argtypes=[wintypes.HANDLE];resume.restype=ctypes.c_long
 assert resume(int(proc._handle))==0

 try:rc=proc.wait(timeout=260)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 (out/(nonce+'-vr.log')).write_bytes((G/'hpl3vr.log').read_bytes());log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'IL_' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log};(out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)



