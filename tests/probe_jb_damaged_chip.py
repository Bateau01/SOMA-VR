"""Native Omicron damaged chip body/permission and adjacent-ray census. No interaction or story state mutation; direct saved-map load omits progression."""
from pathlib import Path
import subprocess,re,time,json,hashlib,uuid,sys
R=Path(__file__).resolve().parents[1]
W=R.parent;G=W/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
D=Path.home()/'Documents/My Games/Soma'
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
saved={};proc=None;nonce=uuid.uuid4().hex
out=R/'audit/jb-damaged-chip';out.mkdir(exist_ok=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime').rglob('*.hps'):put(G/p.relative_to(R/'runtime'),p.read_bytes())
 mp=Path('maps/chapter03/03_02_omicron_inside/03_02_omicron_inside.hps')
 s=(R/'runtime'/mp).read_text(encoding='utf-8-sig')

 fixture='\n [nosave] float mfJBClock=0;\n void JBProbe(float dt){mfJBClock+=dt;if(mfJBClock<3 || mfJBClock>3+dt)return;\nLogNewLine("JB_CHIP_COVER open="+SwingDoor_GetOpenAmount("FluidContainerFuseBox")+" locked="+SwingDoor_GetLocked("FluidContainerFuseBox")+" exploded="+mbBioMechChipExploded+" repaired="+mbBioMechChipRepaired);\n array<tString> names={"ChipTool_Damaged","ChipTool_PreRepair","ChipTool_Repaired","Chip_FullyRepaired"};\n for(uint k=0;k<names.length();k++){\n cLuxProp@ p=Map_GetProp(names[k]);if(p is null){LogNewLine("JB_CHIP_MISSING "+names[k]);continue;}\n LogNewLine("JB_CHIP_PROP name="+names[k]+" active="+p.IsActive()+" disabled="+p.GetInteractionDisabled());\n for(int i=0;i<p.GetBodyNum();i++){\n iPhysicsBody@ b=p.GetBody(i);cVector3f lo=b.GetBoundingVolume().GetMin(),hi=b.GetBoundingVolume().GetMax();\n LogNewLine("JB_CHIP_BODY name="+b.GetName()+" mass="+b.GetMass()+" collide="+b.GetCollide()+" can="+p.CanInteract(0,b)+" bounds="+lo.x+","+lo.y+","+lo.z+":"+hi.x+","+hi.y+","+hi.z);\n if(k==0){cVector3f c=(lo+hi)*.5f;\n for(int axis=0;axis<3;axis++)for(int side=-1;side<=1;side+=2){cVector3f d(0,0,0);if(axis==0)d.x=side;if(axis==1)d.y=side;if(axis==2)d.z=side;\n cLuxClosestEntityData hit;bool ok=cLux_GetClosestEntity(c+d*.18f,d*-1,.36f,0,false,hit);\n if(ok&&hit.mpEntity !is null)LogNewLine("JB_CHIP_RAY axis="+axis+" side="+side+" target="+hit.mpEntity.GetName()+" distance="+hit.mfDistance);\n }}\n }}LogNewLine("IL_DONE|NONCE");cEngine_Exit();}\n'.replace("NONCE",nonce)
 i=s.index("{",s.index("class cScrMap"));s=s[:i+1]+fixture+s[i+1:]
 m=re.search(r"void Update\(float (\w+)\)\s*\{",s);assert m
 s=s[:m.end()]+"JBProbe("+m[1]+");"+s[m.end():];put(G/mp,s)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');menu=menu.replace('void GuiMainMenuSelection()','bool mbILStarted=false;\nvoid GuiMainMenuSelection()',1)
 save=sorted((D/'Main').rglob('*03-02-omicron-inside*.sav'),key=lambda p:p.stat().st_mtime)[-1];assert save.exists()
 menu=menu.replace('void GuiMainMenuSelection()\n\t{','void GuiMainMenuSelection()\n\t{\nif(!mbILStarted){mbILStarted=true;StartSavedGameLoad(tWString("'+save.name+'"));}',1).replace('if(sKeyPress.length()!=0)','if(true)').replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 put(D/'SOMA_VR_IL/IL'/save.name,save.read_bytes())
 cfg=(G/'config/main_init.cfg').read_text(encoding='utf-8-sig').replace('MainSaveFolder = "Main"','MainSaveFolder = "SOMA_VR_IL"').replace('config/default_user_settings.cfg','config/il_user.cfg');put(G/'config/il_init.cfg',cfg)
 settings=(G/'config/default_user_settings.cfg').read_text(encoding='utf-8-sig')+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="true" ShowPreMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/il_user.cfg',settings)
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','IL','-cfg','config/il_init.cfg'],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 log=(D/'SOMA_VR_IL/hpl.log').read_text(errors='replace');(out/(nonce+'.log')).write_text(log)
 result={'nonce':nonce,'scope':__doc__,'inserted_fixture':'--inserted' in sys.argv,'save_sha256':hashlib.sha256(save.read_bytes()).hexdigest(),'exe_sha256':hashlib.sha256((G/'Soma.exe').read_bytes()).hexdigest(),'exit':rc,'lines':[x for x in log.splitlines() if 'JB_CHIP' in x or 'IL_DONE' in x or ' : ERR ' in x or 'Exception' in x],'completed':'IL_DONE|'+nonce in log}
 (out/(nonce+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)




assert result["completed"] and result["exit"]==0,result
assert not any(" : ERR " in x or "Exception" in x or "JB_ENV_MISSING" in x for x in result['lines']),result

