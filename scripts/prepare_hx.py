from pathlib import Path
r=Path('.');p=r/'runtime/script/helpers/helper_vr_escape_hw.hps';s=p.read_text();a=s.index('        // Surface triangle');b=s.index('\n    }',a)
s=s[:a]+'''        iLuxEntity@ area=Map_GetEntity("AreaClimbHole");if(area is null)return;
        // Within the lower, player-facing edge of the authored interaction box.
        // A reach cue, not an extra collider or a new interaction region.
        cMatrixf frame=area.GetMatrix();
        cVector3f at=cMath_MatrixMul(frame,cVector3f(0,-2.12f,.42f));
        if(cMath_Vector3Dist(at,cLux_GetPlayer().GetCamera().GetPosition())>4.0f){Report(3);return;}
        bool shown=mHand.Show(cLux_GetCurrentMap().GetWorld(),"VREscapeLedgeHW",
            VRGuide_HandFrame(at,cMath_Vector3Normalize(frame.GetForward()),false),1,false);
        Report(shown ? 5 : 4);'''+s[b:]
s=s.replace('    float mfPoll=0;','''    float mfPoll=0;
    int mlLastReport=-1;
    void Report(int state){if(state==mlLastReport)return;mlLastReport=state;cScript_RunGlobalFunc("VRESCAPE","",""+state);}''')
s=s.replace('if(!Ready(introOver,escaped) || !cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true)){Hide();return;}','if(!Ready(introOver,escaped)){Hide();Report(1);return;}\n        if(!cLux_GetUserConfig().GetBool("SOMA_VR","InteractionGuides",true)){Hide();Report(2);return;}');p.write_text(s)
p=r/'source/s26n.c';s=p.read_text().replace('S26HW','S26HX')
needle='    if(h5748t_sso_eq(objectName,"VRGUIDEH",8u)){'
block='''    if(h5748t_sso_eq(objectName,"VRESCAPE",8u)){
        static u32 reports; if(reports>=16u)return 1;
        for(i32 i=1;i<=5;i++){char v[2]={(char)('0'+i),0};if(h5748t_sso_eq(functionName,v,1u)){
            const char* reasons[5]={"native gate closed","guide option off","outside 4m range","hand guide creation/pose rejected","hand guide visible"};
            reports++;ext_Log(">>> S26HX ESCAPE GUIDE %u: %s",reports,reasons[i-1]);return 1;
        }}return 0;
    }
'''
assert needle in s;s=s.replace(needle,block+needle,1);p.write_text(s)
for name in ['runtime/script/modules/MenuHandler.hps','installer/source/Build.ps1','installer/source/Installer.cs','installer/source/CurrentUpgradeTests.cs']:
 p=r/name;p.write_bytes(p.read_bytes().replace(b'S26HW',b'S26HX').replace(b'2026102206',b'2026102207'))
s=(r/'scripts/package_hw.py').read_text().replace('S26HW','S26HX').replace('2026102206','2026102207');(r/'scripts/package_hx.py').write_text(s)
