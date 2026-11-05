"""Private bounded free-hand recovery experiment, not a release payload."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
replay=(r/'tests/jb_hand_replay.inc').read_text()
# Explicit clear-space fixture: keep the other physical hand outside the swept envelope.
replay=replay.replace('(h?.25f:-.25f)','(h?.25f:-.80f)')
# A simulated stalled body is explicit fault injection, not a reproduction of
# any reported geometry trap. All ordinary pickup/solver paths remain active.
replay=replay.replace('h&&t>=45&&t<50','h&&((t>=10&&t<14)||(t>=45&&t<50))')
replay=replay.replace('phase==1||phase==2||phase==6||phase==7','phase==6||phase==7')
replay=replay.replace('phase==2||phase==7','phase==7').replace('phase==3||phase==8','phase==8')
replay+='''
static float jbFaultMatrix[16];static int jbFaultStarted;
static void jb_recovery_fault(void){
 if(!cpu6Start||!g_h34HandNewton[1]||g_h14GripBody[1])return;
 float t=(float)((double)(cpu6Now-cpu6Start)*1e-9);
 if(t<10||t>=14||jbRecoveryAccepted)return;
 if(!jbFaultStarted){p_h14GetMatrix(g_h34HandNewton[1],jbFaultMatrix);jbFaultMatrix[12]+=.35f;jbFaultStarted=1;ext_Log("JB_RECOVERY_FAULT_BEGIN simulated root stall, not a geometry-trap reproduction");}
 h536_sync_managed_transform(1,jbFaultMatrix,"private stalled-root fixture");
 float zero[4]={0};p_h14SetVelocity(g_h34HandNewton[1],zero);p_h14SetOmega(g_h34HandNewton[1],zero);
 if(g_h14PhysicsSteps%30u==0){float*m=g_h526Target[1];ext_Log("JB_RECOVERY_WATCH step %u t %.4f target %.4f %.4f %.4f frozen %.4f %.4f %.4f stalled %.4f effort %.4f cooldown %.4f normal %d grab %d pending %d attempt %d arm %u dormant %u collisionOff %u nativeUse %d hidden %d tracked %d",g_h14PhysicsSteps,t,m[12],m[13],m[14],jbFaultMatrix[12],jbFaultMatrix[13],jbFaultMatrix[14],jbRecoveryWatch[1].stalled,jbRecoveryWatch[1].effort,jbRecoveryWatch[1].cooldown,h5755ha_exact_normal_state_now(),h5755gw_exact_grab_state_now(),g_h25PendingValid[1],g_h25AttemptBody[1]!=0,(u32)g_h532ArmState[1],(u32)g_h532Dormant[1],(u32)g_h526CollisionDisabled[1],g_h30NativeMouseDown&&g_h30NativeUseHand==1,g_s26CutsceneHandsHidden,visual_pose_valid(1));}
}
'''
replay=replay.replace('cpu6Done=1;jb_hand_write();','cpu6Done=1;ext_Log("JB_RECOVERY_RESULT attempts %u accepted %u blocked %u deferred %u",jbRecoveryAttempts,jbRecoveryAccepted,jbRecoveryBlocked,jbRecoveryDeferred);jb_hand_write();')
(r/'build/jb-recovery-replay.inc').write_text(replay)
s=(r/'tests/build_jb_hand.py').read_text().replace('tests/jb_hand_replay.inc','build/jb-recovery-replay.inc').replace('build/jb-hand','build/jb-recovery-game')
insert="s=s.replace('static void h14_physics_step(const void* world,float dt){',(r/'tests/jb_recovery_engine_candidate.inc').read_text()+'\\nstatic void jb_recovery_fault(void);\\nstatic void h14_physics_step(const void* world,float dt){');s=s.replace('h5755eg_phys_add_since(H5755EG_P_POST,egPost)','jb_recovery_fault();jb_recovery_tick(timestep);h5755eg_phys_add_since(H5755EG_P_POST,egPost)')"
s=s.replace('needle+"\\ns=s.replace', 'needle+'+repr('\n'+insert+'\n')+'+"\\ns=s.replace')
exec(compile(s,str(r/'tests/build_jb_hand.py'),'exec'),{'__file__':str(r/'tests/build_jb_hand.py'),'__name__':'__main__'})
