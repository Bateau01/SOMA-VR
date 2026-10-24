from pathlib import Path
r=Path.cwd();p=r/'source/s26n.c';s=p.read_text();s=s.replace('static void s26_refresh_native_held_pose(void){','#include "guide_hand_hr.inc"\nstatic void s26_refresh_native_held_pose(void){',1);s=s.replace('if(o_s26MeshCoverage)o_s26MeshCoverage(mesh,coverage);','if(o_s26MeshCoverage)o_s26MeshCoverage(mesh,coverage);\n    if(s26hr_guide_pose(mesh))return;',1)
anchor='    if(h5748t_sso_eq(objectName,"VRMESH",6u))'
code='''    if(h5748t_sso_eq(objectName,"VRGUIDEH",8u)){
        if(h5748t_sso_eq(functionName,"R",1u)){g_s26hrGuideHand=-1;return g_s26hrGuideSuccess;}
        g_s26hrGuideHand=-1;g_s26hrGuideSuccess=0;
        if(g_h576bfMapTransitionActive||h5754h_pause_active()||g_s26CutsceneHandsHidden)return 0;
        for(i32 h=0;h<2;h++){
            char name[2]={(char)('0'+h),0};if(!h5748t_sso_eq(className,name,1u))continue;
            i32 fist=h5748t_sso_eq(functionName,"F",1u);
            if(!fist&&!h5748t_sso_eq(functionName,"O",1u))return 0;
            if(!s26_native_hand_allowed(h)||!s26_install_native_hands())return 0;
            g_s26hrGuideHand=h;g_s26hrGuideFist=fist;return 1;
        }
        return 0;
    }
'''
assert anchor in s;s=s.replace(anchor,code+anchor,1);p.write_text(s)
p=r/'runtime/script/helpers/helper_vr_guidance_hr.hps';s=p.read_text();s += '''
// Uses the same family/rig as the current player, without sampling tracked curls.
class cVRHandGuide
{
    cVRGuideMesh mGuide;
    void Hide(){mGuide.Hide();}
    void Dispose(cWorld@ world){mGuide.Dispose(world);}
    bool Show(cWorld@ world,const tString &in name,const cMatrixf &in transform,int hand,bool fist)
    {
        if(!cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true) ||
           !cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")){Hide();return false;}
        int family=-1;
        for(int f=0;f<4;f++)if(cScript_RunGlobalFunc("VRMESH",""+f,"F")){family=f;break;}
        if(family<0 || hand<0 || hand>1){Hide();return false;}
        array<tString> names={"human","diving","deepsea","deepsea_mutilated"};
        tString side=hand==0 ? "left" : "right";
        if(!mGuide.Show(world,name,"entities/soma_vr/s26f/hand_"+names[family]+"_"+side+".dae",transform))return false;
        for(int b=0;b<mGuide.mpMesh.GetBoneStateNum();b++)mGuide.mpMesh.GetBoneState(b).SetActive(false);
        bool ok=false;
        if(cScript_RunGlobalFunc("VRGUIDEH",""+hand,fist ? "F" : "O")){
            mGuide.mpMesh.SetCoverageAmount(1.0f);
            ok=cScript_RunGlobalFunc("VRGUIDEH","","R");
        }
        if(ok){mGuide.mpMesh.GetBoneStateRoot().UpdateMatrix(true);mGuide.mpMesh.PostUpdateLogic(0.0f);}
        else Hide();
        return ok;
    }
}
''';p.write_text(s)
