"""Native authored three-button sequence via real Prop_MovingButton permission/OnInteract. Panel-on callback substitutes preceding story; no tracked contact test."""
from pathlib import Path
import subprocess,sys,re,json,hashlib
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 moving=(R/'runtime/script/props/Prop_MovingButton.hps').read_text()
 moving=moving.replace('bool CanInteract(',"""
 void _Global_HRPress(){iPhysicsBody@ b=mBaseObj.GetMainBody();bool permitted=CanInteract(0,b);bool accepted=permitted && OnInteract(0,b,b.GetWorldPosition(),"");LogNewLine("HR_REAL_PRESS|"+mBaseObj.GetName()+"|accepted="+accepted);}
 bool CanInteract(""",1);put(G/'script/props/Prop_MovingButton.hps',moving)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in ['01_02_upsilon_inside']:
  p=Path(r'D:/SteamLibrary/steamapps/common/SOMA/maps/chapter01/01_02_upsilon_inside/01_02_upsilon_inside.hps');rel=Path('maps/chapter01/01_02_upsilon_inside/01_02_upsilon_inside.hps');source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_start",4,"HRStart");'+source[m.end():]
  idx=source.index('{',source.index('class '));source=source[:idx+1]+r"""
 void HRStart(const tString &in name){OnChange_ControlRoomButton("ControlRoomButton",1);cScript_RunGlobalFunc("ControlPanelKnob_1","","_Global_HRPress");Map_AddTimer("hr_second",4.55f,"HRSecond");}
 void HRSecond(const tString &in name){cScript_RunGlobalFunc("ControlPanelKnob_2","","_Global_HRPress");Map_AddTimer("hr_third",4.55f,"HRThird");}
 void HRThird(const tString &in name){cScript_RunGlobalFunc("ControlPanelKnob_3","","_Global_HRPress");Map_AddTimer("hr_done",6,"HRSmokeExit");}
 void HRSmokeExit(const tString &in name){LogNewLine("HR_POWER_OUTCOME|knobs="+mlKnobsTurned+"|power="+mbPowerOn_1);LogNewLine("HR_STORY_DONE|01_02_upsilon_inside");cEngine_Exit();}
 """+source[idx+1:];put(G/rel,source)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/('story_'+mapname+'.log')).write_text(log)
  ok='HR_POWER_OUTCOME|knobs=3|power=true' in log and 'HR_STORY_DONE|'+mapname in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if ('HR_STORY' in x or 'HR_REAL_PRESS' in x or 'HR_POWER_OUTCOME' in x) or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/'power_sequence_hr.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))
