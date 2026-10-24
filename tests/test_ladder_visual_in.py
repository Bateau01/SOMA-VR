"""Native rendered placement fixture. Supplies Normal state, target active, VR capability and open bind pose; does not prove story authorization or headset output."""
from pathlib import Path
import subprocess,sys,re,json,hashlib,time,uuid,xml.etree.ElementTree as ET
import numpy as np
from inject_capture_hy import inject
from PIL import Image
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/maps').rglob('*.hps'):put(G/'maps'/p.relative_to(R/'runtime/maps'),p.read_bytes())
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 for p in (R/'runtime/entities/soma_vr/guidance').rglob('*'):
  if p.is_file():put(G/'entities/soma_vr/guidance'/p.relative_to(R/'runtime/entities/soma_vr/guidance'),p.read_bytes())
 # Native clone/visibility fixture: runtime capability and hand-pose acknowledgement
 # supplied; actual live DLL bone pose and headset appearance are not tested.
 helper=(R/'runtime/script/helpers/helper_vr_guidance_hr.hps').read_text()
 helper=helper.replace('!cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','false').replace('if(cScript_RunGlobalFunc("VRMESH",""+f,"F"))','if(f==1)').replace('if(cScript_RunGlobalFunc("VRGUIDEH",""+hand,pointing ? "P" : (fist ? "F" : "O")))','if(true)').replace('ok=cScript_RunGlobalFunc("VRGUIDEH","","R");','ok=true;')
 if '--no-guides' in sys.argv:helper=helper.replace('if(!cLux_GetUserConfig().GetBool','if(true || !cLux_GetUserConfig().GetBool')
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
 h=(R/'runtime/script/helpers/helper_vr_traversal_hy.hps').read_text().replace('!cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','false')
 if '--lift' in sys.argv:h=h.replace('.048f','.348f')
 put(G/'script/helpers/helper_vr_traversal_hy.hps',h)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 usercfg=docs/'My Games/Soma/SOMA_VR_HR_Story/HRStory_user_settings.cfg'
 if usercfg.exists():put(usercfg,usercfg.read_text().replace('<Main ', '<Main DebugMode="true" ForceCacheLoadingAndSkipSaving="false" '))
 if '--load-phi' in sys.argv:
  put(G/'config/hr_story_user.cfg',defaults.replace('ShowMenu="false"','ShowMenu="true"'))
  usercfg=docs/'My Games/Soma/SOMA_VR_HR_Story/HRStory_user_settings.cfg'
  put(usercfg,usercfg.read_text().replace('ShowMenu="false"','ShowMenu="true"'))
  save=next((docs/'My Games/Soma/Main').rglob('AutoSave_05-01-phi-inside_2021_1_5_17_11_51_0.sav'))
  put(docs/'My Games/Soma/SOMA_VR_HR_Story/HRStory'/save.name,save.read_bytes())
  put(G/'script/modules/MenuHandler.hps',menu.replace('if(sKeyPress.length()!=0)', 'if(true)').replace('ClickNewGame();}', 'StartSavedGameLoad(tWString("'+save.name+'"));}',1))

 inventory=[]
 current=json.loads((R/'docs/v109-evidence/ladder_rails_in.json').read_text())
 for item in json.loads((R/'docs/v109-evidence/ladder_coverage_hy.json').read_text()):
  if not item['status'].startswith('candidate'):continue
  for point in item['points']:
   update=next((x for x in current if x['map']==item['map'] and x['target']==item['target'] and 'new' in x),None)
   if point['end']=='top' and update:point={**point,'local_contact':update['new'],'local_normal':update['normal']}
   inventory.append({**item,**point})
 if len(sys.argv)>2 and not sys.argv[2].startswith('--'):inventory=[x for x in inventory if x['target']==sys.argv[2] and (len(sys.argv)<4 or x['map']==sys.argv[3])]
 if len(sys.argv)>4 and sys.argv[4] in ['bottom','top']:inventory=[x for x in inventory if x['end']==sys.argv[4]]
 assert inventory,'No matching scenarios; refusing empty pass'
 for entry in inventory:
  mapname=entry['map']; target=entry['target']
  nonce=uuid.uuid4().hex
  start=time.time()
  p=next((R/'runtime/maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime');source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HY_RUN|'+nonce+'");'+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]
  source=source.replace('bool bDoIntro = true;', 'bool bDoIntro = false;')
  # Placement-only direct loads lack normal saveable story state. Never ship
  # this substitution; lifecycle/save compatibility is not asserted here.
  if '--placement-only' in sys.argv:
   source=source.replace('CheckPoint_Setup();','').replace('Game_AutoSave();','')
   if mapname=='03_01_omicron_outside':source=source.replace('SetupWakeUp(!cLux_ScriptDebugOn());','SetupWakeUp(false);')
  clean=re.sub(r'/\*.*?\*/',lambda m:' '*len(m[0]),source,flags=re.S)
  um=re.search(r'void Update\(float \w+\)\s*\{',clean);assert um
  source=source[:um.end()]+' HYCamera();'+source[um.end():]
  areas=ET.parse(G/rel.with_suffix('.hpm_Area'))
  area=next(a for a in areas.iter('Area') if a.get('Name')==target)
  pos=np.fromstring(area.get('WorldPos'),sep=' ');ax,ay,az=np.fromstring(area.get('Rotation'),sep=' ');cx,sx=np.cos(ax),np.sin(ax);cy,sy=np.cos(ay),np.sin(ay);cz,sz=np.cos(az),np.sin(az)
  rot=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);yaw=float(np.arctan2(rot[0,2],rot[2,2]))
  contact=pos+rot@np.array(entry['local_contact']);feet=contact+rot@np.array([0,-.4 if entry['end']=='top' else -.95,-1.0 if entry['end']=='top' else 1.15])
  if entry['end']=='top':yaw+=float(np.pi)
  v=','.join(str(float(x))+'f' for x in feet)
  fixture='\n bool mbHYCamera=false;\n void HYCamera(){if(!mbHYCamera)return;\n cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(FEET),false);\n cLux_GetPlayer().GetCharacterBody().SetYaw(YAWf);\n cLux_GetPlayer().GetCamera().SetYaw(YAWf);\n cLux_GetPlayer().GetCamera().SetPitch(-.45f);\n }\n void HRSmokeExit(const tString &in timer){\n Player_ChangeStateToNormal();Effect_Fade_In(0);Entity_SetActive("TARGET",true);\n mbHYCamera=true;HYCamera();Map_AddTimer("hy_capture",3,"HYCapture");\n }\n void HYCapture(const tString &in timer){cMatrixf test=VRTraversalFrameHY(cVector3f(0),cVector3f(1,0,0),cVector3f(0,1,0));cVector3f dir=cMath_MatrixMul(test,cVector3f(0,-1,0))-test.GetTranslation();LogNewLine("HY_AXIS|"+dir.x+","+dir.y+","+dir.z);for(uint i=0;i<mVRTraversalHY.mvPoints.length();i++){cVRTraversalPointHY@ p=mVRTraversalHY.mvPoints[i];cLuxArea@ a=cLux_ToArea(Map_GetEntity(p.msTarget));LogNewLine("HY_POINT|"+i+"|dist="+p.DistanceToCamera()+"|active="+a.IsActive()+"|disabled="+a.GetInteractionDisabled()+"|interacted="+a.IsInteractedWith()+"|can="+a.CanInteract(0,a.GetAreaBody())+"|mesh="+p.mHand.mGuide.Live()+"|state="+cLux_GetPlayer().GetCurrentStateId());}HYCheck(HYVisible(),"visible via ordinary map update before forced regression");LogNewLine("HY_CAPTURE_REQUEST");Map_AddTimer("hy_finish",6,"HYFinish");}\n void HYFinish(const tString &in timer){LogNewLine("HR_STORY_DONE|MAP");cEngine_Exit();}\n'.replace('FEET',v).replace('YAW',str(yaw)).replace('TARGET',target).replace('MAP',mapname)
  if entry['end']=='top':fixture=fixture.replace('SetPitch(-.45f)','SetPitch(-.9f)')
  doors={'01_01_upsilon_awake': {'ClimbArea_1': 'exithatch'}, '01_02_upsilon_inside': {'HatchClimb_2': 'hatch_1'}, '02_07_theta_exit': {'ClimbArea_1': 'hatch_4', 'ClimbArea_2': 'hatch_3', 'ClimbArea_3': 'hatch_2', 'ClimbArea_4': 'hatch_1'}}
  door=doors.get(mapname,{}).get(target)
  if door:fixture=fixture.replace('mbHYCamera=true;', 'SlideDoor_SetClosed("'+door+'",false,true);mbHYCamera=true;')
  if '--native-deploy' in sys.argv:
   fixture=fixture.replace('Entity_SetActive("'+target+'",true);','')
   if target=='CrewQuarterLadderArea':
    fixture=fixture.replace('mbHYCamera=true;', 'HYUpdate();HYCheck(!HYVisible(),"raised ladder guide hidden");OnChangeLadderWheel("LadderWheel",1);mbHYCamera=true;').replace('Map_AddTimer("hy_capture",3,','Map_AddTimer("hy_capture",6,')
    fixture=fixture.replace('LogNewLine("HY_CAPTURE_REQUEST");','cVector3f bp=cLux_ToProp(Map_GetEntity("CrewQuarterLadder")).GetMainBody().GetLocalMatrix().GetTranslation();LogNewLine("HY_BODY|"+bp.x+","+bp.y+","+bp.z);LogNewLine("HY_CAPTURE_REQUEST");')
   elif target=='Start_Ladder':
    fixture=fixture.replace('mbHYCamera=true;', 'HYUpdate();HYCheck(!HYVisible(),"retracted ladder guide hidden");DropLadder("");Map_AddTimer("hy_enable",4,"TimerEnableLadder");mbHYCamera=true;').replace('Map_AddTimer("hy_capture",3,','Map_AddTimer("hy_capture",6,')
  if '--dispose-first' in sys.argv:fixture=fixture.replace('cEngine_Exit();','mVRTraversalHY.Dispose();cEngine_Exit();')
  if '--lock-presentation' in sys.argv:fixture=fixture.replace('if(!mbHYCamera)return;', 'if(!mbHYCamera)return;Player_ChangeStateToNormal();Effect_Fade_In(0);')
  if '--force-active' in sys.argv:fixture=fixture.replace('if(!mbHYCamera)return;', 'if(!mbHYCamera)return;Entity_SetActive("'+target+'",true);')
  if '--regression' in sys.argv:
   check=r' void HYCheck(bool ok,const tString &in label){LogNewLine((ok ? "HY_PASS|" : "HY_FAIL|")+label);} bool HYVisible(){for(uint i=0;i<mVRTraversalHY.mvPoints.length();i++){if(mVRTraversalHY.mvPoints[i].msTarget=="TARGET" && mVRTraversalHY.mvPoints[i].mHand.mGuide.Live() && mVRTraversalHY.mvPoints[i].mHand.mGuide.mpMesh.IsVisible())return true;}return false;} void HYUpdate(){mVRTraversalHY.mfPoll=0;mVRTraversalHY.Update(.2f);} void HYRegression(){if(cLux_GetPlayer().GetCurrentStateId()!=ePlayerState_Normal){HYUpdate();HYCheck(!HYVisible(),"scripted state hides guide");Player_ChangeStateToNormal();HYCamera();}cLuxArea@ aa=cLux_ToArea(Map_GetEntity("TARGET"));LogNewLine("HY_FINAL_STATE|state="+cLux_GetPlayer().GetCurrentStateId()+"|active="+aa.IsActive()+"|disabled="+aa.GetInteractionDisabled()+"|interacted="+aa.IsInteractedWith()+"|can="+aa.CanInteract(0,aa.GetAreaBody()));HYUpdate();HYCheck(HYVisible(),"eligible target visible");Entity_SetInteractionDisabled("TARGET",true);HYUpdate();HYCheck(!HYVisible(),"disabled hidden");Entity_SetInteractionDisabled("TARGET",false);HYUpdate();HYCheck(HYVisible(),"reenabled recovers");Entity_SetActive("TARGET",false);HYUpdate();HYCheck(!HYVisible(),"inactive hidden");Entity_SetActive("TARGET",true);HYUpdate();HYCheck(HYVisible(),"repeatable reentry recovers");cLux_GetUserConfig().SetBool("SOMA_VR","InteractionGuides",false);HYUpdate();HYCheck(!HYVisible(),"setting off hidden");cLux_GetUserConfig().SetBool("SOMA_VR","InteractionGuides",true);HYUpdate();HYCheck(HYVisible(),"setting on recovers");mVRTraversalHY.Hide();HYCheck(!HYVisible(),"explicit hide");HYUpdate();HYCheck(HYVisible(),"hide is not consumed forever");mVRTraversalHY.Dispose();HYCheck(mVRTraversalHY.mvPoints.length()==0,"dispose releases all map-owned guides");}'
   check=check.replace('TARGET',target)
   fixture+=check
   fixture=fixture.replace('LogNewLine("HR_STORY_DONE|','HYRegression();LogNewLine("HR_STORY_DONE|')
  if '--load-phi' in sys.argv:
   # Start observations from Update, even if native save loading skips OnEnter.
   source=source.replace(' HYCamera();',' if(!mbHZLoadProbe){mbHZLoadProbe=true;LogNewLine("HY_RUN|'+nonce+'");LogNewLine("HZ_LOADED_POINTS|"+mVRTraversalHY.mvPoints.length());Map_AddTimer("hz_load_probe",3,"HRSmokeExit");} HYCamera();',1)
   fixture=' [nosave] bool mbHZLoadProbe=false;'+fixture
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+fixture+source[idx+1:];put(G/rel,source)

  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=1
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
  if '--no-capture' not in sys.argv:time.sleep(2);inject(proc.pid,R/'tests/capture_swap_hy.dll')
  timed_out=False
  try:rc=proc.wait(timeout=55)
  except subprocess.TimeoutExpired:
   timed_out=True
   proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';out.mkdir(parents=True,exist_ok=True);(out/('traversal_'+mapname+'_'+target+'.log')).write_text(log)
  if '--load-phi' in sys.argv:assert 'Started loading save file AutoSave_05-01-phi-inside_2021_1_5_17_11_51_0.sav' in log,'Fixture did not load requested save'
  ok=not timed_out and 'HY_RUN|'+nonce in log and 'HY_CAPTURE_REQUEST' in log and 'HR_STORY_DONE|'+mapname in log and 'HY_FAIL|' not in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  frames=[p for p in G.glob('hy_frame_*.ppm') if p.stat().st_mtime>=start]
  result_dir=out/('ladder_'+mapname+'_'+target+'_'+entry['end']+'_'+nonce);result_dir.mkdir()
  for frame in frames:
   Image.open(frame).verify()
   (result_dir/frame.name).write_bytes(frame.read_bytes())
  (result_dir/'native.log').write_text(log)
  ok=ok and (bool(frames) or '--no-capture' in sys.argv)
  lines=[x for x in log.splitlines() if 'HY_FINAL' in x or 'HY_PASS' in x or 'HY_FAIL' in x or 'HY_POINT' in x or 'HY_AXIS' in x or 'HW_' in x or 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'target':target,'end':entry['end'],'capture_directory':str(result_dir),'execution_completed':ok,'visual_alignment':'not captured' if '--no-capture' in sys.argv else 'pending pixel inspection','exit':rc,'timed_out':timed_out,'nonce':nonce,'arguments':sys.argv[2:],'scope':__doc__,'lines':lines};results.append(result);(result_dir/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
  (out/'ladder_visual_in.json').write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['execution_completed'] for x in results))


