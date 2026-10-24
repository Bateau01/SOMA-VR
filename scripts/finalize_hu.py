from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
e=r/'docs/v109-evidence'
results=[]
for p in sorted(e.glob('*hu.log')):
 s=p.read_text(errors='replace')
 markers=[x.strip() for x in s.splitlines() if 'HU_' in x]
 expected_failure=p.name.startswith('baseline_')
 passed=('gates=false' in s) if expected_failure else ('HU_DONE' in s and 'gates=false' not in s)
 results.append({'log':p.name,'expected_baseline_failure':expected_failure,'expectation_met':passed,'markers':markers})
assert results and all(x['expectation_met'] for x in results),results
(e/'native_summary_hu.json').write_text(json.dumps({'type':'native-engine fixtures, supplied starting states; no tracked controllers','results':results},indent=2))
p=r/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('**1.0.9-S26HT**. See','**1.0.9-S26HU**. See the [HU follow-up evidence and remaining checks](docs/v109-followup-hu.md). See',1);p.write_text(s,encoding='utf-8')
p=r/'docs/v109-followup-hu.md';s=p.read_text();s=s.replace('# S26HU follow-up — in progress','# S26HU follow-up — candidate for headset testing').replace('actual regression reproduction pending.','extracted baseline/candidate regression results appear below; physical-controller reproduction remains unconfirmed.').replace('native Prop_Button script checks its own disabled flag separately. Audit all VR/direct callback routes before defining the correction.','the actual asset uses Prop_MovingButton. The native baseline and corrected direct callback paths are compared below.');p.write_text(s)
print(json.dumps(results,indent=2))
