from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
sha=hashlib.sha256((r/'build/jb-recovery-game/hpl3vr.dll').read_bytes()).hexdigest()
rates=set()
for d in (r/'audit/delta-integration').iterdir():
 try:
  ident=json.loads((d/'identity.json').read_text());a=json.loads((d/'test-command.json').read_text());v=json.loads((d/'recovery-result.json').read_text());g=json.loads((d/'result.json').read_text());restore=json.loads((d/'restored.json').read_text())
  if ident['dll_sha256']==sha and v['counters'][1]==1 and v['pickup_after_fault'] and v['release_after_fault'] and g['process_exit_code']==0 and restore['restored']:
   rates.add(int(a[a.index('--physics-rate')+1]))
 except (OSError,KeyError,ValueError,TypeError):pass
assert rates=={60,120},rates
s=(r/'tests/jb_recovery_engine_candidate.inc').read_text()
s=s.replace('/* PRIVATE candidate.', '/* Bounded free-hand recovery.')
s=s.replace('#include "../tests/jb_recovery_policy.inc"','#include "hand_recovery_policy_jb.inc"')
a=s.index('static i32 jb_recovery_reject(');b=s.index('static u32 __attribute__((ms_abi)) jb_recovery_filter',a)
s=s[:a]+'static i32 jb_recovery_reject(i32 stage,const void* body,float fraction,i32 count){return 0;}\n'+s[b:]
a=s.index('for(i32 i=0;i<near.count;i++)if(!jb_recovery_tree_empty');b=s.index('\n return 1;',a)
s=s[:a]+'for(i32 i=0;i<near.count;i++)if(!jb_recovery_tree_empty(near.bodies[i],lo,hi))return 0;'+s[b:]
s=s.replace('jbRecoveryAttempts,jbRecoveryAccepted,jbRecoveryBlocked,jbRecoveryDeferred','jbRecoveryAttempts,jbRecoveryAccepted,jbRecoveryBlocked,jbRecoveryDeferred')
# Rare counters remain local and unlogged; test builds can observe them without
# changing the execution path. No fault injection or controller replay ships.
s=s.replace('static void jb_recovery_tick(float dt){','static void jb_recovery_clear_history(i32 h){if(h<0||h>1)return;zero_bytes(&jbRecoveryWatch[h],sizeof(jbRecoveryWatch[h]));jbRecoverySampleStep[h]=0;}\nstatic void jb_recovery_tick(float dt){')
s=s.replace('if(!p_h14GetCollision||!p_h14WorldAABB)return 0;','if(!g_h14NewtonWorld||!p_h14GetCollision||!p_h14WorldAABB)return 0;')
(r/'source/hand_recovery_jb.inc').write_text(s)
(r/'source/hand_recovery_policy_jb.inc').write_text((r/'tests/jb_recovery_policy.inc').read_text().replace('Private stalled-root detector','Stalled-root detector'))
p=r/'source/s26n.c';s=p.read_bytes().decode('cp1252')
assert '#include "hand_recovery_jb.inc"' not in s
s=s.replace('static JBClosureWindow g_s26jbClosure[2];','static void jb_recovery_clear_history(i32 hand);\nstatic JBClosureWindow g_s26jbClosure[2];',1)
s=s.replace('for(i32 h=0;h<2;++h){s26q_roots_reset(h);','for(i32 h=0;h<2;++h){jb_recovery_clear_history(h);s26q_roots_reset(h);',1)
s=s.replace('h25_reset_hand(hand);g_h549AcquireTicks[hand]=0;','jb_recovery_clear_history(hand);h25_reset_hand(hand);g_h549AcquireTicks[hand]=0;',1)
s=s.replace('static void h14_physics_step(const void* world,float dt){','#include "hand_recovery_jb.inc"\nstatic void h14_physics_step(const void* world,float dt){',1)
s=s.replace('if(mapq||uiq){for(i32 j=0;j<2;++j){jb_closure_cancel','if(mapq||uiq){for(i32 j=0;j<2;++j){jb_recovery_clear_history(j);jb_closure_cancel',1)
s=s.replace('h5755eg_phys_add_since(H5755EG_P_POST,egPost);','jb_recovery_tick(timestep);h5755eg_phys_add_since(H5755EG_P_POST,egPost);',1)
p.write_bytes(s.encode('cp1252'))
(r/'audit/jb-recovery-promotion.json').write_text(json.dumps(dict(private_dll=sha,rates=sorted(rates),scope='Clear-path injected-root stall; not arbitrary trapped geometry or held-item relocation',production_files=['source/hand_recovery_jb.inc','source/hand_recovery_policy_jb.inc']),indent=2))
print('Promoted bounded free-hand recovery; runtime candidate needs rebuild and production checks')
