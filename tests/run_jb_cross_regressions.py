"""Sequential isolated-game regressions; never shares the VR session between games."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
g=r.parent/'SOMA_VR_S26AY_SHUTTLE/validation/Game'
base=[sys.executable,str(r/'tests/test_jb_poke.py'),str(g),'--input-mode','0','--runtime-transitions','--movement-replay','--apartment-mechanisms','--native-menu-exit','--fixed-yaw','0']
for hz,extra in [(60,[]),(120,['--locked-poke']),(120,['--occluded-poke'])]:
 print('RUN crossing regression',hz,extra,flush=True)
 subprocess.run(base+['--physics-rate',str(hz)]+extra,cwd=r,check=True)
print('Sequential crossing regression cases passed',flush=True)
