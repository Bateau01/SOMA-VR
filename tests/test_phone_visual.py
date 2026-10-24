"""Native rendered phone guide comparison. Synthetic controller matrices; not headset/grab validation."""
from pathlib import Path
import sys,subprocess,time,json,uuid,ctypes as C
from PIL import Image
from inject_capture_hy import inject
R=Path(__file__).resolve().parents[1];G=Path(sys.argv[1]);z=sys.argv[2];out=R/"audit/phone-guide-rotation"/("visual-"+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
head="#include <math.h>\n#include <string.h>\ntypedef int i32;typedef unsigned u32;\n#define ext_Sqrtf sqrtf\n#define h576c_ci_streq(a,b) (!strcmp(a,b))\ntypedef struct {char name[96];i32 hand,kind;float rotation[9],fraction[3],joint[5][4];} S26EJGrip;\n"
src=head+"\n".join((R/"source"/n).read_text() for n in ["authored_grips_el.inc","holster_grip_ef.inc","phone_guide_frame.inc"])+'\n__declspec(dllexport) int frame(float*b,float*c,float*f){return s26_phone_guide_frame(b,c,f);}\n__declspec(dllexport) void pose(float*r){memcpy(r,s26el_default_grip(1,2,"Phone")->rotation,36);}\n'
p=R/"build/phone_visual_matrix.c";p.write_text(src);dll=p.with_suffix(".dll");subprocess.run([z,"cc","-shared","-O2",str(p),"-o",str(dll)],check=True)
lib=C.CDLL(str(dll));F=C.c_float;rot=(F*9)();lib.pose(rot)
# Controller orientation chosen to hold the phone upright, screen toward viewer.
desired=[[0,0,1],[1,0,0],[0,1,0]];a=[[rot[col*3+row] for col in range(3)] for row in range(3)]
b=[[sum(desired[row][k]*a[col][k] for k in range(3)) for col in range(3)] for row in range(3)]
basis=(F*9)(*[b[row][col] for col in range(3) for row in range(3)]);frame=(F*16)();assert lib.frame(basis,(F*3)(0,0,0),frame)
rows=[",".join(str(float(frame[col*4+row]))+"f" for col in range(3)) for row in range(3)]
saved={};proc=None;start=time.time()
def put(p,data):
 if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode())
try:
 for p in (R/"runtime/script").rglob("*.hps"):put(G/"script"/p.relative_to(R/"runtime/script"),p.read_bytes())
 for p in (R/"runtime/entities/soma_vr/guidance").rglob("*"):
  if p.is_file():put(G/"entities/soma_vr/guidance"/p.relative_to(R/"runtime/entities/soma_vr/guidance"),p.read_bytes())
 menu=(G/"script/modules/MenuHandler.hps").read_text(encoding="utf-8-sig");needle="void GuiMainMenuSelection()\n\t{";assert needle in menu
 menu=menu.replace("void GuiMainMenuSelection()","bool mbPhoneFixture=false;\nvoid GuiMainMenuSelection()",1).replace(needle,needle+"\nif(!mbPhoneFixture){mbPhoneFixture=true;ClickNewGame();}",1);put(G/"script/modules/MenuHandler.hps",menu)
 fixture=r"""#include "interfaces/Map_Interface.hps"
#include "helpers/helper_map.hps"
#include "helpers/helper_player.hps"
#include "helpers/helper_effects.hps"
#include "helpers/helper_vr_guidance_hr.hps"
class cScrMap : iScrMap {
 cVRGuideMesh oldGuide,newGuide;float age=0;int phase=-1;cVector3f eye;bool setup=false;
 void Setup(){} void OnEnter(){} void OnLeave(){oldGuide.Dispose(cLux_GetCurrentMap().GetWorld());newGuide.Dispose(cLux_GetCurrentMap().GetWorld());}
 void OnStart(){Player_SetActive(true);Player_SetHealth(100);Player_SetFallDamageActive(false);Player_ChangeStateToNormal();}
 void Update(float dt){age+=dt;if(age<3)return;
 if(!setup){eye=cLux_GetPlayer().GetCamera().GetPosition();setup=true;LogNewLine("PHONE_VISUAL_BEGIN");}
 Effect_Fade_In(0);cLux_GetPlayer().GetCamera().SetPosition(eye);cLux_GetPlayer().GetCamera().SetPitch(0);
 int next=age<7 ? 0 : (age<11 ? 1 : (age<15 ? 2 : 3));float yaw=next==1 ?.22f:(next==2 ?-.22f:0);
 cLux_GetPlayer().GetCharacterBody().SetYaw(yaw);cLux_GetPlayer().GetCamera().SetYaw(yaw);eye=cLux_GetPlayer().GetCamera().GetPosition();
 cMatrixf oldFrame=cMath_MatrixRotateY(yaw);oldFrame.SetTranslation(eye+cVector3f(-.12f,-.08f,-.55f));
 cMatrixf newFrame=cMatrixf_Identity;newFrame.SetRight(cVector3f(ROW0));newFrame.SetUp(cVector3f(ROW1));newFrame.SetForward(cVector3f(ROW2));newFrame.SetTranslation(eye+cVector3f(.12f,-.08f,-.55f));
 cWorld@ w=cLux_GetCurrentMap().GetWorld();
 bool ok1=oldGuide.Show(w,"OldPhone","entities/urban/tech/cellphone/cellphone_smartphone.dae",oldFrame);
 bool ok2=newGuide.Show(w,"NewPhone","entities/urban/tech/cellphone/cellphone_smartphone.dae",newFrame);
 if(phase!=next){phase=next;LogNewLine("PHONE_VISUAL_PHASE|"+phase+"|old="+ok1+"|new="+ok2+"|eye="+eye.x+","+eye.y+","+eye.z+"|forward="+newFrame.GetForward().x+","+newFrame.GetForward().y+","+newFrame.GetForward().z);}
 if(age>18){oldGuide.Dispose(w);newGuide.Dispose(w);LogNewLine("PHONE_VISUAL_DONE");cEngine_Exit();}
 }
}
"""
 for i,row in enumerate(rows):fixture=fixture.replace("ROW"+str(i),row)
 put(G/"maps/vr_pump_lab/vr_pump_lab.hps",fixture)
 defaults=(G/"config/default_user_settings.cfg").read_text()+'\n<Screen Width="1280" Height="720" FullScreen="false" Vsync="false" RefreshRate="60" />\n<Engine LimitFPS="true" SleepWhenOutOfFocus="false" />\n<Main ShowMenu="false" FirstGameStart="false" SaveConfig="false" />\n'
 put(G/"config/phone_visual_user.cfg",defaults)
 cfg=(G/"config/pump_lab_init.cfg").read_text().replace("SOMA_VR_PumpLab","SOMA_VR_PhoneVisual").replace("config/default_user_settings.cfg","config/phone_visual_user.cfg");put(G/"config/phone_visual_init.cfg",cfg)
 for p in G.glob("hy_frame_*.ppm"):saved[p]=p.read_bytes()
 si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=1
 proc=subprocess.Popen([str(G/"Soma.exe"),"-user","PhoneVisual","-cfg","config/phone_visual_init.cfg"],cwd=G,startupinfo=si,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 time.sleep(2);inject(proc.pid,R/"tests/capture_swap_hy.dll")
 try:rc=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.terminate();rc=proc.wait(timeout=10)
 docs=Path(subprocess.run(["powershell","-NoProfile","-Command","[Environment]::GetFolderPath('MyDocuments')"],capture_output=True,text=True).stdout.strip())
 log=(docs/"My Games/Soma/SOMA_VR_PhoneVisual/hpl.log").read_text(errors="replace");(out/"native.log").write_text(log)
 frames=[]
 for p in G.glob("hy_frame_*.ppm"):
  if p.stat().st_mtime>=start:
   dest=out/(p.stem+".png");Image.open(p).save(dest);frames.append(str(dest))
   if p not in saved:saved[p]=None
 result={"completed":"PHONE_VISUAL_DONE" in log and " : ERR " not in log,"frames":frames,"scope":__doc__,"lines":[x for x in log.splitlines() if "PHONE_VISUAL" in x or " : ERR " in x]};(out/"result.json").write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
finally:
 if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 for p,b in reversed(list(saved.items())):
  if b is None:p.unlink(missing_ok=True)
  else:p.write_bytes(b)
 (out/"restoration.json").write_text(json.dumps({"restored":all((p.read_bytes()==b if b is not None else not p.exists()) for p,b in saved.items())}))

