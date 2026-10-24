"""Native menu page routing/restart with synthetic button activations; not physical controller input."""
from pathlib import Path
import subprocess,sys,time,json,uuid
from PIL import Image
from inject_capture_hy import inject
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);out=R/'audit/welcome-navigation-IS'/uuid.uuid4().hex[:8];out.mkdir(parents=True)
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 put(G/'graphics/soma_vr/welcome_body.png',(R/'runtime/graphics/soma_vr/welcome_body.png').read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 menu=menu.replace('return gbHPL3VRRuntimeActive && mbMainMenuActive && !mbPremenuActive && !mbVRGuideDismissed;', 'return mbMainMenuActive && !mbPremenuActive && !mbVRGuideDismissed;')
 menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
 menu=menu.replace('if(!gbHPL3VRRuntimeActive || !mbMainMenuActive || mbPremenuActive || mfMainAlpha<0.99f || mbVRGuideDismissed)', 'if(!mbMainMenuActive || mbPremenuActive || mfMainAlpha<0.99f || mbVRGuideDismissed)',1)
 menu=menu.replace('bool HPL3VR_DrawWelcome()', 'int testStep=0;uint testNext=0;bool testDone=false;\n bool HPL3VR_DrawWelcome()',1)
 needle='bool cancel=ImGui_ActionTriggered(eImGuiAction_Cancel,true);'
 assert needle in menu
 menu=menu.replace(needle,needle+"\n leftClick=false;rightClick=false;cancel=false;\n if(cSystem_GetApplicationTime()>testNext){testNext=cSystem_GetApplicationTime()+350;testStep++;rightClick=(testStep==1||testStep==2||testStep==5||testStep==6||testStep==7);leftClick=testStep==3;cancel=testStep==4;}",1)
 needle='ImGui_SetTransCategory(cat);return true;'
 assert needle in menu
 start=menu.index('bool HPL3VR_DrawWelcome()');end=menu.index('void HPL3VR_DrawVersion()',start)
 chunk=menu[start:end]
 chunk=chunk.replace(needle,'LogNewLine("WELCOME_NAV|step="+testStep+"|page="+mlVRWelcomePage+"|dismissed="+mbVRGuideDismissed);\n'+needle,1)
 menu=menu[:start]+chunk+menu[end:]
 needle='void GuiMainMenuSelection()\n\t{'
 assert needle in menu
 menu=menu.replace(needle,needle+'\n if(mbVRGuideDismissed && !testDone){testDone=true;LogNewLine("WELCOME_NAV_DONE|pending="+HPL3VR_WelcomePending());cEngine_Exit();}',1)
 put(G/'script/modules/MenuHandler.hps',menu)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 profile='SOMA_VR_WelcomeNav_'+out.name
 for run in range(2):
  width,height=1280,720
  nonce=str(run)
  defaults=(G/'config/default_user_settings.cfg').read_text()+f'\n<Screen Width="{width}" Height="{height}" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n<SOMA_VR WelcomeVersion="99999" />\n'
  put(G/'config/welcome_visual_user.cfg',defaults)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/welcome_visual_user.cfg');put(G/'config/welcome_visual_init.cfg',cfg)
  start=time.time()
  for p in G.glob('hy_frame_*.ppm'):
   if p not in saved:saved[p]=p.read_bytes()
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','WelcomeVisual','-cfg','config/welcome_visual_init.cfg'],cwd=G,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
  time.sleep(2)
  timedout=False
  try:proc.wait(timeout=35)
  except subprocess.TimeoutExpired:timedout=True;proc.terminate();proc.wait(timeout=10)
  log=(docs/'My Games/Soma'/profile/'hpl.log').read_text(errors='replace');(out/f'run{run}.log').write_text(log)
  frames=[]
  for p in G.glob('hy_frame_*.ppm'):
   if p.stat().st_mtime>=start:
    dst=out/f'{height}_{p.stem}.png';Image.open(p).save(dst);frames.append(str(dst))
    if p not in saved:saved[p]=None
  result={'size':[width,height],'completed':not timedout and 'WELCOME_NAV_DONE|pending=false' in log and ' : ERR ' not in log and all(('WELCOME_NAV|step='+str(i)+'|page='+str(pg)+'|dismissed='+('true' if i==7 else 'false')) in log for i,pg in [(1,1),(2,2),(3,1),(4,0),(5,1),(6,2),(7,2)]),'run':run,'states':list(dict.fromkeys(x for x in log.splitlines() if 'WELCOME_NAV' in x)),'errors':list(dict.fromkeys(s for s in log.splitlines() if 'ERR' in s or 'welcome_body' in s))};results.append(result);print(json.dumps(result),flush=True)
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 (out/'result.json').write_text(json.dumps({'scope':__doc__,'results':results,'restored':all(p.read_bytes()==b if b is not None else not p.exists() for p,b in saved.items())},indent=2))
