from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];G=sys.argv[1]
cases=[('02_01_ms_curie_outside','LadderArea_3','bottom',False),('02_01_ms_curie_outside','LadderArea_3','top',False),('02_01_ms_curie_outside','Start_Ladder','bottom',True),('02_01_ms_curie_outside','Start_Ladder','top',True),('02_01_ms_curie_outside','LadderArea_1','top',False),('01_02_upsilon_inside','LadderArea_1','bottom',False),('01_02_upsilon_inside','LadderArea_1','top',False),('02_06_theta_tunnels','LadderArea_2','bottom',False),('03_01_omicron_outside','SubBaseLadder_Outer','top',False)]
rows=[]
start=int(sys.argv[2]) if len(sys.argv)>2 else 0
for map,target,end,deploy in cases[start:]:
 args=[sys.executable,str(R/'tests/test_ladder_visual_hy.py'),G,target,map,end,'--regression','--lock-presentation']
 args+=['--native-deploy'] if deploy else ['--force-active']
 p=subprocess.run(args,cwd=R,capture_output=True,text=True)
 try:out=json.loads(p.stdout.strip().splitlines()[-1])
 except Exception:out={'error':p.stdout+p.stderr}
 rows.append(out);(R/'docs/v109-evidence'/('final_ladders_hy_'+str(start)+'.json')).write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(json.dumps({'map':map,'target':target,'end':end,'exit':p.returncode,'capture_directory':out.get('capture_directory'),'failure':out.get('error')}),flush=True)
 if p.returncode:sys.exit(p.returncode)
