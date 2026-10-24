"""Native menu render capture with VR label/welcome visibility substituted only during draw; no headset proof."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None
out=R/'docs/v109-evidence';savedImages=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 source=(R/'runtime/script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 for welcome in ([True] if "--hold" in sys.argv else [True,False]):
  for w,h in ([(1280,720)] if "--hold" in sys.argv else [(1280,720),(3440,1440)]):
   image=out/f'menu_{w}_{h}_{"welcome" if welcome else "footer"}.png'
   menu=source.replace('return gbHPL3VRRuntimeActive && mbMainMenuActive','return mbMainMenuActive').replace('void GuiMainMenuSelection()','int mlHRCaptureFrame=0;\n void GuiMainMenuSelection()',1)
   needle='        HPL3VR_DrawVersion();\n        if(HPL3VR_DrawWelcome())return;';assert needle in menu
   replace='''        mlHRCaptureFrame++;
        if(mlHRCaptureFrame==120)cLux_SaveScreenshotToFile(tWString("IMAGE"));
        if(mlHRCaptureFrame==125){LogNewLine("HR_MENU_CAPTURE_DONE");cEngine_Exit();}
        bool originalVR=gbHPL3VRRuntimeActive;gbHPL3VRRuntimeActive=true;
        mbVRGuideDismissed=DISMISSED;
        HPL3VR_DrawVersion();bool welcomeVisible=HPL3VR_DrawWelcome();
        gbHPL3VRRuntimeActive=originalVR;if(welcomeVisible)return;'''.replace('IMAGE',image.as_posix()).replace('DISMISSED','false' if welcome else 'true')
   
   if '--hold' in sys.argv:
    replace=replace.replace('if(mlHRCaptureFrame==125)', 'if(mlHRCaptureFrame==2000000000)').replace('mbVRGuideDismissed=false;', 'if(mlHRCaptureFrame==1)mbVRGuideDismissed=false;')
   menu=menu.replace(needle,replace,1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
   defaults=(G/'config/default_user_settings.cfg').read_text()+f'\n<Screen Width="{w}" Height="{h}" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_menu_user.cfg',defaults)
   cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',f'SOMA_VR_HR_Menu_{w}_{h}').replace('config/default_user_settings.cfg','config/hr_menu_user.cfg');put(G/'config/hr_menu_init.cfg',cfg)
   si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=1 if "--hold" in sys.argv else 0
   proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRMenu','-cfg','config/hr_menu_init.cfg'],cwd=G,startupinfo=si)
   try:rc=proc.wait(timeout=180 if "--hold" in sys.argv else 60)
   except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
   docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip());log=(docs/f'My Games/Soma/SOMA_VR_HR_Menu_{w}_{h}/hpl.log').read_text(errors='replace');(out/(image.stem+'.log')).write_text(log)
   result={'width':w,'height':h,'welcome':welcome,'exit':rc,'image':str(image),'exists':image.exists(),'errors':[x for x in log.splitlines() if ' : ERR ' in x or 'FATAL' in x]};savedImages.append(result);print(json.dumps(result),flush=True);(out/'menu_capture_hr.json').write_text(json.dumps(savedImages,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['exists'] and not x['errors'] for x in savedImages))

