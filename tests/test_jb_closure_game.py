from pathlib import Path
import json,re,sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/test_jb_hand.py').read_text().replace('build/jb-hand','build/jb-closure-game')
exec(compile(s,str(r/'tests/test_jb_hand.py'),'exec'))
log=(out/'hpl3vr.log').read_text(errors='replace')
result={'scope':'Actual XR, synthetic squeeze ramp; mug moved into physical contact 40ms after squeeze as fixture setup. No ownership injection. Not proof of every finger pose or natural approach.',
 'edge_seen':'JB_CLOSURE_EDGE_FIXTURE' in log,
 'held_after_contact':'CPU6_REPLAY_PHASE 5 held 1' in log,
 'released':bool(re.search(r'CPU6_REPLAY_SAVED rows \d+ held 0',log)),
 'closure_observer':[x for x in log.splitlines() if 'JB_CLOSURE_OBSERVE' in x]}
(out/'closure-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
assert result['edge_seen'] and result['released'],result
assert result['held_after_contact']==('--baseline-closure' not in sys.argv),result
