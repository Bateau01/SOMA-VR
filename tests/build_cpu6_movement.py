from pathlib import Path
import subprocess,hashlib,json,sys
r=Path(__file__).resolve().parents[1];b=r/'build/movement';b.mkdir(parents=True,exist_ok=True)
assert not ('--hand-mesh-release' in sys.argv and '--paired-sse' in sys.argv), 'Do not hook the same native entry twice'
s=(r/'source/s26n.c').read_text();s=s.replace('typedef long long i64;','typedef long long i64;\nstatic void cpu6_pose(i64);static void cpu6_controls(void);',1)
s=s.replace('static void cpu6_pose(i64);','static unsigned int cpu13Phase=99,cpu13Steps[11],cpu13NativeCalls[11];static double cpu13Dt[11];static unsigned long long cpu13Totals[11][32];static double cpu6Scene,cpu6XR,cpu6Newton,cpu6Texture;static void cpu6_pose(i64);')
s=s.replace('o_h14NewtonUpdate(world,timestep);c44_leave(c44Entered);h5755eg_phys_add_since','if(cpu13Phase<11){cpu13NativeCalls[cpu13Phase]++;cpu13Dt[cpu13Phase]+=timestep;}u64 cpu6NT0=0,cpu6NT1=0;if(cpuCounter)cpuCounter(&cpu6NT0);o_h14NewtonUpdate(world,timestep);if(cpuCounter){cpuCounter(&cpu6NT1);cpu6Newton+=1000.0*(cpu6NT1-cpu6NT0)/cpuFreq;}c44_leave(c44Entered);h5755eg_phys_add_since',1)
s=s.replace('    h5753c_auto_hand_visibility_step();','    cpu6_pose(displayTime);\n    h5753c_auto_hand_visibility_step();',1)
s=s.replace('    h5710_update_controller_buttons(displayTime);','    cpu6_controls();\n    h5710_update_controller_buttons(displayTime);',1)
s=s.replace('static u8 h5755cy_check_held_world(', (r/'tests/cpu13_held_query.inc').read_text()+'\nstatic u8 h5755cy_check_held_world(',1)
q='u8 hit=p_h509CheckShapeWorldCollision(g_h34PhysicsWorldWrapper,push,heldShape,hplM,heldWrapper,0,0,&c,1,0,0xffffffffu,0);'
assert s.count(q)==1
s=s.replace(q,'cpu13_pair_install();cpu13OwnShape=(hand>=0&&hand<2&&g_h34HandNewton[hand])?h522_body_shape_relaxed(g_h34HandNewton[hand],hand):0;cpu13QueryScope=1;u64 cpu13Q0=0,cpu13Q1=0;if(cpuCounter)cpuCounter(&cpu13Q0);'+q+'cpu13QueryScope=0;cpu13OwnShape=0;'+'if(cpuCounter&&cpu13Phase<11){cpuCounter(&cpu13Q1);cpu13Totals[cpu13Phase][16]+=cpu13Q1-cpu13Q0;cpu13Totals[cpu13Phase][17]++;if(hit)cpu13Totals[cpu13Phase][18]++;}')
s+='\n'+(r/'tests/cpu6_movement_replay.inc').read_text(encoding='utf-8-sig')
if '--hand-mesh-release' in sys.argv:
 adapter=(r/'source/cpu_hand_mesh.inc').read_text()
 needle44='c43_begin(1);c44Execute(p);c43Active=0;'
 assert adapter.count(needle44)==1
 adapter=adapter.replace(needle44,'u64 c44T=c44_now();c43_begin(1);c44Execute(p);c43Active=0;cpu14_event(67,0,c44T,c44_now(),c43Hits);')
 s=s.replace('#include "cpu_hand_mesh.inc"',adapter)

prof=(r/'source/cpu_work_profile.inc').read_text()
prof=prof.replace('cpuRenderRows<10&&','')
prof=prof.replace('||cpuRows>=12','||cpu13Phase>10')
prof=prof.replace('for(u32 i=0;i<H5755EG_P_COUNT;i++)cpuTotal[i]+=cpuBucket[i];', 'if(cpu13Phase<11){cpu13Steps[cpu13Phase]++;for(u32 i=0;i<H5755EG_P_COUNT&&i<32;i++)cpu13Totals[cpu13Phase][i]+=cpuBucket[i];}for(u32 i=0;i<H5755EG_P_COUNT;i++)cpuTotal[i]+=cpuBucket[i];')
prof=prof.replace('if(cpuRenderWarm++<120)', 'if(cpuRenderRows>=10)return;\n if(cpuRenderWarm++<120)')
prof=prof.replace('u64 t=cpu_observe_tick();if(!t0||t<t0)return;', 'u64 t=cpu_observe_tick();if(!t0||t<t0)return;cpu6Scene+=1000.0*sceneTicks/cpuFreq;cpu6XR+=1000.0*xrTicks/cpuFreq;',1)
prof=prof.replace('cpu_detail_end(0,t,empty);','cpu_detail_end(0,t,empty);if(t){u64 q=0;cpuCounter(&q);cpu6Texture+=1000.0*(q-t)/cpuFreq;}',1)
if '--frame-attribution' in sys.argv:
 s=s.replace('cpu13_pair_install();cpu13OwnShape=', 'cpu13OwnShape=')
 prof=prof.replace('if(cpuRows==12){cpu_metadata_census(world);cpu_near_probe(world);}', '')
if '--event-trace' in sys.argv:
 from cpu14_instrument import augment
 s,prof=augment(r,s,prof)
if '--texture-attribution' in sys.argv:
 assert '--event-trace' in sys.argv and '--frame-attribution' in sys.argv
 from cpu15_instrument import augment
 s,prof=augment(r,s,prof,defer='--defer-bitmap-free' in sys.argv,paired='--paired-bitmap-free' in sys.argv)
if '--map-attribution' in sys.argv:
 assert '--event-trace' in sys.argv and '--frame-attribution' in sys.argv
 prof='static void cpu16_install(void);\n'+prof
 prof=prof.replace('cpu_detail_install();cpu_job_install();','cpu_detail_install();cpu16_install();cpu_job_install();')
 prof+='\n'+(r/'tests/cpu16_map.inc').read_text()
 s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==15')
 s=s.replace('cpu14Saved||cpu13Phase>10||!a', 'cpu14Saved||(cpu13Phase>10&&!(kind==15&&cpu13Phase==99))||!a')
 s=s.replace('static void cpu14_save(void){','static void cpu14_save(void){for(u32 i=0;i<5;i++)ext_Log(">>> CPU16_MAP_TOTAL stage %u calls %llu total_ms %.6f",i,cpu16Calls[i],1000.0*cpu16Ticks[i]/cpuFreq);')
if '--gui-install-timing' in sys.argv:
 s=s.replace('static i32 s26_gui_install(void){','static i32 cpu16_gui_install_body(void){',1)
 marker='static void h576bq_resolve_stock_mouse(void){'
 wrapper=r"""static i32 s26_gui_install(void){
 if(g_s26GuiTried)return g_s26GuiReady;
 void*k=ext_GetModuleHandleA("kernel32.dll");
 i32 (__attribute__((ms_abi))*q)(u64*)=(void*)ext_GetProcAddress(k,"QueryPerformanceCounter");
 i32 (__attribute__((ms_abi))*f)(u64*)=(void*)ext_GetProcAddress(k,"QueryPerformanceFrequency");
 u64 a=0,b=0,hz=0;if(f)f(&hz);if(q)q(&a);
 i32 result=cpu16_gui_install_body();if(q)q(&b);
 ext_Log(">>> CPU16_GUI_INSTALL ready %d cursor %d ms %.6f",result,g_s26anCursorReady,hz?1000.0*(b-a)/hz:0.0);
 return result;
}
"""
 assert s.count(marker)==1;s=s.replace(marker,wrapper+marker)
 if '--gui-prewarm' in sys.argv:
  anchor='    h5748n_try_install_entity_hook();\n    h5755ad_try_install_graphics_owner_hook();'
  assert anchor in s[s.index('u32 __attribute__((ms_abi)) s6_h5748n_load_thread_wrapper'):s.index('/* H57.55CP:')]
  s=s.replace(anchor,'    s26_gui_install(); /* private candidate: same verified hooks before map updates */\n'+anchor,1)
if '--gpu-texture-attribution' in sys.argv:
 assert '--texture-attribution' in sys.argv and '--gui-prewarm' in sys.argv
 extra=(r/'tests/cpu17_texture.inc').read_text()
 prof=prof.replace('static i32 h21_copy_ascii(const void*,char*,u32);',extra+'\nstatic i32 h21_copy_ascii(const void*,char*,u32);',1)
 prof=prof.replace('u64 t=cpu_detail_begin();cpuRetireOriginal(p);', 'u64 t=cpu_detail_begin();if(t)cpu17RetireDepth++;cpuRetireOriginal(p);if(t)cpu17RetireDepth--;',1)
 assert prof.count('cpu15_free_init();cpu_texture_trial_install();')==1
 prof=prof.replace('static void cpu_texture_install(void){','static void cpu_texture_install(void){cpu17_install();',1)
 assert prof.count('cpu_texture_install(void){cpu17_install();')==1
 assert prof.index('cpu_texture_install(void){cpu17_install();')<prof.index('cpu_detail_hook(0x56a820')
 storage=(r/'source/cpu_texture_storage_trial.inc').read_text()
 storage=storage.replace('cpuTrialEnabled=1;', 'cpu17StorageOriginal=cpuTrialStorage;cpu17SubOriginal=cpuTrialSub;cpuTrialStorage=cpu17_storage;cpuTrialSub=cpu17_sub;cpuTrialEnabled=1;',1)
 prof=prof.replace('#include "cpu_texture_storage_trial.inc"',storage)
 s=s.replace('kind==8||kind==10||kind==11||kind==12', 'kind==8||kind==10||kind==11||kind==12||kind==16')
if '--input-attribution' in sys.argv:
 assert '--event-trace' in sys.argv and '--frame-attribution' in sys.argv
 prof='static void cpu17_input_install(void);\n'+prof
 assert prof.count('cpu_detail_install();')==1
 prof=prof.replace('cpu_detail_install();','cpu_detail_install();cpu17_input_install();',1)
 prof+='\n'+(r/'tests/cpu17_input.inc').read_text()
 s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==17')
if '--post-attribution' in sys.argv:
 assert '--event-trace' in sys.argv and '--frame-attribution' in sys.argv
 prof='static void cpu18_post_install(void);\n'+prof
 assert prof.count('cpu_detail_install();')==1
 prof=prof.replace('cpu_detail_install();','cpu_detail_install();cpu18_post_install();',1)
 prof+='\n'+(r/'tests/cpu18_post.inc').read_text()
 needle=' cpuModuleOriginal(object,event,dt);'
 assert prof.count(needle)==1
 prof=prof.replace(needle,' if(t0&&event==6&&vt-(u64)ext_GetModuleHandleA(0)==0x6c2b58){u8*p=object;u32 flags=(p[0x98]!=0)|((*(void**)(p+0x158)!=0)<<1)|((p[0x160]!=0)<<2)|((*(void**)(p+0x148)!=0)<<3)|((p[0x3c8]!=0)<<4);cpu14_event(22,flags,t0,t0,*(u64*)(p+0x3b8));}\n'+needle,1)
 s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==21')
if '--newton-attribution' in sys.argv:
 assert '--event-trace' in sys.argv and '--frame-attribution' in sys.argv
 prof='static void cpu18_newton(const void*,u64,u64);\n'+prof
 prof+='\n'+(r/'tests/cpu18_newton.inc').read_text()
 needle='cpu14_event(9,0,cpu6NT0,cpu6NT1,0);'
 assert s.count(needle)==1
 s=s.replace(needle,needle+'cpu18_newton(world,cpu6NT0,cpu6NT1);',1)
if '--newton-clock' in sys.argv:
 assert '--newton-attribution' in sys.argv
 prof='static u32 cpu25_begin(const void*);static void cpu25_end(const void*,u32);\n'+prof
 prof+='\n'+(r/'tests/cpu25_clock.inc').read_text()
 needle='o_h14NewtonUpdate(world,timestep);'
 assert s.count(needle)==1
 s=s.replace(needle,'u32 cpu25Active=cpu25_begin(world);'+needle,1)
 needle='cpu18_newton(world,cpu6NT0,cpu6NT1);'
 assert s.count(needle)==1
 s=s.replace(needle,needle+'cpu25_end(world,cpu25Active);',1)
 if '--newton-clock-paired' in sys.argv:
  # Observation only. Alternate ABBA within one world to reduce between-run
  # differences from actual initial controller orientation and contact history.
  prof=prof.replace('static u32 cpu25Ready,cpu25Valid;', 'static u32 cpu25Sequence;static u32 cpu25Ready,cpu25Valid;',1)
  prof=prof.replace('cpu25SetClock(w,cpu25_clock);return 1;', 'if(((cpu25Sequence++)&3u)==0u||((cpu25Sequence-1u)&3u)==3u)return 0;cpu25SetClock(w,cpu25_clock);return 1;',1)
  s=s.replace('cpu25_end(world,cpu25Active);','cpu25_end(world,cpu25Active);u64 cpu25End=0;cpuCounter(&cpu25End);cpu14_event(32,cpu25Active,cpu6NT0,cpu25End,cpu6NT1);',1)
if '--newton-clock-paired' in sys.argv:assert '--newton-clock' in sys.argv
if '--collision-callbacks' in sys.argv:
 assert '--newton-clock' in sys.argv and '--newton-clock-paired' not in sys.argv
 prof='static void cpu26_install(void);static void cpu26_before(const void*);static void cpu26_after(u64,u64);\n'+prof
 prof=prof.replace('cpu_detail_install();','cpu_detail_install();cpu26_install();',1)
 prof+='\n'+(r/'tests/cpu26_callbacks.inc').read_text()
 s=s.replace('u32 cpu25Active=cpu25_begin(world);','cpu26_before(world);u32 cpu25Active=cpu25_begin(world);',1)
 s=s.replace('cpu25_end(world,cpu25Active);','cpu25_end(world,cpu25Active);cpu26_after(cpu6NT0,cpu6NT1);',1)
 needle='static u64 __attribute__((ms_abi)) s26_overlap_detour('
 assert s.count(needle)==1
 s=s.replace(needle,'static u64 __attribute__((ms_abi)) cpu26_overlap_body(',1)
 marker='static void s26_install_held_filter(u8* soma){'
 assert s.count(marker)==1
 s=s.replace(marker,'''static u64 __attribute__((ms_abi)) s26_overlap_detour(const void*m,const void*a,const void*b,i32 thread){u64 t=cpu26_begin_callback(thread);u64 result=cpu26_overlap_body(m,a,b,thread);cpu26_end_callback(0,thread,t);return result;}
'''+marker,1)
 needle='static i32 __attribute__((ms_abi)) h530_hand_overlap_filter('
 assert s.count(needle)==1
 s=s.replace(needle,'static i32 __attribute__((ms_abi)) cpu26_hand_body(',1)
 marker='static void h530_install_pair(const void* world,i32 mat){'
 assert s.count(marker)==1
 s=s.replace(marker,'''static i32 __attribute__((ms_abi)) h530_hand_overlap_filter(const void*m,const void*a,const void*b,i32 thread){u64 t=cpu26_begin_callback(thread);i32 result=cpu26_hand_body(m,a,b,thread);cpu26_end_callback(2,thread,t);return result;}
'''+marker,1)
if '--xml-trial' in sys.argv:
 assert '--post-attribution' in sys.argv
 prof='static void cpu19_install(void);\n'+prof
 prof=prof.replace('cpu18_post_install();','cpu18_post_install();cpu19_install();',1)
 prof+='\n'+(r/'tests/cpu19_xml.inc').read_text()
 s=s.replace('static void cpu14_save(void){','static void cpu14_save(void){ext_Log(">>> CPU19_XML_CALLS %llu",cpu19Calls);',1)
if '--xml-budget-trial' in sys.argv:
 assert '--post-attribution' in sys.argv and '--xml-trial' not in sys.argv
 prof='static void cpu20_scope(void*);static void cpu20_drain(void);static void cpu20_init(void);static i32 cpu20_retire(void*,u32);static void cpu20_unscope(void);\n'+prof
 prof=prof.replace('cpu18_post_install();','cpu18_post_install();cpu20_init();',1)
 prof=prof.replace('cpu18UpdateOriginal(p,arg,budget);','cpu20_scope(p);cpu18UpdateOriginal(p,arg,budget);cpu20_unscope();',1)
 prof=prof.replace('void*result=cpu18_xmlOriginal(p,flags);','void*result=cpu20_retire(p,flags)?p:cpu18_xmlOriginal(p,flags);',1)
 prof=prof.replace(' cpuModuleOriginal(object,event,dt);',' cpuModuleOriginal(object,event,dt);if(event==6&&object&&*(u64*)object-(u64)ext_GetModuleHandleA(0)==0x6c2b58)cpu20_drain();',1)
 prof+='\n'+(r/'tests/cpu20_xml.inc').read_text()+'\nstatic void cpu20_unscope(void){cpu20Eligible[0]=cpu20Eligible[1]=0;}\n'
 s=s.replace('static void cpu14_save(void){','static void cpu14_save(void){ext_Log(">>> CPU20_XML accepted %llu nodes %llu fallback %llu pending %u depth %u slices %llu total_ms %.4f max_ms %.4f",cpu20Accepted,cpu20Nodes,cpu20Fallback,cpu20Count,cpu20Depth,cpu20Slices,1000.0*cpu20Ticks/cpuFreq,1000.0*cpu20Max/cpuFreq);',1)
if '--xml-observer' in sys.argv:
 assert '--long-replay' in sys.argv and '--post-attribution' in sys.argv
 # Deliberately no synthetic input: paired loader timing does not require hands.
 s=s.replace('    cpu6_pose(displayTime);','    /* XML observer: live input unchanged. */',1)
 s=s.replace('    cpu6_controls();','    /* XML observer: no synthetic controls. */',1)
 s=s.replace('static void cpu6_pose(i64);','static void cpu20_observe(void);static void cpu6_pose(i64);',1)
 prof=prof.replace(' cpuModuleOriginal(object,event,dt);',' if(event==6)cpu20_observe();cpuModuleOriginal(object,event,dt);',1)
 s+='\nstatic void cpu20_observe(void){static u64 begin;u64 now=0;if(g_h5755bhPresentationState!=H5755BH_GAMEPLAY_VR||!cpuCounter||!cpuFreq||!cpuThreadId||cpuThreadId()!=cpuMainThread)return;cpuCounter(&now);if(!begin)begin=now;cpu13Phase=0;if(now-begin>=100*cpuFreq&&!cpu14Saved){cpu14_save();ext_Log(">>> CPU20_OBSERVER_SAVED native loader only, no synthetic input or hand assertions");}}\n'
if '--entity-attribution' in sys.argv:
 assert '--post-attribution' in sys.argv
 prof='static void cpu21_install(void);\n'+prof
 prof=prof.replace('cpu18_post_install();','cpu18_post_install();cpu21_install();',1)
 prof+='\n'+(r/'tests/cpu21_entities.inc').read_text()
 s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==27')
if '--buffer-verify' in sys.argv:
 assert '--buffer-pack' in sys.argv
 prof='#define CPU24_VERIFY 1\n'+prof
if '--buffer-pack' in sys.argv:
 assert '--buffer-attribution' in sys.argv and '--buffer-staging' not in sys.argv
 prof='#define CPU24_PACK 1\n'+(r/'tests/cpu24_pack.inc').read_text()+'\n'+prof
if '--buffer-staging' in sys.argv:
 assert '--buffer-attribution' in sys.argv
 prof='#define CPU23_STAGING 1\n'+prof
if '--buffer-attribution' in sys.argv:
 assert '--post-attribution' in sys.argv
 prof='static void*cpu24Expected;static unsigned int cpu23Eligible;static void cpu23_buffer_snapshot(void*);\n'+prof
 needle='cpu18UpdateOriginal(p,arg,budget);'
 assert prof.count(needle)==1
 scope='cpu23_buffer_snapshot(p);'+needle+'cpu23Eligible=0;cpu24Expected=0;'
 bridge=(r/'tests/cpu23_buffers.inc').read_text()
 if '--buffer-independent' in sys.argv:
  assert '--buffer-pack' in sys.argv and '--buffer-staging' not in sys.argv
  from cpu28_transform import transform
  bridge=transform(bridge)
  scope='if(cpuThreadId&&cpuThreadId()==cpuMainThread){void*cpu28SavedExpected=cpu24Expected;u32 cpu28SavedEligible=cpu23Eligible;cpu23_buffer_snapshot(p);'+needle+'cpu23Eligible=cpu28SavedEligible;cpu24Expected=cpu28SavedExpected;}else{'+needle+'}'
 prof=prof.replace(needle,scope,1)
 prof+='\n'+bridge
 s=s.replace('kind==8||kind==10||kind==11||kind==12','kind==8||kind==10||kind==11||kind==12||kind==29')
if '--visibility-preinit' in sys.argv:
 assert '--entity-attribution' in sys.argv
 prof='static void cpu22_install(void);\n'+prof
 prof=prof.replace('cpu21_install();','cpu21_install();cpu22_install();',1)
 prof+='\n'+(r/'tests/cpu22_visibility.inc').read_text()
if '--visibility-membership' in sys.argv:
 assert '--entity-attribution' in sys.argv
 prof='static void cpu29_install(void);\n'+prof
 prof=prof.replace('cpu21_install();','cpu21_install();cpu29_install();',1)
 prof+='\n'+(r/'tests/cpu29_membership.inc').read_text()
if '--xml-lifetime' in sys.argv and '--xml-budget-trial' in sys.argv:
 assert '--xml-observer' in sys.argv
 prof=prof.replace('static void cpu20_drain(void){','static void cpu20_drain(void){static void* heldWorld;static u32 released,reported;if(!released){if(cpu20Count&&!reported){reported=1;ext_Log(">>> CPU20_LIFETIME_HOLD roots %u",cpu20Count);}if(cpu20Accepted<4)return;if(!heldWorld){heldWorld=(void*)g_h14NewtonWorld;return;}if(!g_h14NewtonWorld||heldWorld==(void*)g_h14NewtonWorld)return;released=1;ext_Log(">>> CPU29_LIFETIME_WORLD_CHANGED old %p new %p pending %u",heldWorld,g_h14NewtonWorld,cpu20Count);}',1)
 prof=prof.replace('cpu20Count++;cpu20Accepted++;return 1;','cpu20Count++;cpu20Accepted++;ext_Log(">>> CPU20_LIFETIME_ENQUEUE accepted %llu pending %u frame %u world %p",cpu20Accepted,cpu20Count,g_frameCounter,g_h14NewtonWorld);return 1;',1)
if '--xml-exit-hold' in sys.argv:
 assert '--xml-observer' in sys.argv and '--xml-budget-trial' in sys.argv and '--xml-lifetime' not in sys.argv
 prof=prof.replace('static void cpu20_drain(void){','static void cpu20_drain(void){if(cpu20Count)return; /* shutdown ownership stress only */',1)
if '--long-replay' in sys.argv:
 assert '--delta-route' not in sys.argv
 s=s.replace('cpu6Rows[12000]','cpu6Rows[24000]').replace('cpu6Count<12000','cpu6Count<24000').replace('t>=52.f','t>=100.f')
 s=s.replace('cpu14Events[200000]','cpu14Events[400000]').replace('cpu14Count>=200000','cpu14Count>=400000')
if '--delta-route' in sys.argv:
 assert '--input-attribution' in sys.argv
 s=s.replace('cpu6Rows[12000]','cpu6Rows[24000]').replace('cpu6Count<12000','cpu6Count<24000').replace('t>=52.f','t>=190.f')
 s=s.replace('cpu14Events[200000]','cpu14Events[600000]').replace('cpu14Count>=200000','cpu14Count>=600000')
 needle='cpu6LastTick=now;'
 assert s.count(needle)==1
 s=s.replace(needle,'''if(now&&p2_camera_obj()){float*pos=(float*)((u8*)p2_camera_obj()+0x10);union{float f;u32 u;} x,y,z;x.f=pos[0];y.f=pos[1];z.f=pos[2];cpu14_event(18,y.u,now,now,((u64)x.u<<32)|z.u);}'''+needle)
if '--hand-validation' in sys.argv:
 needle='static i32 h5755ct_noncharacter_body_eligible(i32 hand,const void* body){'
 assert s.count(needle)==1
 s=s.replace(needle,(r/'tests/cpu27_validation.inc').read_text()+'\n'+needle,1)
 needle='!w||!h20_mem_readable((u8*)w+0x2e0,1)||!h20_mem_readable((u8*)w+0x258,4)||!h20_mem_readable((u8*)w+0x240,4)||!h20_mem_readable((u8*)w+0x0e4,1)'
 assert s.count(needle)==1
 replacement='!cpu27_wrapper_readable(w)'
 if '--hand-validation-paired' in sys.argv:
  replacement='(((g_h14PhysicsSteps/120u)%4u==1u||(g_h14PhysicsSteps/120u)%4u==2u)?!cpu27_wrapper_readable(w):('+needle+'))'
 s=s.replace(needle,replacement,1)
if '--local-proof-paired' in sys.argv:
 assert '--hand-helper-cost' not in sys.argv and '--collision-callbacks' not in sys.argv
 from cpu31_transform import transform as local_transform
 s=local_transform(s)
if '--hand-helper-cost' in sys.argv:
 assert '--collision-callbacks' in sys.argv and '--hand-validation' not in sys.argv
 from cpu30_helpers import augment as helper_augment
 s,prof=helper_augment(s,prof)
if '--worker-cycles' in sys.argv:
 assert '--event-trace' in sys.argv and '--newton-workers-2' not in sys.argv and '--collision-callbacks' not in sys.argv
 prof='static void cpu34_begin(const void*);static void cpu34_after(u64,u64);\n'+prof+'\n'+(r/'tests/cpu34_cycles.inc').read_text()
 needle='o_h14NewtonUpdate(world,timestep);'
 assert s.count(needle)==1
 s=s.replace(needle,'cpu34_begin(world);'+needle,1)
 needle='cpuCounter(&cpu6NT1);'
 assert s.count(needle)==1
 s=s.replace(needle,needle+'cpu34_after(cpu6NT0,cpu6NT1);',1)
if '--main-native-clock' in sys.argv:
 assert '--worker-cycles' in sys.argv and '--newton-clock' in sys.argv and '--newton-clock-paired' not in sys.argv
 prof='static void cpu35_point(void*,u64);static u32 cpu34Active;\n'+prof+'\n'+(r/'tests/cpu35_point.inc').read_text()
 needle='cpuCounter(&t);return (u32)((t/cpuFreq)*1000000ULL+'
 assert prof.count(needle)==1
 prof=prof.replace(needle,'cpuCounter(&t);cpu35_point(__builtin_return_address(0),t);return (u32)((t/cpuFreq)*1000000ULL+',1)
 needle='if(!w||!cpu_detail_begin()||!cpuCounter||!cpuFreq||cpu14Saved)return 0;'
 assert prof.count(needle)==1
 prof=prof.replace(needle,'if(!cpu34Active)return 0;'+needle,1)
 s=s.replace('cpu34_begin(world);o_h14NewtonUpdate','o_h14NewtonUpdate',1)
 s=s.replace('u32 cpu25Active=cpu25_begin(world);','cpu34_begin(world);u32 cpu25Active=cpu25_begin(world);',1)
if '--paired-sse' in sys.argv:
 assert '--event-trace' in sys.argv and '--parallel-sse' not in sys.argv and '--main-native-clock' not in sys.argv and '--collision-callbacks' not in sys.argv
 code=('#define C37_MIN_PAIRS 2\n' if '--sse-small-batches' in sys.argv else '')+(r/'tests/cpu37_game.inc').read_text()+(r/'tests/cpu37_core.inc').read_text()+(r/'tests/cpu37_report.inc').read_text()
 if '--narrow-zero' in sys.argv:
  assert '--pair-cost' not in sys.argv and '--adaptive-sse' not in sys.argv
  from cpu43_transform import transform as narrow_zero
  code=narrow_zero(code,r,shadow='--reuse-zero' not in sys.argv,invert='--invert-sse' in sys.argv)
 if '--pair-cost' in sys.argv:
  assert '--adaptive-sse' not in sys.argv
  from cpu41_transform import transform as pair_cost
  code=pair_cost(code,r,metadata="--pair-metadata" in sys.argv)
 if '--adaptive-sse' in sys.argv:
  assert '--sse-small-batches' in sys.argv
  from cpu38_transform import transform as adapt_schedule
  code=adapt_schedule(code,r,serial_cost="--serial-cost-sse" in sys.argv,invert="--invert-sse" in sys.argv)
 prof='static void c37_install(void);\n'+prof+'\n'+code
 prof=prof.replace('cpu_detail_install();','cpu_detail_install();c37_install();',1)
 s=s.replace('static CPU14Event cpu14Events[600000]','static CPU14Event cpu14Events[900000]').replace('cpu14Count>=600000','cpu14Count>=900000')
 s=s.replace('static CPU14Event cpu14Events[200000]','static CPU14Event cpu14Events[900000]').replace('cpu14Count>=200000','cpu14Count>=900000')
 assert 'cpu14Events[900000]' in s and 'cpu14Count>=900000' in s
if '--parallel-sse' in sys.argv:
 assert '--main-native-clock' not in sys.argv and '--newton-workers-2' not in sys.argv and '--collision-callbacks' not in sys.argv
 code=(r/'tests/cpu36_parallel.inc').read_text().replace('memcpy(', '__builtin_memcpy(')
 # Worker entries from our temporary vtable use the original trampoline;
 # unrelated native generic jobs must retain their existing floating point state.
 code=code.replace('if(*(int*)(j+0x18)!=1||', 'if(cpuThreadId()!=cpuMainThread){c36Execute(j);return;}if(*(int*)(j+0x18)!=1||',1)
 # Temporary vtable calls use a separate worker wrapper with the captured main MXCSR.
 code=code.replace('static void c36_job(void*arg){','static void c36_worker(void*arg){unsigned old=c36_getmx();c36_setmx(c36Mx);c36Execute(arg);c36_setmx(old); }\nstatic void c36_job(void*arg){',1)
 code=code.replace('void*vt[1]={(void*)c36_job};','void*vt[1]={(void*)c36_worker};',1)
 prof='static void c36_install(void);\n'+prof+'\n'+code+'\n'+(r/'tests/cpu36_install.inc').read_text()
 prof=prof.replace('cpu_detail_install();','cpu_detail_install();c36_install();',1)
 needle='if(cpu14Saved)return;cpu14Saved=1;'
 assert s.count(needle)==1
 s=s.replace(needle,'if(cpu14Saved)return;u64 c36Stamp=0;cpuCounter(&c36Stamp);cpu14_event(52,0,c36Stamp,c36Stamp,c36Runs);ext_Log(">>> CPU36 private dispatch batches %llu",c36Runs);cpu14Saved=1;',1)
if '--newton-workers-2' in sys.argv:
 assert '--collision-callbacks' not in sys.argv and '--local-proof-paired' not in sys.argv
 needle='o_h14NewtonUpdate(world,timestep);'
 assert s.count(needle)==1
 s=s.replace(needle,'cpu33_workers(world);'+needle)
 s='static void cpu33_workers(const void*);\n'+s+'\n'+(r/'tests/cpu33_workers.inc').read_text()
if '--collision-pairs' in sys.argv:
 assert '--collision-callbacks' in sys.argv and '--hand-helper-cost' not in sys.argv and '--hand-validation' not in sys.argv
 from cpu32_transform import augment as pair_augment
 s,prof=pair_augment(s,prof)
(b/'cpu_work_profile.inc').write_text(prof)
(b/'test.c').write_text(s)
zig=str(r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe')
subprocess.run([zig,'cc',f'-DCPU_HAND_MESH={int("--hand-mesh-release" in sys.argv)}',f'-DCPU_STREAMING_OPTIMISATIONS={int("--streaming-release" in sys.argv)}','-target','x86_64-windows-gnu','-DCPU_WORK_PROFILE=1','-DCPU_RENDER_JOBS=1','-DCPU_TEXTURE_MIN_BYTES=65536','-DCPU_STRING_SPANS=1','-DCPU_NEAR_TYPES=1','-DCPU_TEXTURE_STORAGE=1','-DCPU_TEXTURE_LATC=1','-DS26IU_TEST=1','-I',str(r/'source'),'-O2','-g0','-ffreestanding','-fno-asynchronous-unwind-tables','-fno-ident','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-parameter','-c',str(b/'test.c'),'-o',str(b/'test.obj')],check=True)
subprocess.run([sys.executable,str(r/'scripts/apply_payload.py'),str(r/'third_party/hpl3vr_S5-P2_base.dll'),str(b/'test.obj'),str(b/'hpl3vr.dll')],check=True)
files=list((r/'source').glob('*'))+[r/'tests/cpu43_reuse.inc',r/'tests/cpu43_transform.py',r/'tests/cpu41_names.inc',r/'tests/cpu41_pair.inc',r/'tests/cpu41_transform.py',r/'tests/cpu40_policy.inc',r/'tests/cpu38_policy.inc',r/'tests/cpu38_transform.py',r/'tests/cpu37_core.inc',r/'tests/cpu37_game.inc',r/'tests/cpu37_report.inc',r/'tests/cpu36_parallel.inc',r/'tests/cpu36_install.inc',r/'tests/cpu35_point.inc',r/'tests/cpu34_cycles.inc',r/'tests/cpu33_workers.inc',r/'tests/cpu32_pairs.inc',r/'tests/cpu32_transform.py',r/'tests/cpu29_membership.inc',r/'tests/cpu28_transform.py',r/'tests/cpu27_validation.inc',r/'tests/cpu26_callbacks.inc',r/'tests/cpu25_clock.inc',r/'tests/cpu24_pack.inc',r/'tests/cpu23_buffers.inc',r/'tests/cpu22_visibility.inc',r/'tests/cpu21_entities.inc',r/'tests/cpu20_xml.inc',r/'tests/cpu19_xml.inc',r/'tests/cpu18_post.inc',r/'tests/cpu18_newton.inc',r/'tests/cpu18_route.hps',r/'tests/cpu17_input.inc',r/'tests/cpu17_texture.inc',r/'tests/cpu16_map.inc',r/'tests/cpu15_defer.inc',r/'tests/cpu15_instrument.py',r/'tests/cpu14_events.inc',r/'tests/cpu14_instrument.py',r/'tests/cpu13_held_query.inc',r/'tests/cpu13_query_oracle.inc',r/'tests/cpu6_movement_replay.inc',r/'tests/smaa_observer_iu.inc',b/'test.c',b/'cpu_work_profile.inc']
(b/'build-receipt.json').write_text(json.dumps({'arguments':{'production':False,'hand_mesh_release':'--hand-mesh-release' in sys.argv,'narrow_zero':'--narrow-zero' in sys.argv,'reuse_zero':'--reuse-zero' in sys.argv,'pair_metadata':'--pair-metadata' in sys.argv,'pair_cost':'--pair-cost' in sys.argv,'invert_sse':'--invert-sse' in sys.argv,'serial_cost_sse':'--serial-cost-sse' in sys.argv,'schedule_prime':'--adaptive-sse' in sys.argv,'adaptive_sse':'--adaptive-sse' in sys.argv,'sse_small_batches':'--sse-small-batches' in sys.argv,'paired_sse':'--paired-sse' in sys.argv,'parallel_sse':'--parallel-sse' in sys.argv,'main_native_clock':'--main-native-clock' in sys.argv,'worker_cycles':'--worker-cycles' in sys.argv,'newton_workers_2':'--newton-workers-2' in sys.argv,'collision_pairs':'--collision-pairs' in sys.argv,'local_proof_paired':'--local-proof-paired' in sys.argv,'hand_helper_cost':'--hand-helper-cost' in sys.argv,'streaming_release':'--streaming-release' in sys.argv,'visibility_membership':'--visibility-membership' in sys.argv,'buffer_independent':'--buffer-independent' in sys.argv,'hand_validation_paired':'--hand-validation-paired' in sys.argv,'hand_validation':'--hand-validation' in sys.argv,'collision_callbacks':'--collision-callbacks' in sys.argv,'buffer_verify':'--buffer-verify' in sys.argv,'buffer_pack':'--buffer-pack' in sys.argv,'buffer_staging':'--buffer-staging' in sys.argv,'buffer_attribution':'--buffer-attribution' in sys.argv,'xml_exit_hold':'--xml-exit-hold' in sys.argv,'entity_attribution':'--entity-attribution' in sys.argv,'visibility_preinit':'--visibility-preinit' in sys.argv,'xml_lifetime':'--xml-lifetime' in sys.argv,'xml_observer':'--xml-observer' in sys.argv,'xml_budget_trial':'--xml-budget-trial' in sys.argv,'xml_trial':'--xml-trial' in sys.argv,'long_replay':'--long-replay' in sys.argv,'post_attribution':'--post-attribution' in sys.argv,'newton_clock':'--newton-clock' in sys.argv,'newton_clock_paired':'--newton-clock-paired' in sys.argv,'newton_attribution':'--newton-attribution' in sys.argv,'delta_route':'--delta-route' in sys.argv,'input_attribution':'--input-attribution' in sys.argv,'map_attribution':'--map-attribution' in sys.argv,'gpu_texture_attribution':'--gpu-texture-attribution' in sys.argv,'gui_install_timing':'--gui-install-timing' in sys.argv,'gui_prewarm':'--gui-prewarm' in sys.argv,'event_trace':'--event-trace' in sys.argv,'frame_attribution':'--frame-attribution' in sys.argv,'texture_attribution':'--texture-attribution' in sys.argv,'defer_bitmap_free':'--defer-bitmap-free' in sys.argv,'paired_bitmap_free':'--paired-bitmap-free' in sys.argv},'dll_sha256':hashlib.sha256((b/'hpl3vr.dll').read_bytes()).hexdigest(),'source_hashes':{p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},'scope':'isolated synthetic controller replay; production source unmodified'},indent=2))

