"""Interactive authentic Theta ENV fixture. Setup invokes native insertion; player tests actual removal/reinsertion. --smoke compiles and checks native callback chain without VR."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
smoke='--smoke' in sys.argv
sys.argv += ['--inserted']
if smoke: sys.argv += ['--lifecycle']
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/env-panel-playtest'")
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
 candidate=(R/'build/jd-env/hpl3vr.dll').read_bytes()
 assert hashlib.sha256(candidate).hexdigest()=='4692b387568574305d65b5dfd7a0ec278bf0f00bfabe69e2283d12529a02c0ad','Revalidate fixture against the new runtime before use'
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
s=s.replace(" log=(D/"," if (G/'hpl3vr.log').exists():(out/(nonce+'-vr.log')).write_bytes((G/'hpl3vr.log').read_bytes())\n log=(D/",1)
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
