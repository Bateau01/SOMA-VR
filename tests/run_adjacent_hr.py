from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];results=[]
for name in ['test_pickup_chain_gp.py','test_shared_grips_gp.py','test_shared_grips.py','test_handheld.py','test_tracer_two_hands.py','test_shadow_leases.py','test_binding_editor_hc.py']:
 p=subprocess.run([sys.executable,str(R/'tests'/name),sys.argv[1]],cwd=R,capture_output=True,text=True);results.append({'test':name,'exit':p.returncode,'output':p.stdout+p.stderr});(R/'docs/v109-evidence/adjacent_regressions_hr.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,(p.stdout+p.stderr)[-240:],flush=True)
raise SystemExit(any(x['exit'] for x in results))
