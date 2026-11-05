"""Private current-production-policy observer; no installer payload."""
from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1]
s=(r/'tests/build_cpu6_movement.py').read_text()
s=s.replace("s=s.replace('    h5753c_auto_hand_visibility_step();'", "s=s.replace('\\n    h5753c_auto_hand_visibility_step();'")
s=s.replace("(r/'tests/cpu6_movement_replay.inc').read_text(encoding='utf-8-sig')", "(r/'tests/iz_physics_replay.inc').read_text(encoding='utf-8-sig')")
s=s.replace("'-DCPU_TEXTURE_MIN_BYTES=65536'", "'-DCPU_TEXTURE_MIN_BYTES=0','-DCPU_TEXTURE_RELEASE=1','-DCPU_GUI_PREWARM=1','-DCPU_LEAF_FILTER=1','-DCPU_HELD_QUERY=1'")
s=s.replace("files=list((r/'source').glob('*'))+", "files=[r/'tests/iz_physics_replay.inc',r/'tests/build_iz_profile.py']+list((r/'source').glob('*'))+")

# Keep the production pixel-retirement optimization active under observation.
# The historical CPU_WORK_PROFILE build intentionally disabled it.
extra=r"""
# Attribute the observed acquisition spike without changing dispatch order.
a=s.index('u64 egPost=h5755eg_tick(),eg;');z=s.index('h5755eg_phys_add_since(H5755EG_P_POST,egPost)',a)
post=s[a:z]
for stage,call in enumerate(('h528_post_solver_guard()','h540_post_solver_segments()','h5755dc_post_solver_hand_contacts()','h5755hk_post_solver_zero_mass_edge_semantics()','h5755ha_post_solver_edge_native_commit(world)','h5755do_log_rocker_solver_delta()','h5755de_arm_free_contact_visual()','s26ah_tick()','h567_post_solver()','h482_camera_guard_step()','h35_post_solver_segments()','h25_dispatch_pending()','s26hl_dispatch()','h576av_update_theta_handoff()','h5748_post_physics_switch()','s26bb_apply_world_scale()')):
 assert call+';' in post,call
 post=post.replace(call+';','{u64 izT=h5755eg_tick();'+call+';cpu14_event(68,'+str(stage)+',izT,h5755eg_tick(),0);}')
s=s[:a]+post+s[z:]
s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==68')
a=s.index('static void h5755ch_dispatch_native_grab_semantics(void){');z=s.index('static i32 h14_hand_pose_raw(',a)
part=s[a:z]
for stage,call in enumerate(('h5755ch_dispatch_native_grab_semantics()','h5735_dispatch_native_move()','h5747_dispatch_native_look()','h5711_dispatch_semantic_actions()','s26_texture_streaming_step()')):
 part=part.replace(call+';','{u64 izT=h5755eg_tick();'+call+';cpu14_event(69,'+str(stage)+',izT,h5755eg_tick(),0);}')
for stage,call in enumerate(('fCan(entity,0,wrapper)','fOn(entity,0,wrapper,p.contact,&empty)'),10):
 part=part.replace(call,'({u64 izT=h5755eg_tick();u64 izR='+call+';cpu14_event(69,'+str(stage)+',izT,h5755eg_tick(),0);izR;})')
# Measure dispatch bookkeeping/logging without replacing its results.
for stage,name,returns in ((20,'h30_native_use_begin',False),(21,'h481_bind_nearby_mechanism',False),(22,'h25_resolve_native_target',True),(23,'ext_Log',False)):
 offset=0
 while True:
  start=part.find(name+'(',offset)
  if start<0:break
  k=start+len(name);depth=0;quote=False;escape=False
  while k<len(part):
   c=part[k]
   if quote:
    if escape:escape=False
    elif c==chr(92):escape=True
    elif c=='"':quote=False
   elif c=='"':quote=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:break
   k+=1
  call=part[start:k+1]
  wrapped='({u64 izT=h5755eg_tick();'+('i32 izR=' if returns else '')+call+';cpu14_event(69,'+str(stage)+',izT,h5755eg_tick(),0);'+('izR;' if returns else '')+'})'
  part=part[:start]+wrapped+part[k+1:];offset=start+len(wrapped)
s=s[:a]+part+s[z:]
s=s.replace('kind==12||kind==68','kind==12||kind==68||kind==69')
# Observe OS input latency independently of hold bookkeeping.
a=s.index('static void h30_native_use_begin(i32 hand,const void* body,i32 jointed,void* owner){');z=s.index('static void h30_native_use_motion(',a)
part=s[a:z]
for flag in ('0x0002u','0x0004u'):
 call='p_h16MouseEvent('+flag+',0,0,0,0)'
 part=part.replace(call,'({u64 izT=h5755eg_tick();'+call+';cpu14_event(70,'+('0' if flag=='0x0002u' else '1')+',izT,h5755eg_tick(),0);})')
s=s[:a]+'static u64 h5755eg_tick(void);\nstatic void cpu14_event(u32,u32,u64,u64,u64);\n'+part+s[z:]
s=s.replace('kind==68||kind==69','kind==68||kind==69||kind==70')
if __import__('os').environ.get('IZ_SDL_HOLD')=='1':
 a=s.index('static void h30_native_use_begin(i32 hand,const void* body,i32 jointed,void* owner){');z=s.index('static void h30_native_use_motion(',a)
 part=s[a:z].replace('p_h16MouseEvent(0x0002u,0,0,0,0)','iz_hold_transport(0x0002u)').replace('p_h16MouseEvent(0x0004u,0,0,0,0)','iz_hold_transport(0x0004u)')
 wrapper='''static i32 izSDLHeld;
static void iz_hold_transport(u32 flag){
 i32 down=flag==2;
 if(down||izSDLHeld){
  h5754d_resolve_platform();
  if(p_h5754dSDLPushEvent){H5754DEvent e;zero_bytes(&e,sizeof(e));e.button.type=down?H5755AN_SDL_MOUSEBUTTONDOWN:H5755AN_SDL_MOUSEBUTTONUP;e.button.button=1;e.button.state=(u8)down;e.button.clicks=1;
   i32 accepted=p_h5754dSDLPushEvent(&e);if(accepted>0){izSDLHeld=down;ext_Log("IZ_PRIVATE_SDL_HOLD %u accepted",flag);return;}}
 }
 if(p_h16MouseEvent)p_h16MouseEvent(flag,0,0,0,0);
 izSDLHeld=0;
}
'''
 s=s[:a]+wrapper+part+s[z:]

tex=(r/'source/cpu_texture_profile.inc').read_text()
tex=tex.replace('cpu_texture_cost(0,t,end,0,0);','cpu_texture_cost(0,t,end,0,0);cpu14_event(13,0,t,end,0);')
tex=tex.replace('cpu_texture_cost(1,t,end,bytes>0?(u32)bytes:0,t?*(u8*)((u8*)p+0xea):0);','cpu_texture_cost(1,t,end,bytes>0?(u32)bytes:0,t?*(u8*)((u8*)p+0xea):0);cpu14_event(13,1,t,end,bytes>0?(u32)bytes:0);')
tex=tex.replace('static void cpu_texture_install(void){','static void cpu_texture_release_install(void);\nstatic void cpu_texture_install(void){')
tex=tex.replace(' cpu_texture_trial_install();',' cpu_texture_trial_install();cpu_texture_release_install();')
storage=(r/'source/cpu_texture_storage_trial.inc').read_text()
# Production policy, not the historical paired trial/config-file policy.
line=next(x for x in storage.splitlines() if 'cpu4_texture_storage_trial.txt' in x)
storage=storage.replace(line,'')
render=(r/'source/cpu9_render_trial.inc').read_text()
line=next(x for x in render.splitlines() if 'cpu9_render_mode.txt' in x)
render=render.replace(line,' cpu9Forced=1;')
prof=prof.replace('#include "cpu9_render_trial.inc"',render)
release=(r/'source/cpu_texture_release.inc').read_text().replace('#if CPU_TEXTURE_RELEASE && !CPU_WORK_PROFILE','#if CPU_TEXTURE_RELEASE')
storage=storage.replace('#include "cpu_texture_release.inc"',release)
tex=tex.replace('#include "cpu_texture_storage_trial.inc"',storage)
prof=prof.replace('#include "cpu_texture_profile.inc"',tex)
"""
s=s.replace("(b/'cpu_work_profile.inc').write_text(prof)",extra+"\n(b/'cpu_work_profile.inc').write_text(prof)")

sys.argv=[str(r/'tests/build_cpu6_movement.py'),'--event-trace','--frame-attribution','--streaming-release','--hand-mesh-release']
exec(compile(s,str(r/'tests/build_cpu6_movement.py'),'exec'),{'__file__':str(r/'tests/build_cpu6_movement.py'),'__name__':'__main__'})

