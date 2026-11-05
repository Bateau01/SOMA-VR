"""Interactive authentic Theta ENV fixture. Setup invokes native insertion; player tests actual removal/reinsertion. --smoke compiles and checks native callback chain without VR."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
smoke='--smoke' in sys.argv
sys.argv += ['--inserted']
if smoke: sys.argv += ['--lifecycle']
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/je-env-playtest'")
# Separate profile, never overwrite Main saves/settings.
s=s.replace('SOMA_VR_IL','SOMA_VR_ENV_TEST')
# Add one-time placement AFTER the native insertion setup. No recurring locomotion override.
needle=' i=s.index("{",s.index("class cScrMap"));'
addition='''
 fixture=fixture.replace('LogNewLine("JB_ENV_STATE|', 'cLux_GetPlayer().GetCharacterBody().SetFeetPosition(cVector3f(2.20666f,3.4f,-97.35f),false);cLux_GetPlayer().GetCharacterBody().SetYaw(0);cLux_GetPlayer().GetCamera().SetYaw(0);LogNewLine("ENV_TEST_READY");LogNewLine("JB_ENV_STATE|',1)
'''
if not smoke:
 addition+='''
 fixture=fixture.replace('cEngine_Exit();','')
 candidate=(R/'build/je-env/hpl3vr.dll').read_bytes()
 assert hashlib.sha256(candidate).hexdigest()=='1d3495ffe86fadda0705f13686d2881fef36f1ea1428cdc6f2dcbc70e8d07c8d','Revalidate fixture against the new runtime before use'
 put(G/'hpl3vr.dll',candidate)
 for name in ('hpl3vr_vr_settings.ini','hpl3vr_simulation_rate.txt','item_grips.dat'):
  src=Path('D:/SteamLibrary/steamapps/common/SOMA')/name
  if src.exists():put(G/name,src.read_bytes())
'''
addition+='\n fixture=fixture.replace("mbJBPrepared=true;", "mbJBPrepared=true;Entity_SetActive(\\"brandon_chip_interact\\",false);")\n fixture=fixture.replace(\'LogNewLine("JB_ENV_STATE|\',\'LogNewLine("JD_FIXTURE_OLD_AREA|active="+Entity_IsActive("brandon_chip_interact"));LogNewLine("JB_ENV_STATE|\',1)\n'

s=s.replace(needle,addition+needle)
if not smoke:
 s=s.replace('si.wShowWindow=0','si.wShowWindow=1')
 s=s.replace('creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)', 'creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n import ctypes\n inj=subprocess.run([str(G/"hpl3vr_inject.exe"),"Soma.exe","hpl3vr.dll"],cwd=G,input="\\n",capture_output=True,text=True,timeout=25)\n assert "SUCCESS" in inj.stdout,inj.stdout+inj.stderr\n resume=ctypes.WinDLL("ntdll").NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0\n print("Theta ENV test running. Exit SOMA normally when finished; this launcher restores the isolated files.",flush=True)')
 s=s.replace('proc.wait(timeout=60)','proc.wait()')

# Interactive motion-controller fixture: desktop mouse movement must not steer
# the camera while the automated launcher owns desktop focus. GUI pointing and
# direct OpenXR analog turning do not use this native mouse sensitivity.
s=s.replace(" si=subprocess.STARTUPINFO();", " settings=settings.replace('SmoothMouse=\"true\"', 'SmoothMouse=\"false\"');settings+='\\n<Input MouseSensitivity=\"0\" SmoothMouse=\"false\" />\\n';put(G/'config/il_user.cfg',settings);put(D/'SOMA_VR_ENV_TEST/IL_user_settings.cfg',settings)\n si=subprocess.STARTUPINFO();")
s=s.replace(" log=(D/"," if (G/'hpl3vr.log').exists():(out/(nonce+'-vr.log')).write_bytes((G/'hpl3vr.log').read_bytes())\n log=(D/",1)
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
