"""Native map initialization/compile smoke tests. No VR runtime or completed story sequence."""
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
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in ['00_03_laboratory']:
  matches=list((R/'runtime/maps').rglob(mapname+'.hps'));p=matches[0] if matches else next((G/'maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime') if matches else p.relative_to(G);source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]
  idx=source.index('{',source.index('class '));source=source[:idx+1]+'\n void HRSmokeExit(const tString &in name){LogNewLine("HR_STORY_DONE|'+mapname+'");  cGuiSet@ set=cGui_CreateSet("HSTouchProbe",null);set.SetVirtualSize(cVector2f(512),-1000,1000,cVector2f(0)); cImGui@ gui=cGui_CreateImGui("HSTouchProbe",set); cImGuiButtonData data;data.mbUseBackgroundGfx=false;data.mbUseInFocusGfx=false;data.mbUseTriggeredGfx=false; data.mFont.SetFile("sansation.fnt");data.mFont.mvSize=cVector2f(16); for(int test=0;test<6;test++){  gui.ClearStates();int accepted=0;bool pending=false;  for(int frame=0;frame<5;frame++){   gui.Begin(1.0f/60.0f);gui.SetShowMouse(true);   bool down=frame==1 || frame==2;bool edge=frame==1 || (test>=3 && pending && down);   cVector2f pos(110,110);if((test==1 || test==3 || test==5) && frame==1)pos=cVector2f(30,30);   if((test==2 || test==4) && frame==2)pos=cVector2f(230,110);   gui.SendMouseVirtualPosition(pos,cVector2f(1));gui.SendMouseVirtualPosition(pos,cVector2f(1));   gui.SendAction(eImGuiAction_MouseLeft,down,edge);   bool hit=gui.DoButton("ONE",tWString(""),data,cVector3f(100,100,1),cVector2f(80,40));   bool other=gui.DoButton("TWO",tWString(""),data,cVector3f(220,100,1),cVector2f(80,40));   if(hit)accepted++;LogNewLine("HS_WIDGET|test="+test+"|frame="+frame+"|accepted="+hit+"|other="+other);   bool custom=false;if(test==5)custom=gui.ActionTriggered(eImGuiAction_MouseLeft);   pending=gui.ActionTriggered(eImGuiAction_MouseLeft,true);   LogNewLine("HS_WIDGET_CONSUMED|test="+test+"|frame="+frame+"|pending="+pending+"|custom="+custom);   gui.End();  }  LogNewLine("HS_WIDGET_TOTAL|test="+test+"|accepted="+accepted); } cGui_DestroyImGui(gui);cGui_DestroySet(set);  cEngine_Exit();}\n'+source[idx+1:];put(G/rel,source)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/('widget_'+mapname+'.log')).write_text(log)
  widget_ok=all(('HS_WIDGET_TOTAL|test='+str(i)+'|accepted='+str(n)) in log for i,n in enumerate([1,0,1,1,1,0])) and '|other=true' not in log
  ok=widget_ok and 'HR_STORY_DONE|'+mapname in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/'widget_probe_hs.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))
