"""Native map initialization/compile smoke tests. Actual campaign geometry; synthetic permission and native placement helpers. No completed story sequence or headset validation."""
from pathlib import Path
import subprocess,sys,re,json,hashlib,os
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
routes=json.loads((R/'docs/key-item-guide-routes-ht.json').read_text())['routes']
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 if os.environ.get("HT_NATIVE_EXE"):put(G/"Soma.exe",Path(os.environ["HT_NATIVE_EXE"]).read_bytes())
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 for p in (R/'runtime/entities/soma_vr/guidance').rglob('*'):
  if p.is_file():put(G/'entities/soma_vr/guidance'/p.relative_to(R/'runtime/entities/soma_vr/guidance'),p.read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in ['01_01_upsilon_awake', '02_01_ms_curie_outside', '02_03_delta', '02_05_theta_inside', '02_06_theta_tunnels', '03_02_omicron_inside', '04_02_tau_inside', '05_01_phi_inside']:
  if len(sys.argv)>2 and mapname not in sys.argv[2:]:continue
  matches=list((R/'runtime/maps').rglob(mapname+'.hps'));p=matches[0] if matches else next((G/'maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime') if matches else p.relative_to(G);source=p.read_text(encoding='utf-8-sig')
  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n LogNewLine("HR_STORY_ENTER|'+mapname+'");Map_AddTimer("hr_smoke_exit",4,"HRSmokeExit");'+source[m.end():]

  selected=[r for r in routes if r['map']==mapname]
  calls=[]
  for n,r in enumerate(selected):
   item='BrainScanChip' if r['target']=='SimulationSlot_Right_Interact' else r['items'][0]
   args=[item,r['target'],r['source'],r['mesh'],r['move'],r['stage']]
   calls.append('HTProbe('+','.join(json.dumps(x) for x in args)+','+str(r['mode'])+','+json.dumps(r['sub'])+');')
  probe=r'''
    bool HTCan(const tString &in item,const tString &in target){return true;}
    bool HTUse(const tString &in item,const tString &in target){LogNewLine("HT_UNEXPECTED_USE");return false;}
    void HRSmokeExit(const tString &in name){
      cScript_RunGlobalFunc("PlayerToolHandler","","_Global_HTGeometry");
      LogNewLine("HR_STORY_DONE");
      cEngine_Exit();
    }
  '''
  if mapname=='02_05_theta_inside':
   check=r'''Entity_SetActive("SimulationSlot_Right_Chip",false);Entity_SetActive("SimulationSlot_Left_Chip",false);Entity_SetActive("ScanRoomSlot_Chip",false);
   bool pass=CanUseChip("BrainScanChip","SimulationSlot_Right_Interact") &&
       !CanUseChip("BrainScanChip","SimulationSlot_Left_Interact") &&
       !CanUseChip("BrainScanChip","ScanRoomSlot_Interact") &&
       !CanUseChip("EnvironmentChip","SimulationSlot_Right_Interact") &&
       CanUseChip("EnvironmentChip","SimulationSlot_Left_Interact") &&
       CanUseChip("EnvironmentChip","ScanRoomSlot_Interact");
   Entity_SetActive("SimulationSlot_Right_Chip",true);
   pass=pass && !CanUseChip("BrainScanChip","SimulationSlot_Right_Interact");
   LogNewLine("HT_NATIVE_PERMISSION|theta="+pass);if(!pass)LogNewLine("HT_ALIGNMENT_FAIL|native permission");
   '''
   probe=probe.replace('      LogNewLine("HR_STORY_DONE");',check+'      LogNewLine("HR_STORY_DONE");')
  handler=(R/'runtime/script/modules/PlayerToolHandler.hps').read_text()
  method=r'''
    float HTError(const cMatrixf &in a,const cMatrixf &in b){
      return cMath_Vector3Dist(a.GetTranslation(),b.GetTranslation())+
        cMath_Vector3Dist(a.GetRight(),b.GetRight())+
        cMath_Vector3Dist(a.GetUp(),b.GetUp())+
        cMath_Vector3Dist(a.GetForward(),b.GetForward());
    }
    int mlHTCarrier=0;
    void HTProbe(const tString &in item,const tString &in targetName,const tString &in sourceName,
                 const tString &in mesh,const tString &in move,const tString &in stage,int mode,const tString &in sub){
      cLuxMap@ map=cLux_GetCurrentMap();
      cLuxProp@ source=cast<cLuxProp>(map.GetEntityByName(sourceName,eLuxEntityType_Prop,""));iLuxEntity@ target=map.GetEntityByName(targetName,eLuxEntityType_LastEnum,"");
      if(source is null || target is null){LogNewLine("HT_MISSING|"+item+"|"+targetName+"|"+sourceName);return;}
      // Diagnostic fixture: enable permission/area only, independent of story.
      // Production guide code is unchanged. This does NOT test story eligibility.
      target.SetActive(true);target.SetInteractionDisabled(false);
      if(stage!=""){iLuxEntity@ gate=map.GetEntityByName(stage,eLuxEntityType_LastEnum,"");if(gate !is null)gate.SetActive(true);}
      cMatrixf saved=source.GetMatrix();
      tString carrierName="HTCarrier_"+(mlHTCarrier++);
      map.CreateEntity(carrierName,source.GetFileName(),target.GetMatrix(),cVector3f(1));
      cLuxProp@ carrier=cast<cLuxProp>(map.GetEntityByName(carrierName,eLuxEntityType_Prop,""));
      if(carrier is null){LogNewLine("HT_MISSING_CARRIER");return;}
      carrier.SetActive(true);
      cToolData tool;tool.msPickedEntityName=item;tool.msVRPhysicalCarrierName=carrierName;
      tool.msCanBeUsedCallback="HTCan";tool.msUseCallback="HTUse";
      mlVRItemGuideUsed=0;
      VR_ShowItemGuide(tool,targetName,sourceName,mesh,move,stage,mode,sub);
      if(mlVRItemGuideUsed!=1){LogNewLine("HT_NO_GUIDE|"+item+"|"+targetName);}
      else{
        cMatrixf baseline=cMath_MatrixMul(target.GetMatrix(),
          cMath_MatrixMul(cMath_MatrixInverse(carrier.GetMatrix()),carrier.GetMeshEntity().GetWorldMatrix()));
        // Execute the native placement helper on the original fixture entity.
        // No item-use callbacks, inventory edits or progression are invoked.
        if(move!=""){
          if(mode==2){cScript_SetGlobalArgString(0,sourceName);cScript_SetGlobalArgBool(1,false);cScript_RunGlobalFunc(move,"cScrPropOmniSlot","_Global_Insert");}
          else Entity_PlaceAtEntity(sourceName,move,
              mode==1 ? (targetName=="ArkPlacementArea" ? cVector3f(0,.0625f,0) : cVector3f(0,-.375f,-.25f)) : cVector3f_Zero,
              mode==1);
        }
        float err=0;float oldErr=0;int count=0;
        for(int s=0;s<source.GetMeshEntity().GetSubMeshEntityNum();s++){
          cSubMeshEntity@ native=source.GetMeshEntity().GetSubMeshEntity(s);
          if(sub!="" && native.GetSubMesh().GetName()!=sub)continue;
          cSubMeshEntity@ ghost=mvVRItemGuides[0].mpMesh.GetSubMeshEntity(s);
          LogNewLine("HT_MATRIX|"+item+"|ghost="+ghost.GetWorldMatrix().GetTranslation()+"|native="+native.GetWorldMatrix().GetTranslation()+"|body="+source.GetMatrix().GetTranslation());
          err=cMath_Max(err,HTError(ghost.GetWorldMatrix(),native.GetWorldMatrix()));
          oldErr=cMath_Max(oldErr,HTError(baseline,native.GetWorldMatrix()));count++;
        }
        LogNewLine("HT_GEOMETRY|"+item+"|"+targetName+"|mode="+mode+"|error="+err+"|oldProxyError="+oldErr+"|parts="+count);
        for(int bone=0;bone<source.GetMeshEntity().GetBoneStateNum();bone++){
          float be=HTError(mvVRItemGuides[0].mpMesh.GetBoneState(bone).GetWorldMatrix(),source.GetMeshEntity().GetBoneState(bone).GetWorldMatrix());
          if(be>.002f)LogNewLine("HT_ALIGNMENT_FAIL|bone="+bone+"|error="+be);
        }
        if(err>.002f)LogNewLine("HT_ALIGNMENT_FAIL|"+item+"|"+targetName);
        source.SetMatrix(saved);
      }
      for(uint g=0;g<mvVRItemGuides.length();g++)mvVRItemGuides[g].Dispose(map.GetWorld());
      mvVRItemGuides.resize(0);mlVRItemGuideUsed=0;
      map.DestroyEntity(carrier);
    }
    void _Global_HTGeometry(){
  '''+'\n'.join(calls)+r'''
    }
  '''
  begin=handler.index('    void VR_ShowItemGuide(');end=handler.index('    // HT campaign route inventory:',begin)
  block=handler[begin:end];parts=[]
  for line,n in zip(block.splitlines(),range(1000)):
   parts.append(line.replace('return;', '{LogNewLine("HT_REJECT|'+str(n)+'");return;}'))
  handler=handler[:begin]+chr(10).join(parts)+chr(10)+handler[end:]
  handler=handler.replace('    void VR_HideItemGuides()',method+'\n    void VR_HideItemGuides()',1)
  put(G/'script/modules/PlayerToolHandler.hps',handler)
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+probe+source[idx+1:];put(G/rel,source)

  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/(('store_' if os.environ.get('HT_NATIVE_EXE') else '')+'key_geometry_'+mapname+'.log')).write_text(log)
  ok='HT_ALIGNMENT_FAIL' not in log and 'HT_MISSING' not in log and 'HT_NO_GUIDE' not in log and 'HT_UNEXPECTED_USE' not in log and 'HR_STORY_DONE' in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if 'HT_' in x or 'HR_STORY' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/(('store_' if os.environ.get('HT_NATIVE_EXE') else '')+'key_geometry_ht.json')).write_text(json.dumps(results,indent=2))
  if not ok:break
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))
