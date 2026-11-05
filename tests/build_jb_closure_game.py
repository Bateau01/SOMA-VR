"""Private delayed-contact fixture. Never writes ownership or native acceptance."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
replay=(r/'tests/jb_hand_replay.inc').read_text()
replay=replay.replace('if(phase==4&&!cpu6Placed&&cpu6Cup){','if(phase==4&&t>=20.040f&&!cpu6Placed&&cpu6Cup){')
a=replay.index(' if(phase==4&&cpu6Cup&&!cpu6GripRequested){')
z=replay.index(' if(cpu6Placed&&(cpu6GripRequested',a)
replay=replay[:a]+''' if(phase==4&&!cpu6GripRequested){cpu6GripRequested=1;ext_Log("JB_CLOSURE_EDGE_FIXTURE before mug contact, t %.6f",t);}
 if(phase>=4&&phase<10&&cpu6GripRequested)g_lastSqueeze[1]=clamp01(.60f+(t-20.f)*3.f);
'''+replay[z:]
if '--left-hand' in sys.argv:
    for name in ('g_h34HandNewton','g_h14GripBody','g_lastSqueeze','g_h526TargetValid','g_h526Target','g_h531TrackedTarget','g_h5755eiContactPropCount','g_h567BlockedHold','g_h34LastPosError'):
        replay=replay.replace(name+'[1]',name+'[0]')
    replay=replay.replace('h15_grip_center_world(1,','h15_grip_center_world(0,').replace('g_h30NativeUseHand==1','g_h30NativeUseHand==0')
out=r/'build/jb-closure-replay.inc';out.write_text(replay)
s=(r/'tests/build_jb_hand.py').read_text().replace('tests/jb_hand_replay.inc','build/jb-closure-replay.inc').replace('build/jb-hand','build/jb-closure-game')
needle="s=s.replace(needle,needle+"
# Inject a bounded private observation into the generated C, never production.
insert='''
observe="""s=s.replace('#include \\\"closure_contact_jb.inc\\\"',(r/'source/closure_contact_jb.inc').read_text().replace('if(!jb_closure_step(', 'if(g_s26jbClosure[hand].armed)ext_Log(\\\"JB_CLOSURE_OBSERVE hand %d step %u edge %d closing %d contact %d transaction %d remaining %.5f\\\",hand,g_h14PhysicsSteps,edge,closing,contact,transaction,g_s26jbClosure[hand].remaining);if(!jb_closure_step('))"""
'''
s=s.replace("needle='s=s[:a]+post+s[z:]'",insert+"\nneedle='s=s[:a]+post+s[z:]'")
s=s.replace('needle+"\\ns=s.replace', 'needle+"\\n"+observe+"\\ns=s.replace')
if '--baseline-closure' in sys.argv:
    s=s.replace('needle+"\\n"+observe+', 'needle+"\\ns=s.replace(\'s26jb_closure_contact(world,timestep);\',\'/* baseline: no closing acquisition */\')\\n"+observe+')
exec(compile(s,str(r/'tests/build_jb_hand.py'),'exec'),{'__file__':str(r/'tests/build_jb_hand.py'),'__name__':'__main__'})
