from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
cases=[('ClimbArea_1','01_01_upsilon_awake'),('CrewQuarterLadderArea','02_02_ms_curie_inside'),('ClimbArea_1','02_07_theta_exit'),('LadderArea_1','01_04_transport_station'),('HatchClimb_2','01_02_upsilon_inside'),('ClimbArea_2','02_05_theta_inside'),('LadderArea_2','02_06_theta_tunnels'),('LadderArea_1','02_01_ms_curie_outside'),('SubBaseLadder_Outer','03_01_omicron_outside'),('LadderArea_3','04_02_tau_inside')]
results=[]
docs=Path('C:/Users/BateauPC/Documents/My Games/Soma/Main')
for target,mapname in cases:
 args=[sys.executable,str(r/'tests/test_traversal_save_ia.py'),sys.argv[1],target,mapname,'bottom','--regression','--lock-presentation','--placement-only']
 if list(docs.rglob('AutoSave_'+mapname.replace('_','-')+'*.sav')):args+=['--load-save']
 p=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=110)
 print(p.stdout+p.stderr,flush=True)
 results.append({'map':mapname,'target':target,'saved_game':'--load-save' in args,'exit':p.returncode,'output':p.stdout+p.stderr})
 (r/'docs/v109-evidence/save_batch_ia.json').write_text(json.dumps(results,indent=2))
raise SystemExit(any(x['exit'] for x in results))
