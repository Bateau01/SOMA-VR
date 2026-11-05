"""Compare synthetic native held phases; distinct runs are not identical contacts."""
from pathlib import Path
import json, sys

paths = list(map(Path, sys.argv[1:3]))
assert len(paths) == 2
receipts = [json.loads((p / 'build-receipt.json').read_text()) for p in paths]
options = [dict(r['arguments']) for r in receipts]
assert not options[0].pop('newton_workers_2')
assert options[1].pop('newton_workers_2')
assert options[0] == options[1], 'Unmatched build options'
identities = [json.loads((p / 'identity.json').read_text()) for p in paths]
for ident in identities:
    ident.pop('dll_sha256')
assert identities[0] == identities[1], 'Unmatched executable or scene'
assert (paths[0] / 'fixture-user-settings.cfg').read_bytes() == (paths[1] / 'fixture-user-settings.cfg').read_bytes(), 'Unmatched fixture settings'
assert json.loads((paths[0] / 'test-command.json').read_text()) == json.loads((paths[1] / 'test-command.json').read_text()), 'Unmatched replay commands'
results = [json.loads((p / 'result.json').read_text()) for p in paths]
assert all(r['completed'] and r['process_exit_code'] == 0 and not r['script_errors'] for r in results)
summaries = [json.loads((p / 'movement-summary.json').read_text())['phases'] for p in paths]
for phases in summaries:
    assert all(p['held'] == p['frames'] and p['hands_min'] == 2 for p in phases if 5 <= p['phase'] <= 9)

def aggregate(phases, selected):
    q = [p for p in phases if p['phase'] in selected]
    n = sum(p['frames'] for p in q)
    return dict(frames=n, frame_ms=sum(p['mean_ms'] * p['frames'] for p in q) / n,
                newton_per_frame_ms=sum(p['attribution_mean_ms']['newton'] * p['frames'] for p in q) / n)

groups = {}
for name, selected in [('free', range(1, 4)), ('held', range(5, 10))]:
    a, b = [aggregate(p, selected) for p in summaries]
    groups[name] = dict(reference=a, candidate=b,
                        candidate_minus_reference_ms={k: b[k] - a[k] for k in ('frame_ms', 'newton_per_frame_ms')})
out = dict(scope=__doc__, captures=[str(p) for p in paths],
           dll_hashes=[r['dll_sha256'] for r in receipts], groups=groups,
           limitations='Executable, scene, fixture settings and replay commands matched. External runtime settings are not fully captured; contact history and scheduling vary. Inclusive Newton/frame is not one Newton step. Does not certify story interactions.')
(paths[1] / 'cpu33-held-comparison.json').write_text(json.dumps(out, indent=2))
print(json.dumps(groups, indent=2))
