from pathlib import Path
import subprocess,json,sys,uuid
r=Path(__file__).resolve().parents[1];zig=Path(sys.argv[1]).resolve()
subprocess.run([str(zig),'cc','-O2','-municode',str(r/'tests/logging_ji_test.c'),'-o',str(r/'build/logging_ji_test.exe')],check=True)
results=[]
for mode in ['normal']*3+['flood','rotate']:
 out=r/'audit/ji-logging'/('stress-'+mode+'-'+uuid.uuid4().hex);out.mkdir()
 p=subprocess.run([str(r/'build/logging_ji_test.exe'),str(r/'runtime/SOMA-VR-Logging.dll'),str(out),mode],capture_output=True,text=True,check=True)
 files=list(out.glob('hpl3vr.log*'));assert all(f.stat().st_size<=4*1024*1024 for f in files)
 text=(out/'hpl3vr.log').read_text()
 if mode=='normal':assert 'LEGACY STARTUP' in text and 'FINAL SENTINEL' in text and 'repeated 499 additional' in text and 'value 1.2345' in text
 if mode=='rotate':assert len(files)==4 and 'FINAL SENTINEL' in text
 if mode=='flood':assert 'records dropped' in text
 results.append({'mode':mode,'output':p.stdout,'files':{f.name:f.stat().st_size for f in files}})
(r/'audit/ji-logging/benchmark-final.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
