"""Real native GUI construction/destruction with private observer; no VR pixel proof."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'","out=R/'audit/jb-cursor-lifetime'")
start=s.index(" fixture='");end=s.index(" if '--inserted'",start)
fixture=r'''
 [nosave] float mfJBClock=0;
 void JBProbe(float dt){
  mfJBClock+=dt;if(mfJBClock<3 || mfJBClock>3+dt)return;
  cGuiSet@ set=cGui_CreateSet("JBPrivateLifecycle",null);
  if(set is null){LogNewLine("JB_ENV_MISSING|GuiSet");cEngine_Exit();return;}
  for(int i=0;i<20;i++){
   cImGui@ gui=cGui_CreateImGui("JBPrivateLifecycleGui",set);
   if(gui is null){LogNewLine("JB_ENV_MISSING|ImGui");break;}
   cGui_DestroyImGui(gui);@gui=null;
   LogNewLine("JB_ENV_GUI_DESTROYED|"+i);
  }
  cGui_DestroySet(set);@set=null;
  LogNewLine("IL_DONE|NONCE");cEngine_Exit();
 }
'''
s=s[:start]+' fixture='+repr(fixture)+'.replace("NONCE",nonce)\n'+s[end:]
marker=" si=subprocess.STARTUPINFO();"
s=s.replace(marker," put(G/'hpl3vr.dll',(R/'build/jb-cursor/hpl3vr.dll').read_bytes())\n put(G/'hpl3vr.log',b'')\n"+marker)
s=s.replace('creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)','creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)')
s=s.replace(' try:rc=proc.wait(timeout=60)',r'''
 import ctypes
 inj=subprocess.run([str(G/'hpl3vr_inject.exe'),'Soma.exe','hpl3vr.dll'],cwd=G,input='\n',capture_output=True,text=True,timeout=25)
 assert 'SUCCESS' in inj.stdout,inj.stdout+inj.stderr
 resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long
 assert resume(int(proc._handle))==0
 try:rc=proc.wait(timeout=60)''')
s=s.replace(" result={'nonce':", " vrlog=(G/'hpl3vr.log').read_text(errors='replace');(out/(nonce+'-vr.log')).write_text(vrlog)\n result={'nonce':")
if '--uninjected' in sys.argv:
 a=s.index(' inj=subprocess.run(');z=s.index(' resume=ctypes.WinDLL',a)
 s=s[:a]+s[z:]
s=s.replace("'inserted_fixture':'--inserted' in sys.argv", "'inserted_fixture':'--inserted' in sys.argv,'uninjected':'--uninjected' in sys.argv,'test_scope':'Native GUI lifecycle, not VR pixel proof'")
if '--baseline' in sys.argv:s=s.replace('build/jb-cursor/hpl3vr.dll','build/jb-cursor-baseline/hpl3vr.dll')
s=s.replace("'uninjected':'--uninjected' in sys.argv", "'uninjected':'--uninjected' in sys.argv,'without_lifetime_hook':'--baseline' in sys.argv")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
assert log.count('JB_ENV_GUI_DESTROYED|')==20
if '--uninjected' not in sys.argv:
 assert 'TERMINAL CURSOR DRAW FILTER READY' in vrlog
 if '--baseline' not in sys.argv:assert vrlog.count('JB_GUI_DESTROY before')>=20
