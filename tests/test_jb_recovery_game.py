from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_jb_hand.py').read_text().replace('build/jb-hand','build/jb-recovery-game')
exec(compile(s,str(r/'tests/test_jb_hand.py'),'exec'))
log=(out/'hpl3vr.log').read_text(errors='replace')
m=re.search(r'JB_RECOVERY_RESULT attempts (\d+) accepted (\d+) blocked (\d+) deferred (\d+)',log)
result={'scope':'Actual OpenXR, synthetic controller motion and injected free-root stall. Not a geometry-trap reproduction. Subsequent mug pickup and release use ordinary paths.',
 'fault_started':'JB_RECOVERY_FAULT_BEGIN' in log,'counters':list(map(int,m.groups())) if m else None,
 'pickup_after_fault':'CPU6_REPLAY_PHASE 5 held 1' in log,
 'release_after_fault':bool(re.search(r'CPU6_REPLAY_SAVED rows \d+ held 0',log))}
(out/'recovery-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['fault_started'] and m and int(m[2])==1,result
assert result['pickup_after_fault'] and result['release_after_fault'],result
