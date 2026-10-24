"""Native map initialization/compile smoke tests. No VR runtime or completed story sequence."""
from pathlib import Path
import subprocess,sys,re,json,hashlib,time,uuid
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');
 menu=menu.replace('cScript_RunGlobalFunc("VRCOMFORT","SMAA","READY")','true /* fixture: GPU readiness only */')
 probe='''
 void IUProbe(){
   iPostEffect@ effect=cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA");
   int errors=0;if(effect is null){LogNewLine("IU_NATIVE|missing FXAA");return;}
   gbHPL3VRRuntimeActive=true;
   for(int initial=0;initial<3;initial++) {
     cLux_GetUserConfig().SetBool("SOMA_VR_Comfort","UnifiedAA",false);
     cLux_GetUserConfig().SetBool("SOMA_VR_Comfort","SMAA",initial==2);
     cLux_GetUserConfig().SetString("Graphics","AntiAliasing",initial==0 ? "Off" : "FXAA");
     mbVRComfortLoaded=false;HPL3VR_LoadComfort();if(HPL3VR_AASelection()!=initial){errors++;LogNewLine("AA_FAIL migration "+initial);}
     for(int choice=0;choice<3;choice++) {
       HPL3VR_SetAA(choice);
       if(HPL3VR_AASelection()!=choice || mbVRSMAA!=(choice==2) || cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive()!=(choice==1)){errors++;LogNewLine("AA_FAIL set wanted="+choice+" actual="+HPL3VR_AASelection()+" smaa="+mbVRSMAA+" fxaa="+cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive()+" last="+msVRAALast+" runtime="+gbHPL3VRRuntimeActive);}
       HPL3VR_SaveComfort();HPL3VR_LoadComfort();HPL3VR_UpdateSMAA();
       if(HPL3VR_AASelection()!=choice || cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive()!=(choice==1)){errors++;LogNewLine("AA_FAIL reload wanted="+choice+" actual="+HPL3VR_AASelection()+" fxaa="+cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive());}
       // Native menu/preset writes the same key, then the real update observes it.
       cLux_GetUserConfig().SetString("Graphics","AntiAliasing","FXAA");HPL3VR_UpdateSMAA();
       if(HPL3VR_AASelection()!=1 || mbVRSMAA || !cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive()){errors++;LogNewLine("AA_FAIL native actual="+HPL3VR_AASelection()+" smaa="+mbVRSMAA+" fxaa="+cLux_GetViewport().GetPostEffectComposite().GetPostEffectFromType("FXAA").IsActive());}
     }
   }
   LogNewLine("IU_NATIVE|FXAA restore errors="+errors);
 }
 '''
 # Category count checked separately; function name is not guessed.
 probe=probe.replace('+"|VIDEO rows="+HPL3VR_CategoryCount()','')
 menu=menu.replace('    void HPL3VR_UpdateSMAA()',probe+'\n    void HPL3VR_UpdateSMAA()',1)
 put(G/'script/modules/MenuHandler.hps',menu)

 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in ['00_01_apartment']:
  nonce=uuid.uuid4().hex
  p=next((R/'runtime/maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime');source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+ '\n LogNewLine("HY_RUN|'+nonce+'");'+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]
  idx=source.index('{',source.index('class '));source=source[:idx+1]+'\n void HRSmokeExit(const tString &in name){cScript_RunGlobalFunc("MenuHandler","","IUProbe");LogNewLine("HR_STORY_DONE|'+mapname+'");cEngine_Exit();}\n'+source[idx+1:];put(G/rel,source)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_SmaaIU').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
  timed_out=False
  try:rc=proc.wait(timeout=60)
  except subprocess.TimeoutExpired:timed_out=True;proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_SmaaIU/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/('aa_iv_native_'+mapname+'.log')).write_text(log)
  ok=not timed_out and 'HY_RUN|'+nonce in log and 'HR_STORY_DONE|'+mapname in log and 'IU_NATIVE|FXAA restore errors=0' in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if 'AA_FAIL' in x or 'IU_NATIVE' in x or 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'timed_out':timed_out,'nonce':nonce,'executable_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/'aa_iv_native.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))
