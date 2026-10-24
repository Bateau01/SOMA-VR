from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'runtime/maps/chapter05/05_01_phi_inside/05_01_phi_inside.hps';s=p.read_text()
idx=s.index('    bool mbVRLaunchButtonWindow=false;')
s=s[:idx]+'''    // Final launch is authorized only when the authored dialogue enables this button.
    // All VR physical/auxiliary routes share this guard; no loading flags are set here.
    bool VR_CanPressLaunchButton()
    {
        iLuxEntity@ button=Map_GetEntity("LaunchButton");
        return button !is null && button.IsActive() && !button.GetInteractionDisabled() &&
               mbVRLaunchButtonWindow && !mbARKLaunched && !mbControllingLoaderArm;
    }
'''+s[idx:]
s=s.replace('if(asEntity=="LaunchButton"||asEntity=="TerminalLaunchInteract")','if((asEntity=="LaunchButton"||asEntity=="TerminalLaunchInteract") && VR_CanPressLaunchButton())')
s=s.replace('void OnChangeStateLaunchButton(const tString &in asEntity, int alState)\n\t\t{','void OnChangeStateLaunchButton(const tString &in asEntity, int alState)\n\t\t{\n            if(!VR_CanPressLaunchButton())return;')
s=s.replace('void TerminalLaunchInteract_OnPlayerInteract(const tString &in asEntity)\n\t\t{','void TerminalLaunchInteract_OnPlayerInteract(const tString &in asEntity)\n\t\t{\n            if(!VR_CanPressLaunchButton())return;')
p.write_text(s)
p=r/'runtime/script/props/Prop_Button.hps';s=p.read_text()
idx=s.index('\tbool CanInteract(')
helper='''    bool VR_PhiLaunchAllowed()
    {
        if(mBaseObj.GetName()!="LaunchButton" || mBaseObj.GetMap().GetName()!="05_01_phi_inside")return true;
        cScript_SetGlobalReturnBool(false);
        cScript_RunGlobalFunc("MenuHandler","cScrMenuHandler","HPL3VR_GetRuntimeActive");
        if(!cScript_GetGlobalReturnBool())return true;
        cLuxMap@ map=mBaseObj.GetMap();
        if(!map.ScriptPrepare("bool VR_CanPressLaunchButton()") || !map.ScriptExecute())return false;
        return map.GetReturnBool();
    }
'''
s=s[:idx]+helper+s[idx:]
s=s.replace('bool CanInteract(int alType, iPhysicsBody@ apBody)\n\t{','bool CanInteract(int alType, iPhysicsBody@ apBody)\n\t{\n        if(!VR_PhiLaunchAllowed())return false;')
s=s.replace('bool OnInteract(int alType, iPhysicsBody@ apBody, const cVector3f &in avFocusPos, const tString&in asData)\n\t{','bool OnInteract(int alType, iPhysicsBody@ apBody, const cVector3f &in avFocusPos, const tString&in asData)\n\t{\n        if(!VR_PhiLaunchAllowed())return false;')
p.write_text(s)

