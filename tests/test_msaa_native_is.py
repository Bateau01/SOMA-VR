"""Native window-MSAA/scene-FBO observation, no VR or production render changes."""
from pathlib import Path
import subprocess,ctypes,time,json,sys,hashlib,uuid
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);edition=sys.argv[2];samples=int(sys.argv[3]);fxaa=sys.argv[4] if len(sys.argv)>4 else 'Off'
sources={'steam':Path('D:/SteamLibrary/steamapps/common/SOMA/Soma.exe'),'epic':Path('C:/Program Files/Epic Games/SOMA/Soma.exe'),'gog':Path('C:/Program Files/GOG Galaxy/Games/SOMA/Soma.exe')}
assert not subprocess.run(['powershell','-NoProfile','-Command','Get-Process Soma,RS_Soma -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True).stdout.strip()
saved={};proc=None;out=R/'audit/msaa-IS'/(edition+'_'+str(samples)+'_'+fxaa+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
def put(p,data):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 put(G/'RS_Soma.exe',sources[edition].read_bytes());put(G/'msaa_probe.dll',(R/'build/msaa_observer_is.dll').read_bytes())
 put(G/'msaa_probe.txt','');put(G/'msaa_ready.txt','');put(G/'msaa_request.txt',str(samples))
 put(G/'maps/vr_pump_lab/vr_pump_lab.hps','''#include "interfaces/Map_Interface.hps"
#include "helpers/helper_map.hps"
#include "helpers/helper_effects.hps"
class cScrMap:iScrMap{float age=0;void Setup(){}void OnEnter(){}void OnLeave(){}void OnStart(){}void Update(float dt){age+=dt;Effect_Fade_In(0);if(age>20){LogNewLine("MSAA_SCENE_DONE");cEngine_Exit();}}}
''')
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace('void GuiMainMenuSelection()','bool testStarted=false;\nvoid GuiMainMenuSelection()',1).replace(needle,needle+'\nif(!testStarted){testStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 profile='SOMA_VR_MSAA_'+out.name
 defaults=(G/'config/default_user_settings.cfg').read_text()+f'\n<Screen Width="960" Height="540" FullScreen="false" Vsync="true" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n<Graphics AntiAliasing="{fxaa}" />';put(G/'config/msaa_user.cfg',defaults)
 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/msaa_user.cfg');put(G/'config/msaa_init.cfg',cfg)
 proc=subprocess.Popen([str(G/'RS_Soma.exe'),'-user','MSAA','-cfg','config/msaa_init.cfg'],cwd=G,creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'RS_Soma.exe','msaa_probe.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25);assert 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 for i in range(50):
  if (G/'msaa_ready.txt').read_text()=='1 1':break
  time.sleep(.1)
 assert (G/'msaa_ready.txt').read_text()=='1 1'
 resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0
 try:proc.wait(timeout=55)
 except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip());log=(docs/'My Games/Soma'/profile/'hpl.log').read_text(errors='replace');(out/'native.log').write_text(log)
 probe=(G/'msaa_probe.txt').read_text();(out/'probe.txt').write_text(probe)
 result={'scope':__doc__,'edition':edition,'samples_requested':samples,'fxaa':fxaa,'exe_sha256':hashlib.sha256(sources[edition].read_bytes()).hexdigest(),'completed':'MSAA_SCENE_DONE' in log and ' : ERR ' not in log,'probe':probe};(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 (out/'restoration.json').write_text(json.dumps({'restored':all(p.read_bytes()==b if b is not None else not p.exists() for p,b in saved.items())}))
