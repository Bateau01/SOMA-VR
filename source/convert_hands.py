from pathlib import Path
import subprocess,shutil,time,json,hashlib
R=Path(__file__).resolve().parents[1];C=R/'build/converter';A=R/'runtime/entities/soma_vr/s26f'
out=C/'entities/soma_vr/s26f';report=[]
for p in A.iterdir():
 if p.suffix in ['.dae','.dds','.mat']:shutil.copy2(p,out/p.name)
for p in sorted(out.glob('hand_*.dae')):
 cache=p.with_suffix('.msh')
 if cache.exists():cache.unlink()
 # Only our private converter process and staging files are affected.
 si=subprocess.STARTUPINFO();si.dwFlags=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 log=C/'HPL3/modelview.log'
 if log.exists():log.unlink()
 proc=subprocess.Popen([str(C/'ModelViewer.exe'),str(p)],cwd=C,startupinfo=si)
 try:
  for i in range(100):
   time.sleep(.2)
   if cache.exists() and cache.stat().st_size>1000:
    time.sleep(2);break
   if proc.poll() is not None:raise RuntimeError('Converter exited: '+p.name)
  else:raise RuntimeError('Converter timed out: '+p.name)
 finally:
  if proc.poll() is None:proc.terminate()
  proc.wait(timeout=10)
 text=log.read_text(errors='replace');(R/'audit'/(p.stem+'_import.log')).write_text(text)
 assert 'not connected to a bone' not in text,p.name
 assert "Couldn't create material" not in text,p.name
 shutil.copy2(cache,A/cache.name)
 report.append({'mesh':p.stem,'bytes':cache.stat().st_size,'sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'native_import':'PASS','importer_repaired_tangents':'Free floating vertices' in text})
 print(p.stem+': native import PASS',flush=True)
(R/'audit/native_import.json').write_text(json.dumps(report,indent=2))
