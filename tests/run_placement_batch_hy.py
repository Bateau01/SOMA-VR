"""Sequential representative surface captures; never runs two games together."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
cases=[('LadderArea_1','01_04_transport_station'),('LadderArea_1','02_01_ms_curie_outside'),('LadderArea_2','02_06_theta_tunnels'),('CrateLadderArea_1','02_07_theta_exit'),('SubBaseLadder_Outer','03_01_omicron_outside'),('LadderArea_3','04_02_tau_inside'),('Ladder','05_01_phi_inside')]
if len(sys.argv)>2:cases=cases[int(sys.argv[2]):]
results=[]
for target,mapname in cases:
 for end in ['bottom','top']:
  cmd=[sys.executable,str(r/'tests/test_ladder_visual_hy.py'),sys.argv[1],target,mapname,end,'--force-active','--regression']
  p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=100)
  print(p.stdout+p.stderr,flush=True)
  results.append({'map':mapname,'target':target,'end':end,'exit':p.returncode,'output':p.stdout+p.stderr})
  (r/'docs/v109-evidence/ladder_batch_hy.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
  if p.returncode:raise SystemExit(p.returncode)
