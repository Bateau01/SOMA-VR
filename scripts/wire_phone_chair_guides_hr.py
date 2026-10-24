from pathlib import Path
r=Path.cwd();p=r/'source/s26n.c';s=p.read_text();a='        if(h5748t_sso_eq(functionName,"ACTIVE",6u))return 1;';n=a+'''
        if(h5748t_sso_eq(functionName,"PHONE",5u)){
            float pos[3],m[16],center[3];
            if(!g_s26xPhoneActive||!g_s26xPhonePending||g_h14GripBody[1]||!visual_pose_valid(1)||
               !h14_hand_pose_raw(1,pos,m)||!h15_grip_center_world(1,m,center))return 0;
            s26s_set_vector(center);return 1;
        }''';assert a in s;s=s.replace(a,n,1);p.write_text(s)
p=r/'runtime/script/helpers/helper_vr_phone_q.hps';s=p.read_text();s='#include "helpers/helper_vr_guidance_hr.hps"\n'+s
s=s.replace('    int state=0;','    [nosave] cVRGuideMesh mVRPhoneGuide;\n    [nosave] cVRHandGuide mVRPhoneHandGuide;\n    int state=0;',1)
s=s.replace('        Native("F");\n        if(state==2)', '''        Native("F");
        mVRPhoneGuide.Hide();mVRPhoneHandGuide.Hide();
        if(state==1 && cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true) &&
           cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")){
            cWorld@ world=cLux_GetCurrentMap().GetWorld();
            if(pocket && cScript_RunGlobalFunc("VRGUIDE","","PHONE")){
                cVector3f position=cScript_GetGlobalReturnVector3f();
                cMatrixf frame=cMath_MatrixRotateY(cLux_GetPlayer().GetCamera().GetYaw());
                frame.SetTranslation(position);
                mVRPhoneGuide.Show(world,"VRPhoneGuide","entities/urban/props/phone_mobile/phone_mobile.dae",frame);
            }else if(!pocket){
                cLuxProp@ prop=cLux_ToProp(Entity());
                if(prop !is null && prop.GetMainBody() !is null &&
                   !cScript_RunGlobalFunc("VRPHONEQ",""+prop.GetMainBody().GetUniqueID(),"H")){
                    cMatrixf frame=prop.GetMatrix();
                    mVRPhoneHandGuide.Show(world,"VRPhoneHandGuide",frame,1,false);
                }
            }
        }
        if(state==2)''',1)
s=s.replace('    void End()\n    {','    void End()\n    {\n        mVRPhoneGuide.Dispose(cLux_GetCurrentMap().GetWorld());\n        mVRPhoneHandGuide.Dispose(cLux_GetCurrentMap().GetWorld());',1);p.write_text(s)
p=r/'runtime/maps/chapter00/00_03_laboratory/00_03_laboratory.hps';s=p.read_text();s='#include "helpers/helper_vr_guidance_hr.hps"\n'+s
old='void Update(float afTimeStep)\n\t{\n\t}'
new='''[nosave] cVRHandGuide mVRChairGuide;
    [nosave] float mfVRChairGuidePoll=0;
    bool mbVRChairGuideReady=false;
    void Update(float afTimeStep)
    {
        mfVRChairGuidePoll-=afTimeStep;if(mfVRChairGuidePoll>0)return;mfVRChairGuidePoll=.125f;
        mVRChairGuide.Hide();
        if(!mbVRChairGuideReady || !cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true))return;
        cScript_SetGlobalReturnBool(false);
        cScript_RunGlobalFunc("MenuHandler","cScrMenuHandler","HPL3VR_GetRuntimeActive");
        if(!cScript_GetGlobalReturnBool() || !cScript_RunGlobalFunc("VRGUIDE","","ACTIVE"))return;
        iLuxEntity@ chair=Map_GetEntity("ScanChair");
        if(chair is null || !chair.IsActive() || chair.GetInteractionDisabled() ||
           cLux_GetPlayer().GetCurrentStateId()!=ePlayerState_Normal ||
           cMath_Vector3Dist(chair.GetPosition(),cLux_GetPlayer().GetCamera().GetPosition())>2.5f)return;
        // Authored chair armrest top (Shape_3); its native interaction remains authoritative.
        cVector3f at=cMath_MatrixMul(chair.GetMatrix(),cVector3f(.40625,1.10,.08447));
        mVRChairGuide.Show(cLux_GetCurrentMap().GetWorld(),"VRChairGuide",
            VRGuide_HandFrame(at,cVector3f(0,1,0),false),1,false);
    }'''
assert old in s;s=s.replace(old,new,1);s=s.replace('if(asSubject=="7_GreetDavid"){','if(asSubject=="7_GreetDavid"){mbVRChairGuideReady=true;',1)
s=s.replace('void OnLeave() \n\t{','void OnLeave() \n\t{\n        mVRChairGuide.Dispose(cLux_GetCurrentMap().GetWorld());',1);p.write_text(s)
