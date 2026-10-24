"""Native saved-map lever interaction; real authorization and motor update; simulated held action and packet feed, native damping and stabilized test camera. No XR sampling, hand collision or full physics-option validation."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid,sys
hz=int(sys.argv[1]);assert hz in (60,120)
target=sys.argv[2];assert target in ("vent_grating_lever_1","vent_grating_lever_2","HandleDoorSeal_1","INLeverFixture")
R=Path(__file__).resolve().parents[1]
W=R.parents[1];G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/IP-native-lever';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 mp=Path('maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')

 fixture=r"""
 [nosave] float mfINTime=0;[nosave] bool mbINStart=false;[nosave] cVector3f mvINStart;
 void ILProbe(float dt){mfINTime+=dt;
 if(mfINTime<3)return;
 if("TARGET"=="INLeverFixture" && Map_GetProp("INLeverFixture") is null){
 cMatrixf pose=Map_GetProp("HandleDoorSeal_1").GetMainBody().GetLocalMatrix();
 pose.SetTranslation(cVector3f(0,100,0));
 cLux_GetCurrentMap().CreateEntity("INLeverFixture","entities/station/doors/vent_grating/vent_grating_lever.ent",pose,cVector3f(1));return;}
 cLuxProp@ prop=Map_GetProp("TARGET");
 if(prop is null){LogNewLine("IN_FAIL|prop missing");cEngine_Exit();return;}
 iPhysicsBody@ body=prop.GetMainBody();
 if(!mbINStart){mbINStart=true;Player_ChangeStateToNormal();
 cVector3f pos=body.GetLocalMatrix().GetTranslation();mvINStart=pos;
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(pos+cVector3f(0,-1,1),false);
 LogNewLine("IN_BODY|mass="+body.GetMass()+"|active="+prop.IsActive()+"|disabled="+prop.GetInteractionDisabled());bool can=prop.IsActive()&&!prop.GetInteractionDisabled()&&prop.CanInteract(0,body);bool entered=can&&prop.OnInteract(0,body,pos,"");
 LogNewLine("IN_NATIVE_BEGIN|hz=HZ|can="+can+"|entered="+entered+"|state="+cLux_GetPlayer().GetCurrentStateId());
 cEngine_SetUpdatesPerSec(HZ);return;}
 cLux_GetPlayer().GetCharacterBody().SetFeetPosition(mvINStart+cVector3f(0,-1,1),false);
 cLux_GetPlayer().GetCamera().SetPosition(mvINStart+cVector3f(0,.6f,1));
 cScript_RunGlobalFunc("State_Interact_Lever","","_Global_INFeed");
 if(mfINTime<9)return;
 cVector3f pos=body.GetLocalMatrix().GetTranslation();
 LogNewLine("IN_NATIVE_END|hz=HZ|distance="+cMath_Vector3Dist(mvINStart,pos)+"|state="+cLux_GetPlayer().GetCurrentStateId());
 cScript_RunGlobalFunc("State_Interact_Lever","","_Global_INReport");
 LogNewLine("IL_DONE|NONCE");cEngine_Exit();}
 """.replace('TARGET',target).replace('HZ',str(hz)).replace('NONCE',nonce)
 s=s.replace('void OnStateChangeDoorSeal(const tString &in asEntity, int alState)\n\t{','void OnStateChangeDoorSeal(const tString &in asEntity, int alState)\n\t{LogNewLine("IN_SEAL_CALLBACK|state="+alState);')
 s=re.sub(r'(void OnDoorSealOpenCompleted\([^)]*\)\s*\{)',r'\1LogNewLine("IN_SEAL_OPEN_COMPLETED");',s)
 i=s.index('{',s.index('class cScrMap'));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r'void Update\(float (\w+)\)\s*\{',s);s=s[:m.end()]+'ILProbe('+m[1]+');'+s[m.end():];put(G/mp,s)
 p=G/'script/player/PlayerState_Interact_RotateBase.hps';state=p.read_text()
 marker=' void Init()'
 probe=r"""
 [nosave] bool mbINHeld=true;[nosave] int mlINUpdates=0;[nosave] int mlINPackets=0;[nosave] float mfINSumDT=0;
 void _Global_INFeed(){if(cLux_GetPlayer().GetCurrentStateId()!=ePlayerState_Lever)return;mlINPackets++;OnAnalogInput(eAnalogType_Look,cVector3f(-.0070833333f,0,3));}
 void _Global_INReport(){LogNewLine("IN_NATIVE_COUNTS|updates="+mlINUpdates+"|packets="+mlINPackets+"|dt="+mfINSumDT+"|angle="+cPhysics_ToJointHinge(cLux_ID_Joint(mJointID)).GetAngle());}
 """
 state=state.replace(marker,probe+marker,1)
 match=re.search(r'void Update\(float (\w+)\)\s*\{',state);assert match
 state=state[:match.end()]+'mlINUpdates++;if(mlINUpdates%'+str(hz//4)+'==0)LogNewLine("IN_ANGLE|step="+mlINUpdates+"|angle="+cPhysics_ToJointHinge(cLux_ID_Joint(mJointID)).GetAngle());mfINSumDT+='+match[1]+';'+state[match.end():]

 state=state.replace('return cScript_GetGlobalReturnBool();','return true;').replace('cInput_IsTriggered(eAction_Interact)==false','!mbINHeld')
 put(p,state)
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
 save=D/'Main/Default/AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav';assert save.exists()
 menu=menu.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\nif(!mbILStarted){mbILStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1).replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 put(D/'SOMA_VR_IL/IL'/save.name,save.read_bytes())
 cfg=(G/'config/main_init.cfg').read_text().replace('MainSaveFolder = "Main"','MainSaveFolder = "SOMA_VR_IL"').replace('config/default_user_settings.cfg','config/il_user.cfg');put(G/'config/il_init.cfg',cfg)
 settings=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/il_user.cfg',settings)
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'target':target,'hz':hz,'scope':__doc__,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'S26IP' in x or 'IN_' in x or 'IL_' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log};(out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)




assert result["completed"] and result["exit"]==0, result
assert "IN_NATIVE_BEGIN|hz="+str(hz)+"|can=true|entered=true" in log,result

assert any("IN_ANGLE" in x for x in result["lines"]),result


if target=="HandleDoorSeal_1":
 assert log.count("IN_SEAL_CALLBACK|state=1")==1,result
 assert log.count("IN_SEAL_OPEN_COMPLETED")==1,result

if target=="INLeverFixture":
 angles=[float(x.split("|angle=")[1]) for x in result["lines"] if "IN_ANGLE|" in x]
 assert max(angles)-min(angles)>.5,"Fixture did not establish meaningful lever travel; NOT a passing motor test"

assert any("S26IP LEVER MOTOR name=HandleDoorSeal_1" in x for x in result["lines"]),result
assert sum("S26IP LEVER MOTOR" in x for x in result["lines"])<=120,result

