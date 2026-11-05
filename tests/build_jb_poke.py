"""Private real-XR/synthetic controller acquisition fixture, no release payload."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
jbSwept='--swept-controls' in __import__('sys').argv
jbHand=next((int(x.split('=')[1]) for x in __import__('sys').argv if x.startswith('--poke-hand=')),1)
jbFinger=next((int(x.split('=')[1]) for x in __import__('sys').argv if x.startswith('--poke-finger=')),1)
assert jbHand in (0,1) and 0<=jbFinger<5
replay=(r/'tests/jb_poke_replay.inc').read_text()
for name in ('g_lastPose','g_lastAngularVelocity','g_h14GripBody','g_h15GripJointed','g_h34HandNewton','g_h576azWheelNativePackets'):
 replay=replay.replace(name+'[1]',name+'['+str(jbHand)+']')
replay=replay.replace('h14_hand_pose_raw(1,','h14_hand_pose_raw('+str(jbHand)+',')
replay=replay.replace('h18_finger_points_world(1,1,','h18_finger_points_world('+str(jbHand)+','+str(jbFinger)+',')
replay='/* Test target hand '+str(jbHand)+' finger '+str(jbFinger)+' */\n'+replay
rp=r/'build/jb-poke/replay-selected.inc';rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(replay)
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace('tests/iz_physics_replay.inc','build/jb-poke/replay-selected.inc')
s=s.replace('s=s.replace("s=s.replace', 's=s.replace("b=r/\'build/movement\'","b=r/\'build/jb-poke\'")\ns=s.replace("s=s.replace',1)

extra=r"""
if JBSWEPT:
 rocker=(r/'source/rocker_y.inc').read_text()
 a=rocker.index('static i32 s26hr_control_contact(');z=rocker.index('static i32 s26y_near(',a)
 import re
 part=rocker[a:z];stage=[0]
 def mark(m):
  stage[0]+=1
  if stage[0]==5:return '{if(jbSweepDispatch)ext_Log("JB_SWEEP_GATE active %d blocked %d ownerMatch %d pause %d sync %d matrix %d id %u",r->active,s26hr_control_blocked(r->owner),owner==r->owner,h5754h_pause_active(),g_lastSyncResult,p_h14GetMatrix!=0,r->id);return 1;}'
  return '{if(jbSweepDispatch)ext_Log("JB_SWEEP_DISPATCH exit %d code %d",'+str(stage[0])+','+m[1]+');return '+m[1]+';}'
 part=re.sub(r'return ([012]);',mark,part)
 rocker='static i32 jbSweepDispatch;\n'+rocker[:a]+part+rocker[z:]
 s=s.replace('#include "rocker_y.inc"',rocker)
 sweep=(r/'source/world_touch_sweep_jb.inc').read_text()
 sweep=sweep.replace('S26HDHit hit=s26hd_ray(start,end);','S26HDHit hit=s26hd_ray(start,end);static i32 logs;if(logs++<24)ext_Log("JB_SWEEP_RAY distance %.6f body %p t %.6f",length,hit.body,hit.t);')
 sweep=sweep.replace('i32 result=s26hr_control_contact(', 'ext_Log("JB_WORLD_SWEEP hit hand %d finger %d distance %.5f fraction %.5f",hand,finger,length,hit.t);i32 result=s26hr_control_contact(')
 sweep=sweep.replace('i32 result=s26hr_control_contact(', 'jbSweepDispatch=1;i32 result=s26hr_control_contact(').replace('return result==2?0:result;', 'jbSweepDispatch=0;return result==2?0:result;')
 s=s.replace('#include "world_touch_sweep_jb.inc"',sweep)
else:
 s=s.replace('#include "world_touch_sweep_jb.inc"','')
 s=s.replace('i32 crossingSample=s26jb_poke_contiguous(hand,g_h485PokePrevTipValid[hand]);','')
 s=s.replace('    if(s26jb_cross_fingers(hand,crossingSample))return;','')
""".replace('JBSWEPT',repr(jbSwept))
s=s.replace("tex=(r/'source/cpu_texture_profile.inc').read_text()",extra+"\ntex=(r/'source/cpu_texture_profile.inc').read_text()")

exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})

# Record the private variant and all additional compiled fixture sources.
import json, hashlib
p=r/'build/jb-poke/build-receipt.json'
v=json.loads(p.read_text());v['arguments']['jb_swept_controls']=jbSwept;v['arguments']['jb_poke_hand']=jbHand;v['arguments']['jb_poke_finger']=jbFinger
for rel in ['tests/build_jb_poke.py','tests/jb_poke_replay.inc','build/jb-poke/replay-selected.inc']:
 v['source_hashes'][rel]=hashlib.sha256((r/rel).read_bytes()).hexdigest()
p.write_text(json.dumps(v,indent=2))
