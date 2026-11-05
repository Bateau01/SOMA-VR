"""Native Theta router body/permission census. No interaction or story state mutation; direct saved-map load omits progression."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid,sys
R=Path(__file__).resolve().parents[1]
W=R.parent;G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/jb-router-geometry';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 mp=Path('maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')

 fixture='\n [nosave] float mfJBClock=0;\n void JBProbe(float dt){mfJBClock+=dt;if(mfJBClock<3 || mfJBClock>3+dt)return;\n cLuxProp@ p=Map_GetProp("ServerKey");if(p is null){LogNewLine("JB_ROUTER_FAIL missing");cEngine_Exit();return;}\n for(int i=0;i<p.GetBodyNum();i++){\n iPhysicsBody@ b=p.GetBody(i);cVector3f lo=b.GetBoundingVolume().GetMin(),hi=b.GetBoundingVolume().GetMax();\n LogNewLine("JB_ROUTER_BODY index="+i+" name="+b.GetName()+" mass="+b.GetMass()+" collide="+b.GetCollide()+" can="+p.CanInteract(0,b)+" bounds="+lo.x+","+lo.y+","+lo.z+":"+hi.x+","+hi.y+","+hi.z);\n }\n LogNewLine("IL_DONE|NONCE");cEngine_Exit();}\n'.replace("NONCE",nonce)
 i=s.index("{",s.index("class cScrMap"));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r"void Update\(float (\w+)\)\s*\{",s);assert m
 s=s[:m.end()]+"JBProbe("+m[1]+");"+s[m.end():];put(G/mp,s)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbILStarted=false;\nvoid GuiMainMenuSelection()',1)
 save=sorted((D/'Main/Default').glob('*02-05-theta-inside*.sav'))[0];assert save.exists()
 menu=menu.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\nif(!mbILStarted){mbILStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1).replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 put(D/'SOMA_VR_IL/IL'/save.name,save.read_bytes())
 cfg=(G/'config/main_init.cfg').read_text(encoding='utf-8-sig').replace('MainSaveFolder = "Main"','MainSaveFolder = "SOMA_VR_IL"').replace('config/default_user_settings.cfg','config/il_user.cfg');put(G/'config/il_init.cfg',cfg)
 settings=(G/'config/default_user_settings.cfg').read_text(encoding='utf-8-sig')+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/il_user.cfg',settings)
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'inserted_fixture':'--inserted' in sys.argv,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'exe_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'JB_ROUTER' in x or 'IL_DONE' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log}
 (out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)




assert result["completed"] and result["exit"]==0,result
assert not any(" : ERR " in x or "Exception" in x or "JB_ENV_MISSING" in x for x in result['lines']),result

