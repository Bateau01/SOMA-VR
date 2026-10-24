from pathlib import Path
import subprocess,json,shutil
R=Path('.').resolve(); G=R.parents[1]/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
exe=G/'Soma.exe'; original=exe.read_bytes()
try:
 for name,path in [('Steam',None),('Epic',Path('C:/Program Files/Epic Games/SOMA/Soma.exe')),('GOG',Path('C:/Program Files/GOG Galaxy/Games/SOMA/Soma.exe'))]:
  if path: exe.write_bytes(path.read_bytes())
  subprocess.run(['C:/Python314/python.exe','tests/test_aa_native_iv.py',str(G)],check=True)
  shutil.copy2(R/'docs/v109-evidence/aa_iv_native.json',R/f'docs/v109-evidence/aa-IV/native-{name}.json')
finally: exe.write_bytes(original)
