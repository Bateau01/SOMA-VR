"""Isolated real-OpenXR render test. Native menu methods drive transitions;
fixture map/start avoids story setup. No simulated headset/controller poses."""
from pathlib import Path
import subprocess,sys,ctypes,time,json,uuid
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert not subprocess.run(['powershell','-NoProfile','-Command','Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True).stdout.strip()
nonce=uuid.uuid4().hex[:8];out=R/'audit/aa-IV'/nonce;out.mkdir(parents=True);saved={};proc=None

def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 # Replace a leftover old fixture script only inside this run; restore afterward.
 for p in (R/'runtime/maps').rglob('*.hps'):put(G/'maps'/p.relative_to(R/'runtime/maps'),p.read_bytes())
 put(G/'hpl3vr.dll',(R/'build/smaa-test/hpl3vr.dll').read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
 menu=menu.replace('void GuiMainMenuSelection()','bool iuStarted=false;uint iuBoot=0;\n void GuiMainMenuSelection()',1)
 needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n mbVRGuideDismissed=true;if(iuBoot==0)iuBoot=cSystem_GetApplicationTime();if(!iuStarted && cSystem_GetApplicationTime()-iuBoot>7000){iuStarted=true;ClickNewGame();}',1)
 probe='''
 uint iuStart=0;int iuPhase=-1;
 void IUStart(){iuStart=cSystem_GetApplicationTime();LogNewLine("IU_MAP_ENTER");}
 void IUTick(){
  if(iuStart==0)return;uint elapsed=cSystem_GetApplicationTime()-iuStart;
  int phase=int(elapsed/5000);if(phase>8){LogNewLine("IU_VR_DONE");cEngine_Exit();return;}
  if(phase==iuPhase)return;iuPhase=phase;
  bool aaEnabled=phase==2 || phase==3 || phase==4 || phase==5 || phase==6 || phase==8;
  HPL3VR_SetAA(aaEnabled ? 2 : (phase==1 ? 1 : 0));
  mbVRDynamicFoveation=phase==3;
  

  HPL3VR_PublishComfort();
  cScript_RunGlobalFunc("VRCOMFORT","IUTEST",""+phase);
  if(phase==4){cScript_RunGlobalFunc("VRLIFE","","P");SetMenuActive(true);mCurrentGroup=eMainMenuGroup_Options_Video_Display;msSelectedVideoDisplayButton="AA";}
  if(phase==5){mCurrentGroup=eMainMenuGroup_VRSettings;mbVRComfortOpen=true;mlVRComfortCategory=2;mvVRSettingsPages[2]=0;msVRSettingsSelected="ANTI-ALIASING";}
  if(phase==6){mbVRComfortOpen=false;cScript_RunGlobalFunc("VRLIFE","","R");SetMenuActive(false);}
  if(phase==8){cScript_RunGlobalFunc("VRLIFE","","P");SetMenuActive(true);mCurrentGroup=eMainMenuGroup_VRSettings;mbVRComfortOpen=true;mlVRComfortCategory=2;mvVRSettingsPages[2]=1;msVRSettingsSelected="VIGNETTE";}
  LogNewLine("IU_STAGE|"+phase+"|SMAA="+mbVRSMAA+"|DFR="+mbVRDynamicFoveation+"|runtime="+gbHPL3VRRuntimeActive);
 }
 '''
 menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)',probe+'\n    void HPL3VR_UpdateComfort(float dt)',1)
 menu=menu.replace('    void HPL3VR_UpdateComfort(float dt)\n    {','    void HPL3VR_UpdateComfort(float dt)\n    {\n IUTick();',1)
 if '--saved-on' in sys.argv: menu=menu.replace('elapsed/5000','elapsed/4000').replace('mbVRSMAA=phase==2','mbVRSMAA=phase==0 || phase==2')
 put(G/'script/modules/MenuHandler.hps',menu)
 m='''#include "interfaces/Map_Interface.hps"
#include "helpers/helper_map.hps"
#include "helpers/helper_player.hps"
#include "helpers/helper_modules.hps"
class cScrMap : iScrMap {
 void Setup(){} void OnStart(){Player_SetActive(true);Player_SetHealth(100);Player_SetFallDamageActive(false);Player_ChangeStateToNormal();PlayerHands_SetHandModel_Human();}
 void OnEnter(){cScript_RunGlobalFunc("MenuHandler","","IUStart");} void OnLeave(){} void Update(float dt){}
}
'''
 put(G/'maps/chapter01/01_02_upsilon_inside/01_02_upsilon_inside.hps',m)
 profile='SOMA_VR_Smaa_'+nonce
 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/iu_user.cfg').replace('vr_pump_lab.hpm','01_02_upsilon_inside.hpm').replace('maps/vr_pump_lab/','maps/chapter01/01_02_upsilon_inside/');put(G/'config/iu_init.cfg',cfg)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="180" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" FirstGameStart="false" SaveConfig="false" />\n<SOMA_VR_Comfort SMAA="false" DesktopMirror="true" />\n'
 put(G/'config/iu_user.cfg',defaults.replace('SMAA="false"','SMAA="true"') if '--saved-on' in sys.argv else defaults)
 for p in G.glob('iu_eye_*.rgba'):put(p,b'')
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IU','-cfg','config/iu_init.cfg'],cwd=G,creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma.exe','hpl3vr.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25);assert 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0
 print('VR test PID',proc.pid,'evidence',out,flush=True)
 timedout=False
 try:proc.wait(timeout=115)
 except subprocess.TimeoutExpired:timedout=True;proc.terminate();proc.wait(timeout=10)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for src,name in [(docs/'My Games/Soma'/profile/'hpl.log','hpl.log'),(G/'hpl3vr.log','hpl3vr.log')]:
  if src.exists():(out/name).write_bytes(src.read_bytes())
 for p in G.glob('iu_eye_*.rgba'):
  if p.stat().st_size:(out/p.name).write_bytes(p.read_bytes())
  if p not in saved:saved[p]=None
 log=(out/'hpl.log').read_text(errors='replace');vr=(out/'hpl3vr.log').read_text(errors='replace')
 result={'scope':__doc__,'timedout':timedout,'completed':'IU_VR_DONE' in log,'stages':[l for l in log.splitlines() if 'IU_' in l],'render':[l for l in vr.splitlines() if 'IU_' in l or 'SMAA ' in l or 'DFR STATUS' in l],'script_errors':[l for l in log.splitlines() if ' : ERR ' in l]}
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)

