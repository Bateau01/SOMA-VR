"""Report independent evidence gates; never turn a failed exit into a pass."""
from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1]
for case in sys.argv[1:]:
 p=root/'audit/delta-integration'/case
 vr=(p/'hpl3vr.log').read_text(errors='replace');native=(p/'hpl.log').read_text(errors='replace')
 result=json.loads((p/'result.json').read_text());receipt=json.loads((p/'build-receipt.json').read_text())
 members=[tuple(map(int,m)) for m in re.findall(r'CPU29_MEMBERSHIP members (\d+) mesh_expected (\d+) missing (\d+) invalid (\d+) compiled (\d+)',vr)]
 buffers=[tuple(map(int,m)) for m in re.findall(r'CPU24_GPU_PARITY bytes (\d+) compared (\d+) mismatches (\d+) unmap (\d+)',vr)]
 final=re.findall(r'CPU20_SHUTDOWN pending_before (\d+) pending_after (\d+) nodes (\d+)',vr)
 evidence={'case':case,'dll_sha256':receipt['dll_sha256'],'exit_code':result.get('process_exit_code'),
 'clean_exit':result.get('process_exit_code')==0,'fixture_completed':'IU_VR_DONE' in native,
 'native_route_completed':all(s in native for s in ('CPU20_THETA_LEAVE','CPU29_TUNNELS_ENTER')),
 'membership_rows':members,'membership_pass':any(row[1]>0 for row in members) and all(missing==invalid==0 and compiled==1 for total,expected,missing,invalid,compiled in members),
 'gpu_bytes_compared':sum(x[1] for x in buffers),'gpu_parity_pass':bool(buffers) and all(size==compared and errors==0 and unmap==1 for size,compared,errors,unmap in buffers),
 'held_roots_observed_across_world_identity_change':'CPU29_LIFETIME_WORLD_CHANGED' in vr,
 'shutdown_queue_empty':bool(final) and final[-1][1]=='0',
 'limits':'Membership checks eligible mesh subentities, not every renderable family; GPU byte checks are not visual regression tests. No physical-controller or authored progression certification.'}
 (p/'cpu29-evidence.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
