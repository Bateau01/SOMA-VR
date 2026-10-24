from pathlib import Path
import subprocess,ctypes,time,json,sys,hashlib,re
R=Path(__file__).resolve().parents[1];G=R.parents[1]/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
edition=sys.argv[1];sources={'steam':Path('D:/SteamLibrary/steamapps/common/SOMA/Soma.exe'),'epic':Path('C:/Program Files/Epic Games/SOMA/Soma.exe'),'gog':Path('C:/Program Files/GOG Galaxy/Games/SOMA/Soma.exe')}
scene=sys.argv[2] if len(sys.argv)>2 else 'pump'
assert edition in sources and (G/'config/pump_lab_init.cfg').exists()
assert not subprocess.run(['powershell','-NoProfile','-Command','Get-Process Soma,Soma_NoSteam,RS_Soma -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True).stdout.strip()
saved={};proc=None
profile='SOMA_VR_RSProbe_'+edition+'_'+str(int(time.time()))
def put(p,data):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode())
try:
 for asset in (R/'runtime').rglob('*.hps'):put(G/asset.relative_to(R/'runtime'),asset.read_bytes())
 put(G/'RS_Soma.exe',sources[edition].read_bytes());put(G/'rs_probe.dll',(R/f'build/roomscale-probe-{"steam" if edition=="steam" else "store"}.dll').read_bytes())
 m=G/'maps/vr_pump_lab/vr_pump_lab.hps';text=m.read_text(encoding='utf-8-sig')
 text=text.replace('// Same charge','bool ok=cScript_RunGlobalFunc("VRROOM","","PROBE");LogNewLine("RS_PROBE_DONE|ok="+ok);cEngine_Exit();return;\n // Same charge',1);put(m,text)
 menu=G/'script/modules/MenuHandler.hps';s=menu.read_text(encoding='utf-8-sig')
 s=s.replace('void GuiMainMenuSelection()','bool mbRSStarted=false;\nvoid GuiMainMenuSelection()',1)
 s=s.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\n if(!mbRSStarted){mbRSStarted=true;cLux_StartNewGame();}',1)
 s=s.replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(menu,s)
 if scene=='theta':
  docs=subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip()
  save=Path(docs)/'My Games/Soma/Main/Default/AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav';assert save.exists()
  put(Path(docs)/('My Games/Soma/'+profile+'/RSProbe/'+save.name),save.read_bytes())
  needle='if(!mbRSStarted){mbRSStarted=true;cLux_StartNewGame();}'
  assert needle in s
  put(menu,s.replace(needle,'if(!mbRSStarted){mbRSStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1))
  mp=G/'maps/chapter02/02_05_theta_inside/02_05_theta_inside.hps';s=mp.read_text(encoding='utf-8-sig')
  pos=s.index('{',s.index('class cScrMap'));s=s[:pos+1]+'\n[nosave] float mfRSClock=0;\n'+s[pos+1:]
  match=re.search(r'void Update\(float (\w+)\)\s*\{',s);assert match
  s=s[:match.end()]+'mfRSClock+='+match[1]+';if(mfRSClock>3){bool ok=cScript_RunGlobalFunc("VRROOM","","PROBE");LogNewLine("RS_PROBE_DONE|ok="+ok);cEngine_Exit();return;}'+s[match.end():];put(mp,s)
 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/rs_probe_user.cfg');put(G/'config/rs_probe_init.cfg',cfg)
 defaults=(G/'config/default_user_settings.cfg').read_text()
 defaults=re.sub(r'<Screen\b[^>]*/>','<Screen Width="960" Height="540" FullScreen="false" Vsync="true" RefreshRate="60" />',defaults)
 defaults=re.sub(r'<Main\b[^>]*/>','<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />',defaults)
 if '<Screen ' not in defaults:defaults+='\n<Screen Width="960" Height="540" FullScreen="false" Vsync="true" RefreshRate="60" />'
 if '<Main ' not in defaults:defaults+='\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />'
 defaults+='\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />'
 put(G/'config/rs_probe_user.cfg',defaults)
 put(G/'hpl3vr.log',b'')
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 start=time.time();proc=subprocess.Popen([str(G/'RS_Soma.exe'),'-user','RSProbe','-cfg','config/rs_probe_init.cfg'],cwd=G,startupinfo=si,creationflags=4|0x4000)
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'RS_Soma.exe','rs_probe.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25);assert 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0
 try:code=proc.wait(timeout=90)
 except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=10)
 docs=subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip()
 hp=Path(docs)/('My Games/Soma/'+profile+'/hpl.log');log=hp.read_text(errors='replace') if hp.exists() else ''
 vr=(G/'hpl3vr.log').read_text(errors='replace');out=R/'audit/roomscale-sweep';label=edition+'_'+scene+'_'+profile.rsplit('_',1)[-1];(out/f'{label}_game.log').write_text(log);(out/f'{label}_vr.log').write_text(vr)
 lines=[s for s in (vr+'\n'+log).splitlines() if 'RS_' in s or ' : ERR ' in s]
 result={'edition':edition,'exe_sha256':hashlib.sha256(sources[edition].read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256((G/'rs_probe.dll').read_bytes()).hexdigest(),'exit':code,'lines':lines,'scope':'isolated native engine, copied save load' if scene=='theta' else 'isolated native engine, direct fixture load'}
 result['scope']+='; read-only synchronous queries at hypothetical grid positions, not applied movement, headset or progression validation'
 result['scene']=scene;result['profile']=profile
 (out/f'{label}_game.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 assert hp.exists() and hp.stat().st_mtime>=start and 'RS_PROBE_DONE|ok=true' in log and 'RS_COMPARE rows=' in vr
 if scene=='theta':assert '02_05_theta_inside' in log and "Loading map 'vr_pump_lab.hpm'" not in log
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,data in reversed(list(saved.items())):
  if data is None:p.unlink(missing_ok=True)
  else:p.write_bytes(data)

