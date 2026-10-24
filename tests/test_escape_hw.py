"""Native escape permission/callback test with supplied normal player state; not the preceding flood cinematic or headset appearance."""
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
 for p in (R/'runtime/entities/soma_vr/guidance').rglob('*'):
  if p.is_file():put(G/'entities/soma_vr/guidance'/p.relative_to(R/'runtime/entities/soma_vr/guidance'),p.read_bytes())
 # Native clone/visibility fixture: runtime capability and hand-pose acknowledgement
 # supplied; actual live DLL bone pose and headset appearance are not tested.
 helper=(R/'runtime/script/helpers/helper_vr_guidance_hr.hps').read_text()
 helper=helper.replace('!cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','false').replace('if(cScript_RunGlobalFunc("VRMESH",""+f,"F"))','if(f==1)').replace('if(cScript_RunGlobalFunc("VRGUIDEH",""+hand,fist ? "F" : "O"))','if(true)').replace('ok=cScript_RunGlobalFunc("VRGUIDEH","","R");','ok=true;')
 put(G/'script/helpers/helper_vr_guidance_hr.hps',helper)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in ['01_03_upsilon_outside']:
  p=next((R/'runtime/maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime');source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]
  source=source.replace('void Update(float dt){','int mlHXUpdateCalls=0; void Update(float dt){mlHXUpdateCalls++;',1)
  fixture=(R/'tests/fixtures/escape_hw.hps').read_text()
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+fixture+source[idx+1:];put(G/rel,source)

  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/('story_'+mapname+'.log')).write_text(log)
  ok='HW_FAIL' not in log and 'HR_STORY_DONE|'+mapname in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if 'HW_' in x or 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/'escape_hx.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))

