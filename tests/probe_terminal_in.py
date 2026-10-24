"""Native AngelScript terminal policy with synthetic state fields; real Theta map policy and PID API. Not physical contact, controller or progression validation."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid
R=Path(__file__).resolve().parents[1]
W=R.parents[1];G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/IN-terminal-pid';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 mp=Path('maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')
 fixture='\n [nosave] float mfILClock=0;\n void ILProbe(float dt){mfILClock+=dt;if(mfILClock<3 || mfILClock>3+dt)return;\n cScript_RunGlobalFunc("State_Interact_Terminal","cScrPlayerState_Interact_Terminal","_Global_INPolicy");\n bool ok=true;\n eSimulationTerminalState saved=mSimulationTerminalState;\n mSimulationTerminalState=eSimulationTerminalState_SimulationRunning;\n ok=ok&&!VR_CanUseWorldControlsFromTerminal("BrainScanSimulationTerminal");\n mSimulationTerminalState=eSimulationTerminalState_SimulationSetup;\n ok=ok&&VR_CanUseWorldControlsFromTerminal("BrainScanSimulationTerminal");\n mSimulationTerminalState=saved;\n ok=ok&&!VR_CanUseWorldControlsFromTerminal("UnknownScriptedTerminal");\n LogNewLine("IN_RESTRICTIONS|"+ok);\n // Native PID equal-time motor experiment; isolated numerical integration,\n // not Newton collision or live controller validation.\n for(int hz=60;hz<=120;hz+=60)for(int mode=0;mode<4;mode++){\n cPidControllerVec3 pid;pid.SetErrorNum(10);pid.i=0;\n pid.p=mode==0?6:(mode==1?10:15);pid.d=mode==0?.1f:(mode==1?0:1);\n pid.Reset();float v=0;float pos=0;float dt2=1.0f/hz;\n for(int n=0;n<hz*2;n++){\n float wanted=mode==0?cMath_Clamp(12*(.3f*n/hz-pos),-2.0f,2.0f):.5f;\n cVector3f f=pid.Output(cVector3f(wanted-v,0,0),dt2);\n v+=cMath_Clamp(f.x,-100.0f,100.0f)*dt2;pos+=v*dt2;\n }\n LogNewLine("IN_PID|hz="+hz+"|mode="+mode+"|v="+v+"|pos="+pos);\n }\n LogNewLine("IL_DONE|NONCE");cEngine_Exit();}\n'.replace('NONCE',nonce)
 # Use the actual native permission function name.
 name='CanUseChip'
 fixture=fixture.replace('OnCanUseChip(',name+'(')
 i=s.index('{',s.index('class cScrMap'));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r'void Update\(float (\w+)\)\s*\{',s);s=s[:m.end()]+'ILProbe('+m[1]+');'+s[m.end():];put(G/mp,s)
 state=(G/'script/player/PlayerState_Interact_Terminal.hps').read_text()
 marker='    bool VR_WorldControlsAllowed()'
 old=(R/'tests/fixtures/in_baseline/terminal_policy.hps').read_text();a0=old.index(marker);b0=old.index('\tvoid Exit()',a0)
 baseline=old[a0:b0].replace('VR_WorldControlsAllowed','INBaselineAllowed')
 probe=r"""
 void _Global_INPolicy(){
 tID oldID=mPropID;int oldState=mlPreviousState;bool oldOwn=mbVRLeaveOwnsSequence;
 array<tString> names={"ScanRoomTerminal","LegacyTerminal","BrainScanSimulationTerminal"};
 for(uint k=0;k<names.length();k++){
 cLuxProp@ p=Map_GetProp(names[k]);if(p is null){LogNewLine("IN_FAIL|missing "+names[k]);continue;}
 mPropID=p.GetID();mlPreviousState=ePlayerState_Normal;mbVRLeaveOwnsSequence=true;
 bool before=INBaselineAllowed();bool after=VR_WorldControlsAllowed();
 LogNewLine("IN_POLICY|"+names[k]+"|before="+before+"|after="+after);
 mlPreviousState=ePlayerState_InteractiveCameraAnimation;
 if(VR_WorldControlsAllowed())LogNewLine("IN_FAIL|scripted return permitted");
 }
 mPropID=tID();mlPreviousState=ePlayerState_Normal;
 if(VR_WorldControlsAllowed())LogNewLine("IN_FAIL|missing prop permitted");
 mPropID=oldID;mlPreviousState=oldState;mbVRLeaveOwnsSequence=oldOwn;
 }
 """
 put(G/'script/player/PlayerState_Interact_Terminal.hps',state.replace(marker,baseline+probe+marker))
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
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'IN_' in x or 'IL_' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log};(out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)




assert result["completed"] and result["exit"]==0, result
assert "IN_RESTRICTIONS|true" in log and "IN_FAIL|" not in log and " : ERR " not in log,result
assert "IN_POLICY|ScanRoomTerminal|before=false|after=true" in log,result
assert "IN_POLICY|LegacyTerminal|before=false|after=true" in log,result
