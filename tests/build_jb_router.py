"""Private real-XR/synthetic controller acquisition fixture, no release payload."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace('tests/iz_physics_replay.inc','tests/jb_router_replay.inc')
s=s.replace('s=s.replace("s=s.replace', 's=s.replace("b=r/\'build/movement\'","b=r/\'build/jb-router\'")\ns=s.replace("s=s.replace',1)

probe=r"""
s=s.replace('if(distance==999.0f)return;', 'if(distance==999.0f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_POINTS body %p",body);return;}')
s=s.replace('if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f)return;', 'if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_MESH body %p gap %.5f",body,gap);return;}')
s=s.replace('if(drLeverOwnsEdge)nativeQueuedThisStep=1;', 'if(gripEdge&&h==1)ext_Log("JB_SELECTOR_EDGE enabled %d body %p gap %.5f second %.5f best %p native %p",authScan.drEnabled,authScan.drBody,authScan.drGap,authScan.drSecondGap,authScan.best,authScan.nativeNow);if(drLeverOwnsEdge)nativeQueuedThisStep=1;')
"""
s=s.replace("tex=(r/'source/cpu_texture_profile.inc').read_text()",probe+"\ntex=(r/'source/cpu_texture_profile.inc').read_text()")

exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})
