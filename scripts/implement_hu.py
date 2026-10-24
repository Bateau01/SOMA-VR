from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'runtime/script/modules/MenuHandler.hps';s=p.read_text(encoding='utf-8-sig')
s=s.replace('HPL3VR_Toggle("TEXTURE BUDGET BOOST",7,','HPL3VR_Toggle("TEXTURE BUDGET BOOST",9,').replace('HPL3VR_Toggle("120HZ PHYSICS",9,','HPL3VR_Toggle("120HZ PHYSICS",7,')
s=s.replace('"BUTTON LAYOUT"','"NEXT PAGE"')
a=s.index('        array<tString> lines={',s.index('bool HPL3VR_DrawWelcome()'));b=s.index('        if(mlVRWelcomePage==1)',a)
s=s[:a]+'''        array<tString> lines={
            "First time playing SOMA VR? I strongly suggest reviewing the VR settings",
            "and button layout to adjust things to your preference.",
            "VIDEO: Comfort settings, 120Hz Physics, Desktop Mirror.",
            "GAMEPLAY: VR movement, remote interactions, World Scale, VR hints,",
            "subtitle distance and 2D screen distance.",
            "CONTROLS: Button bindings, sprinting and finger tracking.",
            "EYE TRACKING: Gaze features and dynamic foveated rendering.",
            "AUDIO: Spatial sound settings."
        };
'''+s[b:]
s=s.replace('            HPL3VR_ReadBindings();\n            lines.resize(0);','            cScript_RunGlobalFunc("VRBIND","","PROFILE");\n            HPL3VR_ReadBindings();\n            lines.resize(0);')
# Unknown profile should be honest, not exposed engine abstractions.
s=s.replace('        return buttons[src];','        if(profile<0 && src<4)return "CONTROLLER NOT DETECTED";\n        return buttons[src];')
s=s.replace('10901','10902')
p.write_text(s,encoding='utf-8')
p=r/'source/s26n.c';s=p.read_text()
s=s.replace('static void h48_try_fingertip_poke(i32 hand,const float* handM,i32 gripEdge){','static void h48_try_fingertip_poke(i32 hand,const float* handM,i32 gripEdge){')
s=s.replace('    if(h5730_exact_terminal_state(0,0,0,0))return;\n    if(g_h14GripBody[hand]', '    i32 terminal=h5730_exact_terminal_state(0,0,0,0);\n    if(terminal&&!__atomic_load_n(&g_s26huWorldControlAllowed,__ATOMIC_ACQUIRE))return;\n    if(g_h14GripBody[hand]',1)
needle='    if(iconId==H576BO_TERMINAL_ICON){'
idx=s.index(needle,s.index('static void h48_try_fingertip_poke(i32 hand,const float* handM,i32 gripEdge){'))
s=s[:idx]+'    if(terminal && iconId!=H482_POKE_SWITCH_ICON)return; // Never re-enter or change terminal ownership.\n'+s[idx:]
s=s.replace('static i32 h576bo_terminal_event_gate(void){','static u32 g_s26huWorldControlAllowed; // State-owned, no engine pointers.\nstatic i32 h576bo_terminal_event_gate(void){',1)
idx=s.index('    if(h5748t_sso_eq(objectName,"VRTPRES",7u))')
s=s[:idx]+'''    if(h5748t_sso_eq(objectName,"VRWCTRL",7u)){
        __atomic_store_n(&g_s26huWorldControlAllowed,h5748t_sso_eq(functionName,"Y",1u)?1u:0u,__ATOMIC_RELEASE);return 1u;
    }
'''+s[idx:]
p.write_text(s)
p=r/'source/rocker_y.inc';s=p.read_text();needle='    if(!wrapper||!h20_mem_readable(wrapper,0x2f0u))return 0;'
s=s.replace(needle,'    if(h5730_exact_terminal_state(0,0,0,0)&&!__atomic_load_n(&g_s26huWorldControlAllowed,__ATOMIC_ACQUIRE))return 1;\n'+needle,1);p.write_text(s)
p=r/'runtime/script/player/PlayerState_Interact_Terminal.hps';s=p.read_text()
s=s.replace('        mfVRNoTouchTime=0;\n        mbVRLeavePolicyChecked=false;','        mfVRNoTouchTime=0;\n        cScript_RunGlobalFunc("VRWCTRL","","N");\n        mbVRLeavePolicyChecked=false;')
needle='            if(cScript_RunGlobalFunc("VRTPRES","","")) mfVRNoTouchTime=0;'
s=s.replace(needle,'''            // Ordinary walk-up terminal focus need not suppress a different physical button.
            // Script-owned terminals and non-Normal return states retain exclusivity.
            cScript_RunGlobalFunc("VRWCTRL","",!mbVRLeaveOwnsSequence && mlPreviousState==ePlayerState_Normal ? "Y" : "N");
'''+needle)
s=s.replace('bool bHPL3VR = _HPL3VR_RuntimeActive_TerminalState();','bool bHPL3VR = _HPL3VR_RuntimeActive_TerminalState();\n        cScript_RunGlobalFunc("VRWCTRL","","N");')
p.write_text(s)

