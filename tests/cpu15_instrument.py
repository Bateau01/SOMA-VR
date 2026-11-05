def augment(r,s,prof,defer=False,paired=False):
 tex=(r/'source/cpu_texture_profile.inc').read_text()
 tex=tex.replace('cpu_texture_cost(0,t,end,0,0);','cpu_texture_cost(0,t,end,0,0);cpu14_event(13,0,t,end,((u64)*(u32*)((u8*)p+0xb0)<<32)|*(u32*)((u8*)p+0xb4));')
 tex=tex.replace('cpu_texture_cost(1,t,end,bytes>0?(u32)bytes:0,t?*(u8*)((u8*)p+0xea):0);','cpu_texture_cost(1,t,end,bytes>0?(u32)bytes:0,t?*(u8*)((u8*)p+0xea):0);cpu14_event(13,1,t,end,bytes>0?(u32)bytes:0);')
 tex=tex.replace('cpu_texture_cost(2,t,end,0,0);','cpu_texture_cost(2,t,end,0,0);cpu14_event(13,2,t,end,bytes);')
 tex=tex.replace('cpu_texture_cost(3,t,end,0,0);','cpu_texture_cost(3,t,end,0,0);cpu14_event(13,3,t,end,0);')
 helper="""static CPUObjectCall cpu15DestroyOriginal;
static void __attribute__((ms_abi)) cpu15_destroy(void*p){u64 t=cpuStorageStreamingDepth?cpu_detail_begin():0;u64 size=0;u32 deferred=0;if(t){u64 a=*(u64*)p,b=*((u64*)p+1);if(a&&b>=a&&(b-a)%16==0&&(b-a)/16<=16)for(u64 x=a;x<b;x+=16){i32 n=*(i32*)(x+8);if(n>0)size+=(u32)n;}}cpu15DestroyOriginal(p);if(t){u64 q=0;cpuCounter(&q);cpu14_event(14,deferred,t,q,size);}}
"""
 if defer:
  helper=(r/'tests/cpu15_defer.inc').read_text()+'\n'+helper.replace('cpu15DestroyOriginal(p);','if(cpuStorageStreamingDepth&&cpu_detail_begin()){deferred=cpu15_defer_pixels(p);if(!deferred)cpu15Fallback++;}cpu15DestroyOriginal(p);')
 tex=tex.replace('static void cpu_texture_install(void){',helper+'static void cpu_texture_install(void){')
 tex=tex.replace(' cpu_texture_trial_install();',' const u8 cpu15sig[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x33,0xed};cpu_detail_hook(0x334e20,cpu15sig,sizeof(cpu15sig),(void*)cpu15_destroy,(void**)&cpu15DestroyOriginal);\n cpu_texture_trial_install();')
 if defer:tex=tex.replace(' cpu_texture_trial_install();',' cpu15_free_init();cpu_texture_trial_install();')
 if paired:
  assert defer
  tex=tex.replace(' cpu15_free_init();',' cpu15Alternating=1;cpu15_free_init();')
 if defer:assert tex.count('cpu15_free_init();')==1
 assert prof.count('#include "cpu_texture_profile.inc"')==1
 prof=prof.replace('#include "cpu_texture_profile.inc"',tex)
 if defer:s=s.replace('static void cpu14_save(void){','static void cpu14_save(void){ext_Log(">>> CPU15_FREE_SUMMARY queued %u completed %u fallback %u pending_bytes %llu freed_bytes %llu",cpu15Queued,__atomic_load_n(&cpu15Completed,__ATOMIC_RELAXED),cpu15Fallback,__atomic_load_n(&cpu15PendingBytes,__ATOMIC_RELAXED),__atomic_load_n(&cpu15FreedBytes,__ATOMIC_RELAXED));')
 return s,prof
