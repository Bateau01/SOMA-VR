from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'tests/test_escape_hw.py'
s=p.read_text().replace('fixtures/escape_hw.hps','fixtures/escape_visual_hy.hps')
s=s.replace('si.wShowWindow=0','si.wShowWindow=1').replace('timeout=90','timeout=180')
s=s.replace("source=source.replace('void Update(float dt){','int mlHXUpdateCalls=0; void Update(float dt){mlHXUpdateCalls++;',1)","source=source.replace('void Update(float dt){','int mlHXUpdateCalls=0; void Update(float dt){mlHXUpdateCalls++; HYCamera();',1)")
s=s.replace("out=R/'docs/v109-evidence';", "out=R/'docs/v109-evidence';out.mkdir(parents=True,exist_ok=True);")
(R/'tests/test_escape_visual_hy.py').write_text(s)
(R/'tests/fixtures/escape_visual_hy.hps').write_text('''
    bool mbHYCamera=false;
    void HYCamera(){if(!mbHYCamera)return;
        cLux_GetPlayer().GetCamera().SetPosition(cVector3f(18.15,252.7,-130.1));
        cLux_GetPlayer().GetCamera().SetYaw(-1.5707963f);
        cLux_GetPlayer().GetCamera().SetPitch(0);
    }
    void HRSmokeExit(const tString &in timer){
        Player_ChangeStateToNormal();Effect_Fade_In(0);
        CollideHoleArea("player","AreaClimbHole_FloorZone",1);
        mbHYCamera=true;HYCamera();
        Map_AddTimer("hy_capture",3,"HYCapture");
    }
    void HYCapture(const tString &in timer){
        cLux_SaveScreenshotToFile(tWString("hy_escape.tga"));
        LogNewLine("HY_CAPTURE_REQUEST");
        Map_AddTimer("hy_finish",120,"HYFinish");
    }
    void HYFinish(const tString &in timer){LogNewLine("HR_STORY_DONE|01_03_upsilon_outside");cEngine_Exit();}
''')

