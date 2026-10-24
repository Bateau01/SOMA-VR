from pathlib import Path
import json
r=Path(__file__).resolve().parents[1];base=json.loads((r/'docs/v109-evidence/save_batch_ia.json').read_text());rerun=json.loads((r/'docs/v109-evidence/save_rerun_ia.json').read_text());assert len(rerun)==3
rows={x['map']:x for x in base};rows.update({x['map']:x for x in rerun});assert len(rows)==10 and all(x['exit']==0 for x in rows.values())
summary=[]
for m,x in rows.items():
 result=json.loads(x['output'].strip());assert result['execution_completed'];summary.append({'map':m,'saved_game':x['saved_game'],'assertions_passed':sum('HY_PASS|' in l for l in result['lines']),'evidence':Path(result['capture_directory']).name})
report={'version':'1.0.9-S26IA','maps':summary,'actual_save_load_maps':sum(x['saved_game'] for x in summary),'direct_map_empty_state_recovery_maps':sum(not x['saved_game'] for x in summary),'scope':'Native fixtures; VR capability and pose acknowledgement supplied. No headset playthrough claim.'}
(r/'docs/v109-evidence/save_final_ia.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
