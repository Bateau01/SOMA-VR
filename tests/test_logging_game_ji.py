from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text()
s=s.replace("out=R/'audit/jb-env-geometry'", "out=R/'audit/ji-logging/game'").replace('SOMA_VR_IL','SOMA_VR_LOG_JI')
baseline='--baseline' in sys.argv
s=s.replace(' si=subprocess.STARTUPINFO();', ''' put(G/'hpl3vr.dll',(R/'build/native-runtime/hpl3vr.dll').read_bytes())
 put(G/'SOMA-VR-Logging.dll',(R/'runtime/SOMA-VR-Logging.dll').read_bytes())
 put(G/'hpl3vr.log',b'')
 si=subprocess.STARTUPINFO();''')
s=s.replace('creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)', 'creationflags=4|subprocess.BELOW_NORMAL_PRIORITY_CLASS)\n import ctypes\n inj=subprocess.run([str(G/"hpl3vr_inject.exe"),"Soma.exe","hpl3vr.dll"],cwd=G,input="\\n",capture_output=True,text=True,timeout=25)\n assert "SUCCESS" in inj.stdout,inj.stdout+inj.stderr\n resume=ctypes.WinDLL("ntdll").NtResumeProcess;resume.argtypes=[ctypes.c_void_p];resume.restype=ctypes.c_long;assert resume(int(proc._handle))==0')
s=s.replace(" log=(D/", " vrlog=(G/'hpl3vr.log').read_text(errors='replace');(out/(nonce+'-vr.log')).write_text(vrlog)\n assert 'SOMA VR async logging active' in vrlog,vrlog[-2000:]\n log=(D/",1)
if baseline:
 s=s.replace("R/'build/native-runtime/hpl3vr.dll'","R/'installer-jh/payload/hpl3vr.dll'").replace("audit/ji-logging/game","audit/ji-logging/game-baseline").replace(" assert 'SOMA VR async logging active' in vrlog,vrlog[-2000:]"," assert 'SOMA VR async logging active' not in vrlog")
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
