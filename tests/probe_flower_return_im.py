"""Native AngelScript expression/geometry regression with synthetic contact vectors; real engine matrix APIs, no rendered guide or headset validation."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid
R=Path(__file__).resolve().parents[1]
W=R.parents[1];G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/IM-flower-return';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 mp=Path('maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')
 fixture='''
 [nosave] float mfILClock=0;
 float IMMetric(){cScript_SetGlobalReturnVector3f(cVector3f(1));return cScript_GetGlobalReturnVector3f().x;}
 void ILProbe(float dt){mfILClock+=dt;if(mfILClock<3 || mfILClock>3+dt)return;
 cScript_SetGlobalReturnVector3f(cVector3f(.02f,-.15f,.03f));
 cVector3f old=cScript_GetGlobalReturnVector3f()*IMMetric();
 cScript_SetGlobalReturnVector3f(cVector3f(.02f,-.15f,.03f));
 cVector3f copied=cScript_GetGlobalReturnVector3f();float metric=IMMetric();cVector3f fixed=copied*metric;
 LogNewLine("IM_VECTOR|old="+old.x+","+old.y+","+old.z+"|fixed="+fixed.x+","+fixed.y+","+fixed.z);

 int count=0;
 for(int f=0;f<2;f++)for(int sc=0;sc<3;sc++)for(int n=0;n<3;n++){
 bool fist=f==1;float metric=.75f+.25f*sc;
 cVector3f rim(2,3,4);cVector3f axis=n==0?cVector3f(0,1,0):(n==1?cVector3f(1,0,0):cMath_Vector3Normalize(cVector3f(1,1,1)));
 cMatrixf frame=VRGuide_FlowerFrame(rim,axis,fist);frame.SetTranslation(cVector3f(2,3,4));
 cVector3f raw(.02f,-.15f,.03f);cScript_SetGlobalReturnVector3f(raw);
         cVector3f local=cScript_GetGlobalReturnVector3f();
        local*=metric;
        cVector3f anchor=cMath_MatrixMul(frame,local);
        // Index distal joint ends just behind the fingertip skin. Fist knuckle
        // enters 15mm; the palm remains outside. Native healing target untouched.
        cVector3f target=rim+axis*((fist ? -.015f : .014f)*metric);
        frame.SetTranslation(frame.GetTranslation()+target-anchor);
        cMatrixf final=(cMath_MatrixMul(frame,cMath_MatrixScale(metric)));

 cVector3f actual=cMath_MatrixMul(final,raw);float error=(actual-target).Length();
 if(error>.00001f)LogNewLine("IM_GEOMETRY_FAIL|"+error);count++;
 }
 LogNewLine("IM_GEOMETRY|checks="+count);
 LogNewLine("IL_DONE|NONCE");cEngine_Exit();}
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
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'IM_' in x or 'IL_' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log};(out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)




assert result["completed"] and result["exit"]==0, result
assert "IM_GEOMETRY|checks=18" in log and "IM_GEOMETRY_FAIL" not in log and " : ERR " not in log, result
