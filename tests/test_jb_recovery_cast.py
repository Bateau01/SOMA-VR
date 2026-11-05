"""Separate-process Newton cast capability; no live game or recovery implementation."""
from pathlib import Path
import sys,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];exe=r/'build/jb_recovery_cast.exe'
subprocess.run([sys.argv[1],'c++','-O2',str(r/'tests/jb_recovery_cast.cpp'),'-o',str(exe)],check=True)
results=[]
for game in [Path(r'D:\SteamLibrary\steamapps\common\SOMA'),Path(r'C:\Program Files\Epic Games\SOMA'),Path(r'C:\Program Files\GOG Galaxy\Games\SOMA')]:
 dll=game/'Newton.dll'
 for mode,thickness in [('child','.002'),('compound','.002'),('child','.1'),('compound','.1')]:
  try:
   p=subprocess.run([str(exe),str(dll),mode,thickness],capture_output=True,text=True,timeout=15)
   row={'game':str(game),'sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'mode':mode,'thickness':thickness,'exit':p.returncode,'output':p.stdout+p.stderr}
  except subprocess.TimeoutExpired as e:
   row={'game':str(game),'mode':mode,'timeout':True,'output':str(e.stdout)}
  results.append(row);print(json.dumps(row))
(r/'audit/jb-recovery-cast.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
raise SystemExit(0 if all(v.get('exit')==0 for v in results) else 1)
