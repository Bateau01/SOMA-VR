"""Actual native terminal entry and permission checks. Synthetic denied-state variations are identified in logs; not a physical hand test."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/je-terminal-native'")
needle=' i=s.index("{",s.index("class cScrMap"));'
addition=r"""
 fixture=fixture.replace('LogNewLine("IL_DONE|', 'iLuxEntity@ term=Map_GetEntity("SecurityOfficeTerminal");iPhysicsBody@ tb=term.GetMainBody();bool can=term.CanInteract(0,tb);bool entered=can&&term.OnInteract(0,tb,tb.GetWorldMatrix().GetTranslation(),"");LogNewLine("JE_TERM_ENTER|can="+can+"|entered="+entered+"|state="+cLux_GetPlayer().GetCurrentStateId());cScript_RunGlobalFunc("State_Interact_Terminal","","_Global_JEProbe");bool itemAllowed=Entity_IsActive(msBrokenPanelArea)&&chip_unformatted_CanBeUsed("chip_unformatted",msBrokenPanelArea);bool itemUsed=itemAllowed&&chip_unformatted_OnUse("chip_unformatted",msBrokenPanelArea);LogNewLine("JE_ITEM_NATIVE|allowed="+itemAllowed+"|used="+itemUsed+"|terminal="+(cLux_GetPlayer().GetCurrentStateId()==ePlayerState_Terminal)+"|installed="+mbUnformattedChipInPanel);Player_ChangeStateToNormal();LogNewLine("JE_TERM_EXIT|normal="+(cLux_GetPlayer().GetCurrentStateId()==ePlayerState_Normal));LogNewLine("IL_DONE|',1)
 p=G/'script/player/PlayerState_Interact_Terminal.hps';state=p.read_text(encoding='utf-8-sig')
 probe='\n void _Global_JEProbe(){\n LogNewLine("JE_POLICY|actual="+VR_HeldItemUseAllowed()+"|previous="+mlPreviousState+"|leave="+msLeaveCallback);\n int old=mlPreviousState;mlPreviousState=ePlayerState_Sit;LogNewLine("JE_POLICY|syntheticSit="+VR_HeldItemUseAllowed());mlPreviousState=old;\n tString cb=msLeaveCallback;msLeaveCallback="";LogNewLine("JE_POLICY|syntheticWalkup="+VR_HeldItemUseAllowed());msLeaveCallback=cb;\n }\n'
 state=state.replace('    bool VR_HeldItemUseAllowed()',probe+'    bool VR_HeldItemUseAllowed()',1);put(p,state)
"""
s=s.replace(needle,addition+needle)
s=s.replace("'JB_ENV' in x", "'JB_ENV' in x or 'JE_' in x")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
assert 'JE_POLICY|actual=true' in log
assert 'JE_POLICY|syntheticSit=false' in log
assert 'JE_POLICY|syntheticWalkup=true' in log
assert 'JE_TERM_EXIT|normal=true' in log

assert "JE_ITEM_NATIVE|allowed=true|used=true|terminal=true|installed=true" in log
