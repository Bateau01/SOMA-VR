"""Native scripted sequence/permission fixtures with supplied runtime/held observations. No headset/controller or full-playthrough proof."""
from pathlib import Path
import subprocess,sys,re,json,hashlib,os
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]).resolve();assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;results=[]
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 if os.environ.get('HV_NATIVE_EXE'):put(G/'Soma.exe',Path(os.environ['HV_NATIVE_EXE']).read_bytes())
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 for p in (R/'runtime/entities/soma_vr/guidance').rglob('*'):
  if p.is_file():put(G/'entities/soma_vr/guidance'/p.relative_to(R/'runtime/entities/soma_vr/guidance'),p.read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1);needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace('cScript_SetGlobalReturnBool(gbHPL3VRRuntimeActive);','cScript_SetGlobalReturnBool(true);')
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/hr_story_user.cfg',defaults)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 for mapname in sys.argv[2:] or ['01_01_upsilon_awake']:
  matches=list((R/'runtime/maps').rglob(mapname+'.hps'));p=matches[0] if matches else next((G/'maps').rglob(mapname+'.hps'));rel=p.relative_to(R/'runtime') if matches else p.relative_to(G);source=p.read_text(encoding='utf-8-sig')
  custom=R/'tests/fixtures/omni_hv_map.hps'
  probe=custom.read_text()
  if os.environ.get('HV_AUDIT'):
   routes=[x for x in json.loads((R/'docs/omni-guide-routes-hv.json').read_text()) if x['map']==mapname]
   calls=[]
   for x in routes:
    args=[x[k] for k in ['tool','can','use','slot','expectedTarget']]
    # Stable locals across the argument bridge, not temporary expressions.
    calls.append('{'+''.join('tString a'+str(i)+'='+json.dumps(v)+';' for i,v in enumerate(args))+''.join('cScript_SetGlobalArgString('+str(i)+',a'+str(i)+');' for i in range(5))+'cScript_RunGlobalFunc("PlayerToolHandler","","_Global_HVAudit");}')
   probe='void HVProbe(const tString &in timer){'+''.join(calls)+'LogNewLine("HV_DONE");cEngine_Exit();}'

  m=re.search(r'void OnEnter\(\)\s*\{',source);assert m
  source=source[:m.end()]+'\n Map_AddTimer("HVProbe",4,"HVProbe");'+source[m.end():]
  idx=source.index('{',source.index('class cScrMap'));source=source[:idx+1]+probe+source[idx+1:];put(G/rel,source)
  handler=(R/'runtime/script/modules/PlayerToolHandler.hps').read_text()
  if os.environ.get('HV_BASELINE'):
   handler=(R.parent.parent/'SOMA_VR_109_S26HU/repo/runtime/script/modules/PlayerToolHandler.hps').read_text()
  # Fixture substitutes runtime/held observation only, not inventory or permission.
  a=handler.index('    void _Global_VRCanGuideOmniSlot()');b=handler.index('void _Global_VRPhysicalOmniUseSlot()',a)
  block=handler[a:b].replace('cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','true').replace('cScript_RunGlobalFunc("VROMNIHELD",tool.msPickedEntityName,"Q")','mbHVHeld')
  block=block.replace('if(slot !is null && slot.IsActive()', 'LogNewLine("HV_SLOT|name="+slotName+"|map="+map.GetName()+"|found="+(slot !is null));if(slot !is null)LogNewLine("HV_SLOT_STATE|active="+slot.IsActive()+"|tag="+slot.GetVarBool("IsOmniSlot"));if(slot !is null && slot.IsActive()').replace('bool allowed=false;', 'bool allowed=false;LogNewLine("HV_NAME|"+slotName+"|runtime="+_HPL3VR_RuntimeActive_ToolHandler());').replace('if(target!="") for', 'LogNewLine("HV_TARGET|"+slotName+"->"+target);if(target!="") for').replace('cScript_SetGlobalReturnBool(allowed);','LogNewLine("HV_ALLOWED|"+allowed);cScript_SetGlobalReturnBool(allowed);')
  handler=handler[:a]+block+handler[b:]
  handler=handler.replace('    void _Global_VRCanGuideOmniSlot()', (R/'tests/fixtures/omni_hv_handler.hps').read_text()+(R/'tests/fixtures/omni_hv_audit.hps').read_text()+'\n    void _Global_VRCanGuideOmniSlot()',1)
  handler=handler.replace('cScript_RunGlobalFunc("VROMNIHELD",pPhysicalOmni.msPickedEntityName,"Q")','mbHVHeld')
  put(G/'script/modules/PlayerToolHandler.hps',handler)
  slot=(R/'runtime/script/custom_depth/prop_omnitool_slot.hps').read_text().replace('cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','true')
  slot=slot.replace('    void VR_UpdateGuide(float dt)', (R/'tests/fixtures/omni_hv_slot.hps').read_text()+'\n    void VR_UpdateGuide(float dt)',1)
  a=slot.index('    void VR_UpdateGuide(float dt)');b=slot.index('    // Read-only bridge',a)
  block=slot[a:b]
  block='\n'.join(line.replace('return;', '{LogNewLine("HV_REJECT|slot line '+str(i)+'");return;}') for i,line in enumerate(block.splitlines()))
  slot=slot[:a]+block+'\n'+slot[b:]
  put(G/'script/custom_depth/prop_omnitool_slot.hps',slot)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',mapname+'.hpm').replace('maps/vr_pump_lab/',str(rel.parent).replace('\\','/')+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');out=R/'docs/v109-evidence';(out/(('baseline_' if os.environ.get('HV_BASELINE') else ('store_' if os.environ.get('HV_NATIVE_EXE') else ''))+('audit_' if os.environ.get('HV_AUDIT') else 'omni_')+mapname+'_hv.log')).write_text(log)
  ok='HV_DONE' in log and 'HV_FAIL' not in log and ' : ERR ' not in log and 'FATAL ERROR' not in log
  lines=[x for x in log.splitlines() if ('HV_' in x and 'HV_REJECT' not in x) or ' : ERR ' in x or 'FATAL ERROR' in x]
  result={'map':mapname,'passed':ok,'exit':rc,'scope':__doc__,'lines':lines};results.append(result);print(json.dumps(result),flush=True)
  (out/(('baseline_' if os.environ.get('HV_BASELINE') else ('store_' if os.environ.get('HV_NATIVE_EXE') else ''))+('omni_audit_hv.json' if os.environ.get('HV_AUDIT') else 'omni_sequence_hv.json'))).write_text(json.dumps(results,indent=2))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))

