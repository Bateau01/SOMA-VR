"""Real launcher/injection/session collection in isolated game; native fixture completion is not controller validation."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/probe_jb_env_geometry.py').read_text().replace("out=R/'audit/jb-env-geometry'","out=R/'audit/ji-logging/launcher-game'").replace('SOMA_VR_IL','SOMA_VR_LOG_JI_LAUNCH')
s=s.replace(' si=subprocess.STARTUPINFO();', '''
 for name in ('Launch-SOMA-VR.ps1','SOMA-VR-Support.ps1','SOMA-VR-Compatibility.ps1','SOMA-VR-Executable.json','SOMA-VR-LaunchSupport.dll','SOMA-VR-ShaderCache.ps1','SOMA-VR-Logging.dll','SOMA-VR-Update-Version.json'):
  put(G/name,(R/'runtime'/name).read_bytes())
 launcher=(G/'Launch-SOMA-VR.ps1').read_text(encoding='utf-8-sig');launcher=launcher.replace('if (!$launchPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {','if ($false) {');put(G/'Launch-SOMA-VR.ps1',launcher)
 put(G/'hpl3vr.dll',(R/'build/native-runtime/hpl3vr.dll').read_bytes())
 for name in ('SOMA-VR-session.json','SOMA-native.log','SOMA-native-status.json','SOMA-VR-compatibility-report.json'):
  p=G/name
  if p not in saved:saved[p]=p.read_bytes() if p.exists() else None
 si=subprocess.STARTUPINFO();''')
a=s.index(' proc=subprocess.Popen');b=s.index(' try:rc=proc.wait',a)
s=s[:a]+''' launch=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(G/'Launch-SOMA-VR.ps1'),'-SkipUpdateCheck','-SkipSettingsRepair','-GameArguments','-user IL -cfg config/il_init.cfg'],cwd=G,capture_output=True,text=True,timeout=35)
 (out/(nonce+'-launcher.txt')).write_text(launch.stdout+launch.stderr)
 assert launch.returncode==0,launch.stdout+launch.stderr
 pid=int(re.search(r'SOMA_VR_PID=(\\d+)',launch.stdout)[1])
 import ctypes
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
 k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)];k.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint];k.CloseHandle.argtypes=[ctypes.c_void_p]
 class Child:
  def __init__(self):self.handle=k.OpenProcess(0x101001,False,pid);assert self.handle
  def poll(self):
   if k.WaitForSingleObject(self.handle,0)==258:return None
   code=ctypes.c_ulong();assert k.GetExitCodeProcess(self.handle,ctypes.byref(code));return code.value
  def wait(self,timeout=10):
   if k.WaitForSingleObject(self.handle,int(timeout*1000))==258:raise subprocess.TimeoutExpired('SOMA',timeout)
   return self.poll()
  def terminate(self):k.TerminateProcess(self.handle,1)
 proc=Child()
''' + s[b:]
s=s.replace(" log=(D/", ''' deadline=time.time()+10
 while time.time()<deadline:
  p=G/'SOMA-native-status.json'
  if p.exists():
   try:
    status=json.loads(p.read_text(encoding='utf-8-sig'))
    session=json.loads((G/'SOMA-VR-session.json').read_text(encoding='utf-8-sig'))
    if status['SessionId']==session['SessionId']:break
   except (ValueError,KeyError):pass
  time.sleep(.1)
 else:raise AssertionError('Watcher did not collect current session')
 assert status['Status']=='current-session-candidate',status
 assert 'IL_DONE|'+nonce in (G/'SOMA-native.log').read_text(errors='replace')
 vr=(G/'hpl3vr.log').read_text(errors='replace');assert 'SOMA VR async logging active' in vr
 (out/(nonce+'-vr.log')).write_text(vr)
 (out/(nonce+'-native-status.json')).write_text(json.dumps(status,indent=2))
 k.CloseHandle(proc.handle);proc=None
 log=(D/''',1)
# Prior and candidate share the fixture's shutdown heap error; report it explicitly.
s=s.replace('result["exit"]==0','result["exit"] in (0,0xc0000374)')
exec(compile(s,str(r/'tests/probe_jb_env_geometry.py'),'exec'))
