"""Native checkpoint reload and carrier reconciliation; synthetic held setup, not physical grip/death-animation proof."""
from pathlib import Path
import re,sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/jc-death-reload'")
fixture=r'''
 int mlJBReloadPhase=0;
 [nosave] float mfJBClock=0;
 void JBProbe(float dt){
  mfJBClock+=dt;
  if(mlJBReloadPhase==0 && mfJBClock>=3){
   Entity_CallEntityInteract("chip_unformatted");
   cScript_RunGlobalFunc("PlayerToolHandler","","_Global_JBHeldSaveSetup");
   mlJBReloadPhase=1;
   LogNewLine("JB_RELOAD_SAVE_REQUEST");
   cLux_GetSaveHandler().DelayedSaveGameToFile(tWString("CheckPoint.sav"), false);
  }
  if(mlJBReloadPhase==1 && mfJBClock>=6){
   mlJBReloadPhase=2;
   LogNewLine("JB_RELOAD_DEATH_REQUEST");
   cScript_RunGlobalFunc("GameOverHandler","","_Global_JBDeathReload");
  }
  if(mlJBReloadPhase==1 && mfJBClock>=2 && mfJBClock<3){
   mlJBReloadPhase=3;
   cScript_RunGlobalFunc("PlayerToolHandler","","_Global_JBLoadedInspect");
   LogNewLine("IL_DONE|NONCE");cEngine_Exit();
  }
 }
'''
method=r'''
 void _Global_JBHeldSaveSetup(){
  int found=0;
  for(uint i=0;i<mvInventory.length();i++){
   cToolData@ t=mvInventory[i];if(t.msPickedEntityName!="chip_unformatted")continue;
   found++;t.mbVRShoulderStowed=false;
   iLuxEntity@ e=cLux_GetCurrentMap().GetEntityByName(VR_GetPhysicalCarrierName(t),eLuxEntityType_LastEnum,"");
   if(e is null || e.GetMainBody() is null){LogNewLine("JB_RELOAD_MISSING_BODY");continue;}
   e.SetActive(true);iPhysicsBody@ b=e.GetMainBody();b.SetGravity(false);
   LogNewLine("JB_RELOAD_HELD_SETUP|gravity="+b.GetGravity()+"|active="+e.IsActive());
  }
  LogNewLine("JB_RELOAD_INVENTORY_BEFORE|count="+found);
 }
 void _Global_JBLoadedInspect(){
  VR_ReconcileShoulderInventory(1.0f);
  int found=0;
  for(uint i=0;i<mvInventory.length();i++){
   cToolData@ t=mvInventory[i];if(t.msPickedEntityName!="chip_unformatted")continue;
   found++;iLuxEntity@ e=cLux_GetCurrentMap().GetEntityByName(VR_GetPhysicalCarrierName(t),eLuxEntityType_LastEnum,"");
   if(e is null || e.GetMainBody() is null){LogNewLine("JB_RELOAD_MISSING_BODY");continue;}
   iPhysicsBody@ b=e.GetMainBody();
   LogNewLine("JB_RELOAD_LOADED|gravity="+b.GetGravity()+"|active="+e.IsActive()+"|stowed="+t.mbVRShoulderStowed);
   b.SetGravity(false);VR_ReconcileShoulderInventory(1.0f);
   LogNewLine("JB_RELOAD_ONCE_ONLY|gravity="+b.GetGravity());
  }
  LogNewLine("JB_RELOAD_INVENTORY_AFTER|count="+found);
 }
'''
if '--stowed' in sys.argv:
 method=method.replace('t.mbVRShoulderStowed=false;', 't.mbVRShoulderStowed=true;')
 method=method.replace('e.SetActive(true);iPhysicsBody@ b=', 'e.SetActive(false);iPhysicsBody@ b=')
a=s.index(" fixture='");b=s.index(" if '--inserted'",a)
s=s[:a]+" fixture="+repr(fixture)+".replace('NONCE',nonce)\n"+s[b:]
needle=" mp=Path('maps/chapter02/02_06_theta_tunnels/02_06_theta_tunnels.hps')"
inject=r"""
 # Fixture mode gates only: native process has no OpenXR DLL. Reconciliation and
 # carrier code execute unchanged; no statement about C ownership is implied.
 for rel,fn in [('script/modules/PlayerToolHandler.hps','_HPL3VR_RuntimeActive_ToolHandler'),('script/props/Prop_Tool.hps','_HPL3VR_RuntimeActive_PropTool')]:
  p=G/rel;t=p.read_text(encoding='utf-8-sig')
  pattern=r'bool '+fn+r'\(\)\s*\{[^}]+\}'
  t,n=re.subn(pattern,'bool '+fn+'(){return true;}',t,count=1);assert n==1
  if 'PlayerToolHandler' in rel:t=t.replace('    bool VR_PhysicalTargetContact(',METHOD+'    bool VR_PhysicalTargetContact(',1)
  put(p,t)
 p=G/'script/modules/GameOverHandler.hps';t=p.read_text(encoding='utf-8-sig')
 t=t.replace('void End_Timer_DeathOver(uint64 alID)','void _Global_JBDeathReload(){gsVRDeathHeldMap=cLux_GetCurrentMap().GetName();gsVRDeathHeldKeys.resize(0);gsVRDeathHeldKeys.push_back("chip_unformatted");End_Timer_DeathOver(0); }\n void End_Timer_DeathOver(uint64 alID)',1);put(p,t)
 # Back up the test profile checkpoint, never the player's checkpoint.
 checkpoint=D/'SOMA_VR_IL/IL/CheckPoint.sav'
 if checkpoint not in saved:saved[checkpoint]=checkpoint.read_bytes() if checkpoint.exists() else None
""".replace('METHOD',repr(method))
s=s.replace(needle,inject+'\n'+needle)
s=s.replace("'scope':__doc__","'scope':'Native checkpoint reload with synthetic held/stowed state; forced VR script gates and explicit reconciliation, no OpenXR hand ownership proof'")
s=s.replace("'lines':[x for x", "'test_scope':'Native checkpoint/death reload with synthetic held/stowed state and forced script VR gates; no OpenXR hand ownership proof','stowed_fixture':'--stowed' in sys.argv,'lines':[x for x")
s=s.replace("if 'JB_ENV' in x", "if 'JB_RELOAD' in x or 'JB_ENV' in x")
if '--loose' in sys.argv or '--not-owned' in sys.argv or '--different-map' in sys.argv:
 if '--loose' in sys.argv:s=s.replace('gsVRDeathHeldKeys.push_back("chip_unformatted");','')
 if '--not-owned' in sys.argv:s=s.replace('gsVRDeathHeldKeys.push_back("chip_unformatted");','gsVRDeathHeldKeys.push_back("NotAcquiredTool");')
 if '--different-map' in sys.argv:s=s.replace('gsVRDeathHeldMap=cLux_GetCurrentMap().GetName();','gsVRDeathHeldMap="other_map";')
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
assert ('JB_RELOAD_HELD_SETUP|gravity=false|active=false' if '--stowed' in sys.argv else 'JB_RELOAD_HELD_SETUP|gravity=false|active=true') in log
assert 'JB_RELOAD_DEATH_REQUEST' in log
expected='JB_RELOAD_LOADED|gravity=true|active=true|stowed=false' if any(x in sys.argv for x in ('--loose','--not-owned','--different-map')) else 'JB_RELOAD_LOADED|gravity=false|active=false|stowed=true'
assert expected in log
assert 'JB_RELOAD_INVENTORY_BEFORE|count=1' in log and 'JB_RELOAD_INVENTORY_AFTER|count=1' in log
assert 'JB_RELOAD_ONCE_ONLY|gravity=false' in log
assert 'JB_RELOAD_MISSING_BODY' not in log
