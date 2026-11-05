"""Native Omicron slot/inventory permission census. No interaction or story state mutation; direct saved-map load omits progression."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid,sys
R=Path(__file__).resolve().parents[1]
W=R.parent;G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/jb-omicron-console';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 hp=G/'script/modules/PlayerToolHandler.hps';hs=hp.read_text(encoding='utf-8-sig');hs=hs.replace('    tString VR_ResolveOmniUseTarget(','\n void _Global_JBOmniCensus(){\n cLuxMap@ map=cLux_GetCurrentMap();iLuxEntity@ slot=map.GetEntityByName("omnislot_inside_1",eLuxEntityType_LastEnum,"");\n tString target=VR_ResolveOmniUseTarget(slot);LogNewLine("JB_OMI_TARGET target="+target);\n for(uint i=0;i<mvInventory.length();i++){\n cToolData@ t=mvInventory[i];\n bool ran=false,allowed=false;\n if(t.msCanBeUsedCallback!="" && map.ScriptPrepare("bool "+t.msCanBeUsedCallback+"(const tString &in, const tString &in)")){\n map.SetArgString(0,t.msPickedEntityName);map.SetArgString(1,target);ran=map.ScriptExecute();if(ran)allowed=map.GetReturnBool();}\n LogNewLine("JB_OMI_TOOL name="+t.msPickedEntityName+" can="+t.msCanBeUsedCallback+" use="+t.msUseCallback+" ran="+ran+" allowed="+allowed);\n }\n }\n'+'    tString VR_ResolveOmniUseTarget(',1);put(hp,hs)
 mp=Path('maps/chapter03/03_02_omicron_inside/03_02_omicron_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')

 fixture='\n [nosave] float mfJBClock=0;\n void JBProbe(float dt){mfJBClock+=dt;if(mfJBClock<3 || mfJBClock>3+dt)return;\n LogNewLine("JB_OMI_STATE entered="+mbDiveRoomEntered+" catherine="+mbCatherineInserted+" power="+mbMainPowerRestored);\n array<tString> names={"omnislot_inside_1","CathTool","CathTool_Placed","ContainmentComputer","DivesuitTerminal"};\n for(uint k=0;k<names.length();k++){\n iLuxEntity@ e=Map_GetEntity(names[k]);if(e is null){LogNewLine("JB_OMI_MISSING name="+names[k]);continue;}\n LogNewLine("JB_OMI_ENTITY name="+names[k]+" active="+e.IsActive()+" disabled="+e.GetInteractionDisabled()+" slot="+e.GetVarBool("IsOmniSlot")+" vrDisabled="+e.GetVarBool("VRPhysicalOmniDisabled")+" use="+e.GetVarString("UseCallback")+" can="+e.GetVarString("CanBeUsedCallback"));\n }\n cScript_RunGlobalFunc("PlayerToolHandler","","_Global_JBOmniCensus");\n LogNewLine("IL_DONE|NONCE");cEngine_Exit();}\n'.replace("NONCE",nonce)
 i=s.index("{",s.index("class cScrMap"));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r"void Update\(float (\w+)\)\s*\{",s);assert m
 s=s[:m.end()]+"JBProbe("+m[1]+");"+s[m.end():];put(G/mp,s)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbILStarted=false;\nvoid GuiMainMenuSelection()',1)
 save=sorted((D/'Main').rglob('*03-02-omicron-inside*.sav'),key=lambda p:p.stat().st_mtime)[int(sys.argv[1]) if len(sys.argv)>1 else -1];assert save.exists()
 menu=menu.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\nif(!mbILStarted){mbILStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1).replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 put(D/'SOMA_VR_IL/IL'/save.name,save.read_bytes())
 cfg=(G/'config/main_init.cfg').read_text(encoding='utf-8-sig').replace('MainSaveFolder = "Main"','MainSaveFolder = "SOMA_VR_IL"').replace('config/default_user_settings.cfg','config/il_user.cfg');put(G/'config/il_init.cfg',cfg)
 settings=(G/'config/default_user_settings.cfg').read_text(encoding='utf-8-sig')+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/il_user.cfg',settings)
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'insertion_attempted':False,'physical_controllers':False,'preceding_airlock_exercised':False,'save_name':str(save),'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'exe_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'JB_OMI' in x or 'IL_DONE' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log}
 (out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 restoration={str(p):(not p.exists() if b is None else p.read_bytes()==b) for p,b in saved.items()}
 (out/(nonce+'-restoration.json')).write_text(json.dumps(restoration,indent=2))
 assert all(restoration.values())




assert result["completed"] and result["exit"]==0,result
assert not any(" : ERR " in x or "Exception" in x or "JB_OMI_ERROR" in x for x in result['lines']),result

