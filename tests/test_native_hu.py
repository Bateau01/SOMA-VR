"""Native map probes; synthetic VR flag/starting state, not physical-controller or full-story tests."""
from pathlib import Path
import subprocess,sys,re,json,os
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);saved={};proc=None
assert 'validation' in G.parts
assert subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Soma,Soma_NoSteam -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True).stdout.strip()=='0'
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
out=R/'docs/v109-evidence';out.mkdir(parents=True,exist_ok=True)
try:
 if os.environ.get('HU_NATIVE_EXE'):put(G/'Soma.exe',Path(os.environ['HU_NATIVE_EXE']).read_bytes())
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 if os.environ.get('HU_BASELINE_BUTTON'):
  put(G/'script/props/Prop_MovingButton.hps',(R.parent.parent/'SOMA_VR_109_S26HT/repo/runtime/script/props/Prop_MovingButton.hps').read_bytes())
 state=(G/'script/player/PlayerState_Interact_Terminal.hps').read_text()
 marker='    bool VR_WorldControlsAllowed()'
 probe=r'''
    void _Global_HUPolicy(){
        cLuxProp@ laptop=Map_GetProp("laptop_touchscreen_1");
        bool ok=laptop !is null;
        if(laptop !is null){
            mPropID=laptop.GetID();mlPreviousState=ePlayerState_Normal;mbVRLeaveOwnsSequence=true;
            ok=ok&&VR_WorldControlsAllowed();
            mlPreviousState=ePlayerState_InteractiveCameraAnimation;ok=ok&&!VR_WorldControlsAllowed();
            mlPreviousState=ePlayerState_Normal;mbVRLeaveOwnsSequence=false;ok=ok&&VR_WorldControlsAllowed();
            mbVRLeaveOwnsSequence=true;
            cLuxProp@ other=Map_GetProp("laptop_touchscreen_1");
            mPropID=tID();ok=ok&&!VR_WorldControlsAllowed();
        }
        LogNewLine("HU_TERMINAL|gates="+ok);
    }
'''
 state=state.replace(marker,probe+marker);put(G/'script/player/PlayerState_Interact_Terminal.hps',state)
 for p in (R/'runtime/maps').rglob('*.hpm_Area'):put(G/'maps'/p.relative_to(R/'runtime/maps'),p.read_bytes())
 for p in (R/'runtime/entities/soma_vr/guidance').rglob('*'):
  if p.is_file():put(G/'entities/soma_vr/guidance'/p.relative_to(R/'runtime/entities/soma_vr/guidance'),p.read_bytes())
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig')
 needle='void GuiMainMenuSelection()\n\t{'
 menu=menu.replace('void GuiMainMenuSelection()','bool mbHRTestStarted=false;\n void GuiMainMenuSelection()',1)
 menu=menu.replace(needle,needle+'\n if(!mbHRTestStarted){mbHRTestStarted=true;ClickNewGame();}',1)
 menu=menu.replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false')
 menu=menu.replace('cScript_SetGlobalReturnBool(gbHPL3VRRuntimeActive);','cScript_SetGlobalReturnBool(true);')
 menu=menu.replace('    tString HPL3VR_BindingAction(int role)',r'''
    void _Global_HULabels(){
        mvVRBindingProfiles[0]=0;mvVRBindingProfiles[1]=0;
        bool ok=HPL3VR_BindingButton(0)=="RIGHT A" && HPL3VR_BindingButton(1)=="RIGHT B" &&
            HPL3VR_BindingButton(2)=="LEFT X" && HPL3VR_BindingButton(3)=="LEFT Y";
        mvVRBindingProfiles[0]=1;ok=ok&&HPL3VR_BindingButton(2)=="LEFT A";
        mvVRBindingProfiles[0]=5;ok=ok&&HPL3VR_BindingButton(2)=="D-PAD LEFT";
        mvVRBindingProfiles[0]=-1;ok=ok&&HPL3VR_BindingButton(2)=="CONTROLLER NOT DETECTED";
        LogNewLine("HU_LABELS|gates="+ok);
    }
    tString HPL3VR_BindingAction(int role)''')
 put(G/'script/modules/MenuHandler.hps',menu)
 put(G/'config/hr_story_user.cfg',(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" />\n<Engine LimitFPS="false" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />')
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 results=[]
 for name in sys.argv[2:] or ['03_02_omicron_inside','05_01_phi_inside']:
  p=next((R/'runtime/maps').rglob(name+'.hps'));rel=p.relative_to(R/'runtime');s=p.read_text(encoding='utf-8-sig')
  probe=r'''
    void HUProbe(const tString &in name){
        cScript_RunGlobalFunc("MenuHandler","cScrMenuHandler","_Global_HULabels");
        array<tString> variants={"omnitool","omnitool_with_securitychip","omnitool_with_cortexchip","omnitool_with_securitychip_cortexchip"};
        bool models=true;cVRGuideMesh guide;
        for(uint v=0;v<variants.length();v++){
            models=models&&guide.Show(cLux_GetCurrentMap().GetWorld(),"HUOmni_"+v,
                "entities/station/gameplay/omnitool/"+variants[v]+".dae",cMatrixf_Identity);
            guide.Dispose(cLux_GetCurrentMap().GetWorld());
        }
        LogNewLine("HU_MODELS|gates="+models);
        array<tString> chairs={"chair_scan_1","pilot_seat"};
        for(uint i=0;i<chairs.length();i++){
            iLuxEntity@ ent=Map_GetEntity(chairs[i]);cLuxProp@ chair=Map_GetProp(chairs[i]);
            LogNewLine("HU_CHAIR|"+chairs[i]+"|entity="+(ent !is null)+"|prop="+(chair !is null));
            if(chair is null)continue;
            LogNewLine("HU_CHAIR|bodies="+chair.GetBodyNum()+"|callback="+chair.HasPlayerInteractCallback()+"|class="+chair.GetClassName());
            if(chair.GetMeshEntity() is null)continue;
            for(int j=0;j<chair.GetMeshEntity().GetSubMeshEntityNum();j++){
                cSubMeshEntity@ sub=chair.GetMeshEntity().GetSubMeshEntity(j);
                LogNewLine("HU_MESH|"+chairs[i]+"|"+j+"|pos="+sub.GetWorldMatrix().GetTranslation()+"|up="+sub.GetWorldMatrix().GetUp());
            }
        }
        HUPhiProbe();
        iLuxEntity@ gate=Map_GetEntity("Area_ScanChair");
        bool seatOK=gate !is null;
        gate.SetActive(false);
        for(int h=0;h<2;h++){
            iLuxEntity@ arm=Map_GetEntity("VRSeatArm_"+h);
            if(arm is null){seatOK=false;continue;}
            arm.SetActive(true);
            seatOK=seatOK&&!arm.CanInteract(0,arm.GetMainBody());
            gate.SetActive(true);gate.SetInteractionDisabled(false);
            seatOK=seatOK&&arm.CanInteract(0,arm.GetMainBody());
            gate.SetInteractionDisabled(true);
            seatOK=seatOK&&!arm.CanInteract(0,arm.GetMainBody());
            gate.SetInteractionDisabled(false);gate.SetActive(false);
            LogNewLine("HU_ARM|"+h+"|point="+arm.GetMatrix().GetTranslation());
        }
        LogNewLine("HU_SEAT|gates="+seatOK);
        LogNewLine("HU_DONE");cEngine_Exit();
    }
'''
  if name=='05_01_phi_inside':
   probe+=r'''
    void HUPhiProbe(){
        iLuxEntity@ b=Map_GetEntity("LaunchButton");
        bool ok=!VR_CanPressLaunchButton();
        bool disabled=b.GetInteractionDisabled();
        ok=ok&&!b.CanInteract(0,b.GetMainBody());
        mbVRLaunchButtonWindow=false;b.SetInteractionDisabled(false);
        ok=ok&&!VR_CanPressLaunchButton();
        ok=ok&&!b.CanInteract(0,b.GetMainBody());
        b.SetInteractionDisabled(true);mbVRLaunchButtonWindow=true;
        ok=ok&&!VR_CanPressLaunchButton();
        b.SetInteractionDisabled(false);mbControllingLoaderArm=false;mbARKLaunched=false;
        ok=ok&&VR_CanPressLaunchButton();
        ok=ok&&b.CanInteract(0,b.GetMainBody());
        mbControllingLoaderArm=true;ok=ok&&!VR_CanPressLaunchButton();mbControllingLoaderArm=false;
        mbARKLaunched=true;ok=ok&&!VR_CanPressLaunchButton();mbARKLaunched=false;
        mbVRLaunchButtonWindow=false;b.SetInteractionDisabled(disabled);
        TerminalLaunchInteract_OnPlayerInteract("LaunchButton");
        LogNewLine("HU_LAUNCH|deniedTimer="+Map_TimerExists("LaunchSequenceMicroDelay"));
        ok=ok&&!mbVRLaunchButtonWindow&&!Map_TimerExists("LaunchSequenceMicroDelay");
        mbVRLaunchButtonWindow=true;b.SetInteractionDisabled(false);
        TerminalLaunchInteract_OnPlayerInteract("LaunchButton");
        LogNewLine("HU_LAUNCH|acceptedTimer="+Map_TimerExists("LaunchSequenceMicroDelay")+"|disabled="+b.GetInteractionDisabled()+"|window="+mbVRLaunchButtonWindow);
        ok=ok&&Map_TimerExists("LaunchSequenceMicroDelay")&&b.GetInteractionDisabled()&&!mbVRLaunchButtonWindow;
        Map_RemoveTimer("LaunchSequenceMicroDelay");
        TerminalLaunchInteract_OnPlayerInteract("TerminalLaunchInteract");
        LogNewLine("HU_LAUNCH|repeatTimer="+Map_TimerExists("LaunchSequenceMicroDelay"));
        ok=ok&&mlHUAccepted==1;
        LogNewLine("HU_PHI|gates="+ok);
    }
'''
  else:probe+='void HUPhiProbe(){}\n'
  if name=='05_01_phi_inside':
   probe+='int mlHUAccepted=0;\n'
   needle='if(!VR_CanPressLaunchButton())return;\n\t\t\tmbVRLaunchButtonWindow=false;'
   assert needle in s
   s=s.replace(needle,'if(!VR_CanPressLaunchButton())return;\n            mlHUAccepted++;\n\t\t\tmbVRLaunchButtonWindow=false;',1)
  if name=='00_01_apartment':
   probe='void HUProbe(const tString &in name){cScript_RunGlobalFunc("State_Interact_Terminal","cScrPlayerState_Interact_Terminal","_Global_HUPolicy");LogNewLine("HU_DONE");cEngine_Exit();}\n'
  i=s.index('{',s.index('class cScrMap'));s=s[:i+1]+probe+s[i+1:]
  m=re.search(r'void OnEnter\(\)\s*\{',s);s=s[:m.end()]+'\n Map_AddTimer("HUProbe",4,"HUProbe");'+s[m.end():];put(G/rel,s)
  cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab','SOMA_VR_HR_Story').replace('config/default_user_settings.cfg','config/hr_story_user.cfg').replace('vr_pump_lab.hpm',name+'.hpm').replace('maps/vr_pump_lab/',rel.parent.as_posix()+'/');put(G/'config/hr_story_init.cfg',cfg)
  si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=0
  proc=subprocess.Popen([str(G/'Soma.exe'),'-user','HRStory','-cfg','config/hr_story_init.cfg'],cwd=G,startupinfo=si)
  try:rc=proc.wait(timeout=75)
  except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
  prefix='baseline_' if os.environ.get('HU_BASELINE_BUTTON') else ('store_' if os.environ.get('HU_NATIVE_EXE') else '')
  log=(docs/'My Games/Soma/SOMA_VR_HR_Story/hpl.log').read_text(errors='replace');(out/(prefix+name+'_hu.log')).write_text(log)
  rows=[x for x in log.splitlines() if 'HU_' in x or ' : ERR ' in x or 'FATAL ERROR' in x]
  ok='HU_DONE' in log and ' : ERR ' not in log and 'FATAL ERROR' not in log and 'gates=false' not in log
  results.append({'map':name,'passed':ok,'lines':rows});print(json.dumps(results[-1]),flush=True)
  if not ok:break
 (out/'native_hu.json').write_text(json.dumps(results,indent=2))
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait()
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
raise SystemExit(not all(x['passed'] for x in results))

