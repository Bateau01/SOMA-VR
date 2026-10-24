from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'runtime/script/player/PlayerState_Conversation.hps'
s=p.read_text(encoding='utf-8-sig')
marker='const float gfConvHeadRotateAcc = 6.0f;'
assert 'HPL3VR_ConversationActive' not in s
s=s.replace(marker,'''// Session gate: flatscreen retains the authored camera behavior.
bool HPL3VR_ConversationActive()
{
    cScript_SetGlobalReturnBool(false);
    cScript_RunGlobalFunc("MenuHandler", "cScrMenuHandler", "HPL3VR_GetRuntimeActive");
    return cScript_GetGlobalReturnBool();
}

'''+marker)
call='cLux_GetPlayer().RotateCameraTowards(gfConvHeadRotateAcc, gfConvHeadRotateMaxSpeed, gfConvHeadRotateSpeedMul, mvFocusPos, false);'
assert s.count(call)==3
s=s.replace(call,'if (!HPL3VR_ConversationActive()) '+call)
s=s.replace('void ZoomIn()\n\t{','void ZoomIn()\n\t{\n        if (HPL3VR_ConversationActive()) return;')
needle='if (mePositionState==ePositionState_Ready)'
assert s.count(needle)==1
s=s.replace(needle,'if (mePositionState==ePositionState_Ready && !HPL3VR_ConversationActive())')
s=s.replace('cLux_GetPlayer().SetCameraPosAdd(eCameraAddType_Conversation, mvHeadBob);',
            'cLux_GetPlayer().SetCameraPosAdd(eCameraAddType_Conversation, HPL3VR_ConversationActive() ? cVector3f_Zero : mvHeadBob);')
s=s.replace('cLux_GetPlayer().SetCameraPosAdd(eCameraAddType_Conversation,mvHeadBob);',
            'cLux_GetPlayer().SetCameraPosAdd(eCameraAddType_Conversation,HPL3VR_ConversationActive() ? cVector3f_Zero : mvHeadBob);')
# Preserve response choice processing; only its forced view movement is suppressed.
needle='pCharBody.AddYaw(avAmount.x*-1*fMul);\n\t\t\t\tcLux_GetPlayer().GetCamera().AddPitch(avAmount.y*-1*fMul);'
assert needle in s
s=s.replace(needle,'if (!HPL3VR_ConversationActive()) { '+needle+' }')
p.write_text(s,encoding='utf-8')
