"""Actual Theta lab terminal policy; no held-hand or item callback bypass."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text().replace("out=R/'audit/jb-env-geometry'","out=R/'audit/je-terminal-lab'")
s=s.replace('02_06_theta_tunnels','02_05_theta_inside').replace('AutoSave_02-06-theta-tunnels_2026_10_13_19_59_0_0.sav','AutoSave_02-05-theta-inside_2021_1_5_14_3_20_0.sav')
a=s.index(" fixture='");b=s.index(' i=s.index',a)
fixture=r"""
 [nosave] float mfJET=0;void JBProbe(float dt){mfJET+=dt;if(mfJET<3 || mfJET>3+dt)return;
 array<tString> terms={"ScanRoomTerminal","LegacyTerminal","BrainScanSimulationTerminal"};
 for(uint i=0;i<terms.length();i++){
 Player_ChangeStateToNormal();iLuxEntity@ e=Map_GetEntity(terms[i]);iPhysicsBody@ b=e.GetMainBody();bool can=e.CanInteract(0,b);bool entered=can&&e.OnInteract(0,b,b.GetWorldMatrix().GetTranslation(),"");
 LogNewLine("JE_LAB_ENTER|name="+terms[i]+"|can="+can+"|entered="+entered);if(entered)cScript_RunGlobalFunc("State_Interact_Terminal","","_Global_JEProbe");}
 Player_ChangeStateToNormal();
 LogNewLine("JE_LAB_MAP|unknown="+VR_CanUseHeldItemsFromTerminal("not_a_terminal"));
 mSimulationTerminalState=eSimulationTerminalState_SimulationRunning;
 LogNewLine("JE_LAB_MAP|running="+VR_CanUseHeldItemsFromTerminal("BrainScanSimulationTerminal"));
 LogNewLine("IL_DONE|NONCE");cEngine_Exit();}
"""
# use repr for a code-safe newline inside the generated script literal
# Build this mutation separately to avoid multiple shell/string quoting layers.
setup=' p=G/\'script/player/PlayerState_Interact_Terminal.hps\';state=p.read_text(encoding=\'utf-8-sig\');state=state.replace(\'    bool VR_HeldItemUseAllowed()\', \'void _Global_JEProbe(){LogNewLine("JE_LAB_POLICY|allowed="+VR_HeldItemUseAllowed());}\\n    bool VR_HeldItemUseAllowed()\',1);put(p,state)\n'
s=s[:a]+' fixture='+repr(fixture)+'.replace("NONCE",nonce)\n'+setup+s[b:]
s=s.replace("'JB_ENV' in x","'JE_' in x")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
assert 'JE_LAB_MAP|unknown=false' in log and 'JE_LAB_MAP|running=false' in log
