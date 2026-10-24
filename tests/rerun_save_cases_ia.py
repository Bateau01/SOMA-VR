from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1]
cases=[('ClimbArea_1','01_01_upsilon_awake'),('ClimbArea_1','02_07_theta_exit'),('HatchClimb_2','01_02_upsilon_inside')]
results=[]
docs=Path('C:/Users/BateauPC/Documents/My Games/Soma/Main')
for target,mapname in cases:
 args=[sys.executable,str(r/'tests/test_traversal_save_ia.py'),sys.argv[1],target,mapname,'bottom','--regression','--lock-presentation','--placement-only']
 if list(docs.rglob('AutoSave_'+mapname.replace('_','-')+'*.sav')):args+=['--load-save']
 p=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=110)
 print(p.stdout+p.stderr,flush=True)
 results.append({'map':mapname,'target':target,'saved_game':'--load-save' in args,'exit':p.returncode,'output':p.stdout+p.stderr})
 (r/'docs/v109-evidence/save_rerun_ia.json').write_text(json.dumps(results,indent=2))
raise SystemExit(any(x['exit'] for x in results))
