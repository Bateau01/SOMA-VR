"""Private real-XR/synthetic controller acquisition fixture, no release payload."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace('tests/iz_physics_replay.inc','tests/jb_contact_replay.inc')
s=s.replace('s=s.replace("s=s.replace', 's=s.replace("b=r/\'build/movement\'","b=r/\'build/jb-contact\'")\ns=s.replace("s=s.replace',1)

probe=r"""
s=s.replace('s26ac_contact(h,b,other,j,n);s26ag_note(h,b,other,j);','s26ac_contact(h,b,other,j,n);s26ag_note(h,b,other,j);if(h==1&&g_h5755haGripEdgeStep[h]==g_h14PhysicsSteps){char jbName[96]={0};void*jbW=p_h14GetUserData(other);if(jbW)h5748n_copy_tstring((u8*)jbW+0x10,jbName,sizeof(jbName));ext_Log("JB_EDGE_BLOCKER body %p name %s",other,jbName);}')
s=s.replace('float bm[16],point[3]={0},distance=999.0f;p_h14GetMatrix(body,bm);', 'float bm[16],point[3]={0},distance=999.0f;p_h14GetMatrix(body,bm);if(s26jb_solid_body(body)&&g_h5755haGripEdgeStep[s->hand]==g_h14PhysicsSteps){ext_Log("JB_CONTACT_EDGE step %u contactStep %u count %u",g_h14PhysicsSteps,g_h5755hjStaticContactStep[s->hand],g_h5755hjStaticContactCount[s->hand]);for(u32 q=0;q<g_h5755hjStaticContactCount[s->hand]&&q<H5755HJ_STATIC_CONTACT_MAX;q++)ext_Log("JB_CONTACT_ENTRY match %d valid %d",g_h5755hjStaticContactBody[s->hand][q]==body,g_h5755hjStaticContactPointValid[s->hand][q]);}')
s=s.replace('float gate=jointed?0.0350f:0.0120f;if(meshGap>gate', 'float gate=jointed?0.0350f:0.0120f;if(s26jb_solid_body(body))ext_Log("JB_CONTACT_QUEUE_MESH gap %.5f gate %.5f",meshGap,gate);if(meshGap>gate')
s=s.replace('if(!h20_nearest_hand_mesh_local(s->hand,localContact,skin,&triangle,baryContact,&skinGap)||skinGap>.012f)continue;', 'if(!h20_nearest_hand_mesh_local(s->hand,localContact,skin,&triangle,baryContact,&skinGap)||skinGap>.012f){if(s26jb_solid_body(body)&&g_h5755haGripEdgeStep[s->hand]==g_h14PhysicsSteps)ext_Log("JB_CONTACT_SELECTOR_MESH %.5f",skinGap);continue;}')
s=s.replace('if(distance==999.0f)return;', 'if(distance==999.0f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_POINTS body %p",body);return;}')
s=s.replace('if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f)return;', 'if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_MESH body %p gap %.5f",body,gap);return;}')
s=s.replace('if(drLeverOwnsEdge)nativeQueuedThisStep=1;', 'if(gripEdge&&h==1)ext_Log("JB_SELECTOR_EDGE enabled %d body %p gap %.5f second %.5f best %p native %p",authScan.drEnabled,authScan.drBody,authScan.drGap,authScan.drSecondGap,authScan.best,authScan.nativeNow);if(drLeverOwnsEdge)nativeQueuedThisStep=1;')
"""
s=s.replace("tex=(r/'source/cpu_texture_profile.inc').read_text()",probe+"\ntex=(r/'source/cpu_texture_profile.inc').read_text()")

exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})
