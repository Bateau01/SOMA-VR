from pathlib import Path
p=Path('tests/test_escape_hw.py');s=p.read_text();needle=" menu=(G/'script/modules/MenuHandler.hps').read_text"
a=s.index(needle)
insert=''' # Native clone/visibility fixture: runtime capability and hand-pose acknowledgement
 # supplied; actual live DLL bone pose and headset appearance are not tested.
 helper=(R/'runtime/script/helpers/helper_vr_guidance_hr.hps').read_text()
 helper=helper.replace('!cScript_RunGlobalFunc("VRGUIDE","","ACTIVE")','false').replace('if(cScript_RunGlobalFunc("VRMESH",""+f,"F"))','if(f==1)').replace('if(cScript_RunGlobalFunc("VRGUIDEH",""+hand,fist ? "F" : "O"))','if(true)').replace('ok=cScript_RunGlobalFunc("VRGUIDEH","","R");','ok=true;')
 put(G/'script/helpers/helper_vr_guidance_hr.hps',helper)
'''
s=s[:a]+insert+s[a:];p.write_text(s)
p=Path('tests/fixtures/escape_hw.hps');s=p.read_text();s=s.replace('        mVREscapeGuide.Update(.2f,true,false);','''        cVector3f at=cMath_MatrixMul(Map_GetEntity("AreaClimbHole").GetMatrix(),cVector3f(0,-2.12f,.42f));
        cLux_GetPlayer().GetCamera().SetPosition(at+cVector3f(-1,0,0));
        mVREscapeGuide.Update(.2f,true,false);
        HWCheck(mVREscapeGuide.mHand.mGuide.Live() && mVREscapeGuide.mHand.mGuide.mpMesh.IsVisible(),"native guide mesh visible with supplied runtime/pose acknowledgement");''');p.write_text(s)
