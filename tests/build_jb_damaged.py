"""Private real-XR/synthetic controller acquisition fixture, no release payload."""
from pathlib import Path
import sys,json,hashlib
r=Path(__file__).resolve().parents[1]
early='--early-grip' in sys.argv
replay=(r/'tests/jb_damaged_replay.inc').read_text()
if early:
 replay=replay.replace('if(jbGripAt<0&&t>=4&&t<10&&jbMechanism)', 'if(!1&&jbGripAt<0&&t>=4&&t<10&&jbMechanism)')
 replay=replay.replace('jbGripAt<0&&t>=8&&jbMechanism','jbGripAt<0&&t>=3.85f&&jbMechanism')
 # Record observations only. A contact after the press is not a second input.
 replay=replay.replace('if(ph!=cpu6Phase)', '''if(t>=3.7f&&t<4.3f){float hp[3],hm[16],gap=999,cp[3];if(h14_hand_pose(1,hp,hm))h14_point_to_body(jbMechanism,hp,&gap,cp);ext_Log("JB_CLOSURE_OBSERVE t %.6f step %u edge %u squeeze %.3f applied %u pending %u target %u dynamicStep %u staticStep %u held %d gap %.5f",t,g_h14PhysicsSteps,g_h5755haGripEdgeStep[1],g_lastSqueeze[1],(u32)g_h545AppliedSqueezeLevel[1],(u32)g_h545Pending[1],(u32)g_h545PendingSqueezeLevel[1],g_h5755eiContactPropStep[1],g_h5755hjStaticContactStep[1],g_h14GripBody[1]!=0,gap);}
 if(ph!=cpu6Phase)''')
rp=r/'build/jb-damaged/replay-selected.inc';rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(replay)
if early:
 marker='if(ph!=cpu6Phase)'
 observation='''if(t>=3.84f&&t<3.94f){
 float hp[3],hm[16],inv[16];if(h14_hand_pose(1,hp,hm)){h14_rigid_inverse(hm,inv);
 for(i32 f=0;f<5;f++){float points[5][3],curl[4];i32 len=0;for(i32 q=0;q<4;q++)curl[q]=h545_proxy_finger_curl(1,f);
 if(h18_finger_points_world(1,f,curl,hm,points,&len)&&len>=1&&len<=4){float gap=999,cp[3],local[3],mesh[3],bary[3],meshGap=999;i32 tri=-1;
 if(h14_point_to_body(jbMechanism,points[len],&gap,cp)){h14_transform_point(inv,cp,local);h20_nearest_hand_mesh_local(1,local,mesh,&tri,bary,&meshGap);ext_Log("JB_CLOSURE_CHIP_SURFACE t %.6f finger %d boneGap %.6f meshGap %.6f",t,f,gap,meshGap);}}}
 }
 if(g_h14GripBody[1]){void*w=p_h14GetUserData(g_h14GripBody[1]);char name[128];name[0]=0;if(w)h5748n_copy_tstring((u8*)w+0x10,name,sizeof(name));ext_Log("JB_CLOSURE_HELD_ID t %.6f body %p name %s",t,g_h14GripBody[1],name);}
 }
 '''
 replay=replay.replace(marker,observation+marker);rp.write_text(replay)
s=(r/'tests/build_iz_profile.py').read_text()
s=s.replace('tests/iz_physics_replay.inc','build/jb-damaged/replay-selected.inc')
s=s.replace('s=s.replace("s=s.replace', 's=s.replace("b=r/\'build/movement\'","b=r/\'build/jb-damaged\'")\ns=s.replace("s=s.replace',1)

probe=r"""
s=s.replace('if(localPoint<0)return;', 'if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps&&stageWrapper&&s->drEnabled){char name[128];if(h5748n_copy_tstring((u8*)stageWrapper+0x10,name,sizeof(name))&&h25_str_contains(name,"ChipTool_Damaged")){float inv[16];h14_rigid_inverse(s->drHandM,inv);for(i32 k=0;k<6;k++){float d,cp[3],hl[3],mp[3],bary[3],mg=999;i32 tri=-1;if(h14_point_to_body(body,s->drP[k],&d,cp)){h14_transform_point(inv,cp,hl);h20_nearest_hand_mesh_local(s->hand,hl,mp,&tri,bary,&mg);ext_Log("JB_CHIP_PHYSICAL point %d distance %.5f mesh %.5f",k,d,mg);}}}}if(localPoint<0)return;')

s=s.replace('if(!h576ad_target_can_interact(wrapper,owner,&raw,&icon)||raw!=body||icon!=14)return 0;', 'i32 jbEligible=h576ad_target_can_interact(wrapper,owner,&raw,&icon);ext_Log("JB_PICKUP_GATE eligible %d icon %d raw %p body %p",jbEligible,icon,raw,body);if(!jbEligible||raw!=body||icon!=14)return 0;')
s=s.replace('float gate=jointed?0.0350f:0.0120f;if(meshGap>gate', 'float gate=jointed?0.0350f:0.0120f;ext_Log("JB_QUEUE_MESH body %p gap %.5f gate %.5f",body,meshGap,gate);if(meshGap>gate')
s=s.replace('if(localPoint<0)return;', 'if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps){char jbName[128];jbName[0]=0;if(stageWrapper)h5748n_copy_tstring((u8*)stageWrapper+0x10,jbName,sizeof(jbName));ext_Log("JB_CHIP_CANDIDATE body %p name %s point %d distance %.5f gap %.5f contact %.5f %.5f %.5f",body,jbName,localPoint,localBest,localGap,localContact[0],localContact[1],localContact[2]);}if(localPoint<0)return;')
s=s.replace('if(distance==999.0f)return;', 'if(distance==999.0f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_POINTS body %p",body);return;}')
s=s.replace('if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f)return;', 'if(!h20_nearest_hand_mesh_local(s->hand,local,mesh,&tri,bary,&gap)||gap>.012f){if(s->hand==1&&g_h5755haGripEdgeStep[1]==g_h14PhysicsSteps)ext_Log("JB_SELECTOR_MESH body %p gap %.5f",body,gap);return;}')
s=s.replace('if(drLeverOwnsEdge)nativeQueuedThisStep=1;', 'if(gripEdge&&h==1)ext_Log("JB_SELECTOR_EDGE enabled %d body %p gap %.5f second %.5f best %p native %p",authScan.drEnabled,authScan.drBody,authScan.drGap,authScan.drSecondGap,authScan.best,authScan.nativeNow);if(drLeverOwnsEdge)nativeQueuedThisStep=1;')
"""
s=s.replace("tex=(r/'source/cpu_texture_profile.inc').read_text()",probe+"\ntex=(r/'source/cpu_texture_profile.inc').read_text()")

exec(compile(s,str(r/'tests/build_iz_profile.py'),'exec'),{'__file__':str(r/'tests/build_iz_profile.py'),'__name__':'__main__'})
p=r/'build/jb-damaged/build-receipt.json';d=json.loads(p.read_text());d['arguments']['jb_early_grip']=early
for rel in ['tests/build_jb_damaged.py','tests/jb_damaged_replay.inc','build/jb-damaged/replay-selected.inc']:
 d['source_hashes'][rel]=hashlib.sha256((r/rel).read_bytes()).hexdigest()
p.write_text(json.dumps(d,indent=2))
