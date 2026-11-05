from pathlib import Path

def augment(r,s,prof):
 declarations='static void cpu14_event(u32,u32,u64,u64,u64);static i32 cpu14_gpu_begin(void);static void cpu14_gpu_end(i32);static void cpu14_save(void);\n'
 # Types are available at the profiler include; functions are defined at file end.
 prof=declarations+prof
 prof=prof.replace('cpuBucket[b]+=h5755eg_tick()-t0;', '{u64 end=h5755eg_tick();cpuBucket[b]+=end-t0;cpu14_event(8,(u32)b,t0,end,0);}')
 prof=prof.replace('if(cpuRenderRows>=10)return;', 'cpu14_event(1,0,t0,t,0);if(cpuRenderRows>=10)return;')
 prof=prof.replace('cpuModules[slot].calls++;','cpuModules[slot].calls++;cpu14_event(10,(u32)event,t0,t1,vt-(u64)ext_GetModuleHandleA(0));')
 prof=prof.replace('CPUDetailRow*r=cpuDetails+slot;', 'cpu14_event(11,slot,t0,end,0);CPUDetailRow*r=cpuDetails+slot;')
 prof=prof.replace('cpu9_before_wait(p);cpuWaitOriginal(p);cpu_detail_end(2,t,empty);','cpu9_before_wait(p);cpuWaitOriginal(p);cpu_detail_end(2,t,empty);if(t){u64 end=0;cpuCounter(&end);cpu14_event(12,empty,t,end,caller);}')
 # Profile include precedes renderer and native update definitions.
 a='egT=cpu_observe_tick();h5755eq_call_original_drender(a,b,c,d,e,f,g,h);egT1=cpu_observe_tick();'
 assert s.count(a)==4
 s=s.replace(a,'egT=cpu_observe_tick();i32 cpu14ticket=cpu14_gpu_begin();h5755eq_call_original_drender(a,b,c,d,e,f,g,h);cpu14_gpu_end(cpu14ticket);egT1=cpu_observe_tick();cpu14_event(2,0,egT,egT1,0);')
 s=s.replace('if(egT&&egT1>egT)egXrTicks+=egT1-egT;', 'cpu14_event(3,0,egT,egT1,0);if(egT&&egT1>egT)egXrTicks+=egT1-egT;',1)
 s=s.replace('cpu6Newton+=1000.0*(cpu6NT1-cpu6NT0)/cpuFreq;', 'cpu6Newton+=1000.0*(cpu6NT1-cpu6NT0)/cpuFreq;cpu14_event(9,0,cpu6NT0,cpu6NT1,0);',1)
 s=s.replace('cpu6Done=1;for(u32 ph=', 'cpu6Done=1;cpu14_save();for(u32 ph=',1)
 s+='\n'+(r/'tests/cpu14_events.inc').read_text()
 return s,prof
