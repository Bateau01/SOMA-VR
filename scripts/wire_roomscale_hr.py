from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'source/s26n.c';s=p.read_text();s=s.replace('#include "eye_bridge_s.inc"','#include "eye_bridge_s.inc"\n#include "roomscale_hr.inc"',1)
s=s.replace('if(h5748t_sso_eq(objectName,"VREYES",6u))','if(h5748t_sso_eq(objectName,"VRROOM",6u))return s26hr_room_token(className,functionName);\n    if(h5748t_sso_eq(objectName,"VREYES",6u))',1);p.write_text(s)
p=R/'runtime/script/player/Player.hps';s=p.read_text(encoding='utf-8-sig');s='#include "helpers/helper_vr_roomscale_hr.hps"\n'+s
method='''
    void HPL3VR_UpdateRoomscale()
    {
        int state=mBaseObj.GetCurrentStateId();
        if(!_HPL3VR_RuntimeActive_Player() || !mBaseObj.IsActive() ||
           mBaseObj.GetCurrentMoveStateId()!=eMoveState_Normal ||
           (state!=ePlayerState_Normal && state!=ePlayerState_Grab) ||
           mfMoveSpeedMul<=.05f || mfMoveSpeedMulTarget<=.05f ||
           !cLux_GetUserConfig().GetBool("SOMA_VR","Roomscale",true)){
            cScript_RunGlobalFunc("VRROOM","","RESET");return;
        }
        if(!cScript_RunGlobalFunc("VRROOM","","QUERY"))return;
        cVector3f requested=cScript_GetGlobalReturnVector3f();
        cVector3f accepted=HPL3VR_RoomscaleMove(mBaseObj.GetCharacterBody(),requested);
        tString movement=""+accepted.x+","+accepted.y+","+accepted.z;
        cScript_RunGlobalFunc("VRROOM",movement,"ACK");
    }
'''
s=s.replace('void Update(float afTimeStep)',method+'\n\tvoid Update(float afTimeStep)',1)
needle='void Update(float afTimeStep)\n\t{';assert needle in s;s=s.replace(needle,needle+'\n        HPL3VR_UpdateRoomscale();',1);p.write_text(s,encoding='utf-8')
