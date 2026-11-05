from pathlib import Path
import re,json,statistics,shutil,hashlib
r=Path(__file__).resolve().parents[1]
rows=[]
for run,rate in [('869acce3',120),('bc20bd7b',60),('aa7a6c0c',60),('d6a97838',120)]:
 p=r/'audit/delta-integration'/run
 s=(p/'hpl3vr.log').read_text(errors='replace')
 blocks=re.findall(r'CPU10_VIS block (\d+) mode (\d+) calls (\d+) mean_ms ([\d.]+) jobs_done (\d+) failed (\d+) fallback (\d+)',s)
 means=[statistics.mean(float(x[3]) for x in blocks if int(x[0])>2 and int(x[1])==m) for m in (0,1)]
 result=json.loads((p/'result.json').read_text())
 assert result['completed'] and not result['timedout'] and all(x[5]=='0' for x in blocks)
 rows.append(dict(run=run,physics_hz=rate,native_ms=means[0],candidate_ms=means[1],saved_ms=means[0]-means[1],blocks=blocks))
out=dict(status='rejected: inconsistent performance; no production adoption',baseline='CPU9',scope='Inclusive native visibility calls, alternating 60-call windows, exclude first pair. Same-process comparison; live OpenXR with scripted yaw, not deterministic headset replay or whole-frame FPS.',runs=rows,limitations=['No visual or held-interaction certification of rejected candidate','Steam-only experiment','No new installer warranted'])
(r/'audit/CPU10-closure.json').write_text(json.dumps(out,indent=2))
archive=r/'audit/rejected-visibility-source';archive.mkdir(exist_ok=True)
for name in ('cpu9_render_trial.inc','cpu10_visibility_trial.inc'):
 shutil.copy2(r/'source'/name,archive/name)
shutil.copy2(r.parent/'SOMA_VR_IW_CPU9/source/cpu9_render_trial.inc',r/'source/cpu9_render_trial.inc')
# Unreferenced prototype preserved only in audit, not active source.
(r/'source/cpu10_visibility_trial.inc').unlink()
shutil.copy2(r.parent/'SOMA_VR_IW_CPU9/tests/cpu9_batch_contract.c',r/'tests/cpu9_batch_contract.c')
with (r/'docs/CPU10.md').open('a') as f:
 f.write('\nRejected after four native comparisons. '+json.dumps([{k:v for k,v in x.items() if k!='blocks'} for x in rows])+'. Candidate scheduling removed from active source; CPU9 retained. Diagnostic executable is not a release.\n')
print(json.dumps([{k:v for k,v in x.items() if k!='blocks'} for x in rows],indent=2))
