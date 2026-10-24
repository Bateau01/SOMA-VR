"""Production phone script in native engine, mocked OpenXR/native grip commands.
Moves actual phone body out of reach and advances production recovery; not story/haptic validation.
"""
from pathlib import Path
import sys,subprocess,time,json,uuid,re
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);saved={};proc=None
out=R/'audit/phone-recovery-IS'/uuid.uuid4().hex[:8];out.mkdir(parents=True)
def put(p,b):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode())
try:
 for p in (R/'runtime/script').rglob('*.hps'):put(G/'script'/p.relative_to(R/'runtime/script'),p.read_bytes())
 for root in ['entities/vr','entities/soma_vr/guidance']:
  for p in (R/'runtime'/root).rglob('*'):
   if p.is_file():put(G/root/p.relative_to(R/'runtime'/root),p.read_bytes())
 helper=(R/'runtime/script/helpers/helper_vr_phone_q.hps').read_text()
 a=helper.index('bool VRPhoneQ_Active()');b=helper.index('class cVRPhoneQ',a)
 adapter='''bool testHeld=false,testRetrieve=false,testAccept=false,testGuides=true;int testShown=0,testChecks=0,testFails=0;
void Check(bool ok,const tString &in name){testChecks++;if(!ok)testFails++;LogNewLine("PHONE_CHECK|"+name+"|"+ok);}
bool VRPhoneQ_Active(){return true;}
bool TestBridge(const tString &in obj,const tString &in owner,const tString &in cmd){
 if(obj=="VRPHONEX"){
 if(cmd=="G"){bool r=testRetrieve;testRetrieve=false;return r;}
 if(cmd=="A"){bool r=testAccept;testAccept=false;return r;}
 if(cmd=="J")return false;
 if(cmd=="R")testHeld=true;
 return true;
 }
 if(obj=="VRPHONEQ")return testHeld;
 if(obj=="VRGUIDE"){
 if(cmd=="ACTIVE")return testGuides;
 if(cmd=="PHONE")cScript_SetGlobalReturnVector3f(cLux_GetPlayer().GetCamera().GetPosition()+cVector3f(0,0,-.6f));
 if(cmd=="PHONE_ROW0")cScript_SetGlobalReturnVector3f(cVector3f(1,0,0));
 if(cmd=="PHONE_ROW1")cScript_SetGlobalReturnVector3f(cVector3f(0,1,0));
 if(cmd=="PHONE_ROW2")cScript_SetGlobalReturnVector3f(cVector3f(0,0,1));
 return true;
 }
 return false;
}
'''
 helper=helper[:a]+adapter+helper[b:]
 helper=helper.replace('cScript_RunGlobalFunc(', 'TestBridge(')
 helper=helper.replace('if(valid) mVRPhoneGuide.Show(world,"VRPhoneGuide","entities/urban/tech/cellphone/cellphone_smartphone.dae",frame);','if(valid && mVRPhoneGuide.Show(world,"VRPhoneGuide","entities/urban/tech/cellphone/cellphone_smartphone.dae",frame)) testShown++;')
 if '--baseline' in sys.argv:helper=helper.replace('(state==1 || (state==2 && pocket))','state==1')
 put(G/'script/helpers/helper_vr_phone_q.hps',helper)
 menu=(G/'script/modules/MenuHandler.hps').read_text(encoding='utf-8-sig');needle='void GuiMainMenuSelection()\n\t{';assert needle in menu
 menu=menu.replace('void GuiMainMenuSelection()','bool testStarted=false;\nvoid GuiMainMenuSelection()',1).replace(needle,needle+'\nif(!testStarted){testStarted=true;ClickNewGame();}',1).replace('mpConfig.GetBool("Main", "ShowPreMenu", true)','false');put(G/'script/modules/MenuHandler.hps',menu)
 fixture='''#include "interfaces/Map_Interface.hps"
#include "helpers/helper_map.hps"
#include "helpers/helper_imgui.hps"
#include "helpers/helper_audio.hps"
#include "helpers/helper_vr_phone_q.hps"
class cScrMap : iScrMap {
 float age=0;bool done=false;cVRPhoneQ p;
 void Setup(){}void OnEnter(){}void OnLeave(){}void OnStart(){}
 void Update(float dt){age+=dt;if(done||age<3)return;done=true;
 cLux_GetUserConfig().SetBool("SOMA_VR","InteractionGuides",true);
 for(int route=0;route<3;route++){
 testHeld=false;testGuides=true;testShown=0;
 if(route==0){cMatrixf m=cMatrixf_Identity;m.SetTranslation(cLux_GetPlayer().GetCamera().GetPosition());Check(p.Spawn(m),"scene spawn");}
 Check(p.Begin(route==0 ? "VR_StoryPhone_Q" : ""),"begin "+route);
 if(route>0){testRetrieve=true;p.Tick(0);}else testHeld=true;
 Check(!p.pocket && p.state==1,"initial held");
 testAccept=true;Check(p.Tick(0)==1 && p.state==2,"accept once");Check(p.Tick(0)==0,"no duplicate accept");
 testHeld=false;cMatrixf far=cMatrixf_Identity;far.SetTranslation(cLux_GetPlayer().GetCamera().GetPosition()+cVector3f(3,0,0));p.Entity().SetMatrix(far);
 for(int i=0;i<65;i++)p.Tick(0);
 Check(p.pocket && p.state==2 && !p.Entity().IsActive(),"out of reach recovery");
 testShown=0;p.Tick(0);Check(testShown==1,"answered recovery guide");
 testGuides=false;testShown=0;p.Tick(0);Check(testShown==0,"native eligibility denied");testGuides=true;
 cLux_GetUserConfig().SetBool("SOMA_VR","InteractionGuides",false);p.Tick(0);Check(testShown==0,"guide off");cLux_GetUserConfig().SetBool("SOMA_VR","InteractionGuides",true);
 testRetrieve=true;p.Tick(0);Check(!p.pocket && testHeld && p.state==2,"recover to hand");testShown=0;p.Tick(0);Check(testShown==0,"held answered hides guide");
 p.End();testShown=0;p.Tick(0);Check(p.state==0 && !p.pocket && testShown==0,"end cleanup");
 }
 Check(p.Begin(""),"begin timeout");p.Tick(.01f);testShown=0;p.Tick(0);Check(p.state==3 && testShown==0,"expired hidden");p.End();
 LogNewLine("PHONE_RECOVERY_DONE|checks="+testChecks+"|failures="+testFails);cEngine_Exit();
 }
}
'''
 put(G/'maps/vr_pump_lab/vr_pump_lab.hps',fixture)
 profile='SOMA_VR_PhoneRecovery_'+out.name
 defaults=(G/'config/default_user_settings.cfg').read_text()+'\n<Screen Width="960" Height="540" FullScreen="false" Vsync="true" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n';put(G/'config/phone_recovery_user.cfg',defaults)
 cfg=(G/'config/pump_lab_init.cfg').read_text().replace('SOMA_VR_PumpLab',profile).replace('config/default_user_settings.cfg','config/phone_recovery_user.cfg');put(G/'config/phone_recovery_init.cfg',cfg)
 proc=subprocess.Popen([str(G/'Soma.exe'),'-user','Recovery','-cfg','config/phone_recovery_init.cfg'],cwd=G,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 try:proc.wait(timeout=45)
 except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10)
 docs=Path(subprocess.run(['powershell','-NoProfile','-Command',"[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 log=(docs/'My Games/Soma'/profile/'hpl.log').read_text(errors='replace');(out/'native.log').write_text(log)
 lines=[s for s in log.splitlines() if 'PHONE_CHECK' in s or 'PHONE_RECOVERY_DONE' in s or ' : ERR ' in s];print(json.dumps({'output':str(out),'baseline':'--baseline' in sys.argv,'lines':lines[:60]}),flush=True)
 (out/'result.json').write_text(json.dumps({'scope':__doc__,'baseline':'--baseline' in sys.argv,'lines':lines},indent=2))
finally:
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 (out/'restoration.json').write_text(json.dumps({'restored':all(p.read_bytes()==b if b is not None else not p.exists() for p,b in saved.items())}))
