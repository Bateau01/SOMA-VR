"""Native menu rendering; forces welcome page only, not a VR/input validation."""
from pathlib import Path
import subprocess,sys,time,json,uuid
from PIL import Image
from inject_capture_hy import inject
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);out=R/'audit/welcome-IS'/uuid.uuid4().hex[:8];out.mkdir(parents=True)
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
 needle='bool HPL3VR_DrawWelcome()\n    {';assert needle in menu
 menu=menu.replace('bool HPL3VR_DrawWelcome()','uint welcomeVisualStart=0;\n bool HPL3VR_DrawWelcome()',1)
 menu=menu.replace('if(!gbHPL3VRRuntimeActive || !mbMainMenuActive || mbPremenuActive || mfMainAlpha<0.99f || mbVRGuideDismissed)', 'if(!mbMainMenuActive || mbPremenuActive || mfMainAlpha<0.99f || mbVRGuideDismissed)',1)
 menu=menu.replace(needle,needle+'\n mlVRWelcomePage=2; if(welcomeVisualStart==0)welcomeVisualStart=cSystem_GetApplicationTime();\n if(cSystem_GetApplicationTime()-welcomeVisualStart>14000){LogNewLine("WELCOME_VISUAL_DONE");cEngine_Exit();}',1)
 put(G/'script/modules/MenuHandler.hps',menu)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for width,height in [(1280,720),(1280,536)]:
  nonce=uuid.uuid4().hex[:8];profile='SOMA_VR_Welcome_'+nonce
  defaults=(G/'config/default_user_settings.cfg').read_text()+f'\n<Screen Width="{width}" Height="{height}" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n'
  put(G/'config/welcome_visual_user.cfg',defaults)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/welcome_visual_user.cfg');put(G/'config/welcome_visual_init.cfg',cfg)
  start=time.time()
  for p in G.glob('hy_frame_*.ppm'):
   if p not in saved:saved[p]=p.read_bytes()
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','WelcomeVisual','-cfg','config/welcome_visual_init.cfg'],cwd=G,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
  time.sleep(2);inject(proc.pid,R/'tests/capture_swap_hy.dll')
  timedout=False
  try:proc.wait(timeout=35)
  except subprocess.TimeoutExpired:timedout=True;proc.terminate();proc.wait(timeout=10)
  log=(docs/'My Games/Soma'/profile/'hpl.log').read_text(errors='replace');(out/f'{height}.log').write_text(log)
  frames=[]
  for p in G.glob('hy_frame_*.ppm'):
   if p.stat().st_mtime>=start:
    dst=out/f'{height}_{p.stem}.png';Image.open(p).save(dst);frames.append(str(dst))
    if p not in saved:saved[p]=None
  result={'size':[width,height],'completed':not timedout and 'WELCOME_VISUAL_DONE' in log and ' : ERR ' not in log,'frames':frames,'errors':list(dict.fromkeys(s for s in log.splitlines() if 'ERR' in s or 'welcome_body' in s))};results.append(result);print(json.dumps(result),flush=True)
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 (out/'result.json').write_text(json.dumps({'scope':__doc__,'results':results,'restored':all(p.read_bytes()==b if b is not None else not p.exists() for p,b in saved.items())},indent=2))
