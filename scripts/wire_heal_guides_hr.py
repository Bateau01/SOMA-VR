from pathlib import Path
r=Path.cwd();p=r/'runtime/script/helpers/helper_vr_guidance_hr.hps';s=p.read_text();s+='''
// Hand meshes extend along local -Y and bend toward local -Z.
// Open palm faces the surface; closed knuckles point into its opening.
cMatrixf VRGuide_HandFrame(const cVector3f &in point,const cVector3f &in outward,bool fist)
{
    cVector3f n=cMath_Vector3Normalize(outward);
    cVector3f reference=cVector3f(0,1,0);
    if(cMath_Abs(n.y)>0.9f)reference=cVector3f(0,0,1);
    cVector3f right=cMath_Vector3Normalize(cMath_Vector3Cross(reference,n));
    cVector3f tangent=cMath_Vector3Normalize(cMath_Vector3Cross(n,right));
    cMatrixf frame=cMatrixf_Identity;
    frame.SetRight(right);frame.SetUp(fist ? n : tangent);
    frame.SetForward(fist ? -tangent : n);
    frame.SetTranslation(point+n*(fist ? 0.04f : 0.025f));return frame;
}
''';p.write_text(s)
p=r/'runtime/script/props/Prop_EnergySource.hps';s=p.read_text();s='#include "helpers/helper_vr_guidance_hr.hps"\n'+s
s=s.replace('    [nosave] cVector3f mvVRMouth;','    [nosave] cVRHandGuide mVRHealGuide;\n    [nosave] float mfVRGuideLease=0;\n    [nosave] cVector3f mvVRMouth;',1)
s=s.replace('void OnUpdate(float afTimeStep) {}','''void OnUpdate(float afTimeStep) {
        mfVRGuideLease-=afTimeStep;
        if(mfVRGuideLease<=0 || !VR_CanStartHeal() ||
           !cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true))mVRHealGuide.Hide();
    }''',1)
needle='        if(stage>=2) mvVRMouth-=axis*0.070f;';s=s.replace(needle,needle+'''
        mfVRGuideLease=0.15f;
        mVRHealGuide.Show(cLux_GetCurrentMap().GetWorld(),"VRHealGuide_"+mBaseObj.GetName(),
            VRGuide_HandFrame(mvVRMouth,axis,stage>=2),0,stage>=2);''',1)
import re
m=re.search(r'(void BeforeEntityDestruction\(\)\s*\{)',s);assert m;s=s[:m.end()]+'\n        mVRHealGuide.Dispose(cLux_GetCurrentMap().GetWorld());'+s[m.end():];p.write_text(s)
p=r/'runtime/maps/chapter04/04_03_tau_escape/04_03_tau_escape.hps';s=p.read_text();s='#include "helpers/helper_vr_guidance_hr.hps"\n'+s
s=s.replace('[nosave] float mfVRAlphaPoll = 0;','[nosave] cVRHandGuide mVRAlphaGuide;\n\t[nosave] float mfVRAlphaPoll = 0;',1)
s=s.replace('if(!_HPL3VR_AlphaActive() || !HPL3VR_AlphaEligible()) return;','mVRAlphaGuide.Hide();\n        if(!_HPL3VR_AlphaActive() || !HPL3VR_AlphaEligible()) return;',1)
s=s.replace('cVector3f target=rim+axis*0.22f;','''cVector3f target=rim+axis*0.22f;
        mVRAlphaGuide.Show(cLux_GetCurrentMap().GetWorld(),"VRAlphaHandGuide",
            VRGuide_HandFrame(target,axis,true),0,true);''',1)
s=s.replace('void OnLeave()\n\t{','void OnLeave()\n\t{\n        mVRAlphaGuide.Dispose(cLux_GetCurrentMap().GetWorld());',1);p.write_text(s)
# Retain same-world guide ownership on Reset; OnMapLeave destroys it.
p=r/'runtime/script/modules/PlayerToolHandler.hps';s=p.read_text();s=s.replace('VR_HideItemGuides();mvVRItemGuides.resize(0);mfVRItemGuidePoll=0;','VR_HideItemGuides();mfVRItemGuidePoll=0;',1);p.write_text(s)
