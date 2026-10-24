"""Native escape permission/callback test with supplied normal player state; not the preceding flood cinematic or headset appearance."""
from pathlib import Path
import subprocess,sys,re,json,hashlib,time,uuid
from inject_capture_hy import inject
from PIL import Image
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
 if '--depth-probe' in sys.argv:
  put(G/'entities/soma_vr/guidance/guide.mat',(R/'runtime/entities/soma_vr/guidance/guide.mat').read_text().replace('DepthTest="true"','DepthTest="false"'))
 # Native clone/visibility fixture: runtime capability and hand-pose acknowledgement
 # supplied; actual live DLL bone pose and headset appearance are not tested.
 helper=(R/'runtime/script/helpers/helper_vr_guidance_hr.hps').read_text()
 helper=helper.replace('!cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','false').replace('if(cScript_RunGlobalFunc("VRMESH",""+f,"F"))','if(f==1)').replace('if(cScript_RunGlobalFunc("VRGUIDEH",""+hand,fist ? "F" : "O"))','if(true)').replace('ok=cScript_RunGlobalFunc("VRGUIDEH","","R");','ok=true;')
 # Geometry-only rendering fixture: remove skinning rather than pretend a
 # runtime bone-pose callback ran. This does not certify the tracked hand rig.
 import xml.etree.ElementTree as ET
 ns='{http://www.collada.org/2005/11/COLLADASchema}'; ET.register_namespace('',ns[1:-1])
 tree=ET.parse(R/'runtime/entities/soma_vr/s26f/hand_diving_right.dae')
 root=tree.getroot(); import copy; bindings={c.get('url')[1:]:copy.deepcopy(c.find(ns+'bind_material')) for c in root.findall('.//'+ns+'instance_controller')}; skins={c.get('id'):c.find(ns+'skin').get('source')[1:] for c in root.findall(ns+'library_controllers/'+ns+'controller')}; scene=root.find(ns+'library_visual_scenes/'+ns+'visual_scene')
 root.remove(root.find(ns+'library_controllers'))
 scene.clear();scene.set('id','Scene')
 for geo in root.findall(ns+'library_geometries/'+ns+'geometry'):
  node=ET.SubElement(scene,ns+'node',{'id':geo.get('id')+'Node','name':geo.get('id')+'Node','type':'NODE'})
  inst=ET.SubElement(node,ns+'instance_geometry',{'url':'#'+geo.get('id')})
  for skin,gid in skins.items():
   if gid==geo.get('id') and skin in bindings:inst.append(bindings[skin])
 put(G/'entities/soma_vr/guidance/hz_static_hand.dae',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 helper=helper.replace('mGuide.mpMesh.GetBoneStateRoot().UpdateMatrix(true);','')
 helper=helper.replace('"entities/soma_vr/s26f/hand_"+names[family]+"_"+side+".dae"','"entities/soma_vr/guidance/hz_static_hand.dae"')
 put(G/'script/helpers/helper_vr_guidance_hr.hps',helper)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 usercfg=docs/'My Games/Soma/SOMA_VR_HR_Story/HRStory_user_settings.cfg'
 put(usercfg,usercfg.read_text().replace('<Main ', '<Main DebugMode="true" ForceCacheLoadingAndSkipSaving="false" '))
 for mapname in ['01_03_upsilon_outside']:
  nonce=uuid.uuid4().hex
  start=time.time()
  p=next((R/'runtime/maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime');source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HY_RUN|'+nonce+'");'+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]
  source=source.replace('bool bDoIntro = true;', 'bool bDoIntro = false;')
  source=source.replace('void Update(float dt){','int mlHXUpdateCalls=0; void Update(float dt){mlHXUpdateCalls++; HYCamera();',1)
  fixture=(R/'tests/fixtures/escape_visual_hy.hps').read_text()
  fixture=fixture.replace('if(!mbHYCamera)return;', 'if(!mbHYCamera)return;Player_ChangeStateToNormal();Effect_Fade_In(0);')
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+fixture+source[idx+1:];put(G/rel,source)

  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=1
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
  time.sleep(2);inject(proc.pid,R/'tests/capture_swap_hy.dll')
  timed_out=False
  try:rc=proc.wait(timeout=55)
  except subprocess.TimeoutExpired:timed_out=True;proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';out.mkdir(parents=True,exist_ok=True);(out/('story_'+mapname+'.log')).write_text(log)
  ok=not timed_out and 'HY_RUN|'+nonce in log and 'HY_CAPTURE_REQUEST' in log and 'HR_STORY_DONE|'+mapname in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  frames=[p for p in G.glob('hy_frame_*.ppm') if p.stat().st_mtime>=start]
  result_dir=out/('escape_visual_'+nonce);result_dir.mkdir()
  for frame in frames:
   Image.open(frame).verify()
   (result_dir/frame.name).write_bytes(frame.read_bytes())
  (result_dir/'native.log').write_text(log)
  ok=ok and bool(frames) and 'Exception from module' not in log and 'HZ_BOUNDS|' in log and "Couldn't load mesh 'entities/soma_vr/guidance/hz_static_hand" not in log
  lines=[x for x in log.splitlines() if 'HW_' in x or 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'execution_completed':ok,'visual_alignment':'pending pixel inspection','exit':rc,'timed_out':timed_out,'nonce':nonce,'scope':__doc__,'lines':lines};results.append(result);(result_dir/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
  (out/'escape_visual_hy.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['execution_completed'] for x in results))



