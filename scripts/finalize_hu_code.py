from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'runtime/script/areas/Area_InteractAux.hps';s=p.read_text()
needle='\tbool CanInteract(int alType, iPhysicsBody@ apBody)'
helper='''    bool HU_SeatContactAllowed(iLuxEntity@ parent)
    {
        if(mBaseObj.GetName()!="VRSeatArm_0" && mBaseObj.GetName()!="VRSeatArm_1")return true;
        cScript_SetGlobalReturnBool(false);
        cScript_RunGlobalFunc("MenuHandler","cScrMenuHandler","HPL3VR_GetRuntimeActive");
        return cScript_GetGlobalReturnBool() && parent !is null && parent.IsActive() &&
            cLux_GetPlayer().GetCurrentStateId()==ePlayerState_Normal;
    }
'''
s=s.replace(needle,helper+needle)
s=s.replace('if ((mBaseObj.GetName()=="VRSeatArm_0" || mBaseObj.GetName()=="VRSeatArm_1") &&\n            (!pInteractEntity.IsActive() || cLux_GetPlayer().GetCurrentStateId()!=ePlayerState_Normal))return false;','if(!HU_SeatContactAllowed(pInteractEntity))return false;')
p.write_text(s)
p=r/'runtime/script/player/PlayerState_Interact_Terminal.hps';s=p.read_text();s=s.replace('void OnMapEnter(cLuxMap @apMap)\n\t{','void OnMapEnter(cLuxMap @apMap)\n\t{\n        cScript_RunGlobalFunc("VRWCTRL","","N");').replace('void OnMapLeave(cLuxMap @apMap)\n\t{','void OnMapLeave(cLuxMap @apMap)\n\t{\n        cScript_RunGlobalFunc("VRWCTRL","","N");');p.write_text(s)
for name in ['source/s26n.c','runtime/script/modules/MenuHandler.hps','installer/source/Build.ps1','installer/source/Installer.cs','installer/source/CurrentUpgradeTests.cs']:
 p=r/name;b=p.read_bytes();p.write_bytes(b.replace(b'S26HT',b'S26HU').replace(b'2026102203',b'2026102204'))

