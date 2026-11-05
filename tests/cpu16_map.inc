static i32 h5748n_copy_tstring(void*,char*,u32);
static u64 cpu16Calls[5],cpu16Ticks[5];
static void (__attribute__((ms_abi))*cpu16_map_original)(void*p,float dt);
static void __attribute__((ms_abi)) cpu16_map(void*p,float dt){u64 t=cpu_detail_begin(),vt=t&&p?*(u64*)p-(u64)ext_GetModuleHandleA(0):0;cpu16_map_original(p,dt);if(t){u64 end=0;cpuCounter(&end);cpu16Calls[0]++;cpu16Ticks[0]+=end-t;cpu14_event(15,0,t,end,vt);}}
static void (__attribute__((ms_abi))*cpu16_transient_original)(void*p,float dt);
static void __attribute__((ms_abi)) cpu16_transient(void*p,float dt){u64 t=cpu_detail_begin(),vt=t&&p?*(u64*)p-(u64)ext_GetModuleHandleA(0):0;cpu16_transient_original(p,dt);if(t){u64 end=0;cpuCounter(&end);cpu16Calls[1]++;cpu16Ticks[1]+=end-t;cpu14_event(15,1,t,end,vt);}}
static void (__attribute__((ms_abi))*cpu16_timer_original)(void*p,float dt);
static void __attribute__((ms_abi)) cpu16_timer(void*p,float dt){u64 t=cpu_detail_begin(),vt=t&&p?*(u64*)p-(u64)ext_GetModuleHandleA(0):0;cpu16_timer_original(p,dt);if(t){u64 end=0;cpuCounter(&end);cpu16Calls[2]++;cpu16Ticks[2]+=end-t;cpu14_event(15,2,t,end,vt);}}
static void (__attribute__((ms_abi))*cpu16_entity_original)(void*p,float dt);
static void __attribute__((ms_abi)) cpu16_entity(void*p,float dt){u64 t=cpu_detail_begin(),vt=t&&p?*(u64*)p-(u64)ext_GetModuleHandleA(0):0;char name[96];name[0]=0;if(t&&(cpu13Phase==99||cpu13Phase==0)&&vt==0x6c8038)h5748n_copy_tstring((u8*)p+0x120,name,sizeof(name));cpu16_entity_original(p,dt);if(t){u64 end=0;cpuCounter(&end);cpu16Calls[3]++;cpu16Ticks[3]+=end-t;cpu14_event(15,3,t,end,vt);if(end-t>cpuFreq/100)ext_Log(">>> CPU16_SLOW_ENTITY name %s phase %u ms %.6f",name,cpu13Phase,1000.0*(end-t)/cpuFreq);}}
static u64 (__attribute__((ms_abi))*cpu16_script_original)(void*p);
static u64 __attribute__((ms_abi)) cpu16_script(void*p){u64 t=cpu_detail_begin(),vt=t&&p?*(u64*)p-(u64)ext_GetModuleHandleA(0):0;u64 result=cpu16_script_original(p);if(t){u64 end=0;cpuCounter(&end);cpu16Calls[4]++;cpu16Ticks[4]+=end-t;cpu14_event(15,4,t,end,vt);}return result;}
static void cpu16_install(void){
const u8 s0[]={0x48,0x8b,0xc4,0x57,0x48,0x83,0xec,0x70,0x48,0xc7,0x44,0x24,0x28,0xfe,0xff,0xff};cpu_detail_hook(0x12fcf0,s0,sizeof(s0),(void*)cpu16_map,(void**)&cpu16_map_original);
const u8 s1[]={0x48,0x89,0x5c,0x24,0x18,0x55,0x48,0x83,0xec,0x40,0x48,0x8b,0x81,0x80,0x06,0x00};cpu_detail_hook(0x12ad00,s1,sizeof(s1),(void*)cpu16_transient,(void**)&cpu16_transient_original);
const u8 s2[]={0x48,0x8b,0xc4,0x57,0x41,0x54,0x41,0x55,0x48,0x81,0xec,0x90,0x00,0x00,0x00,0x48};cpu_detail_hook(0x12f5c0,s2,sizeof(s2),(void*)cpu16_timer,(void**)&cpu16_timer_original);
const u8 s3[]={0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x30,0x33,0xff,0x0f,0x29,0x74,0x24};cpu_detail_hook(0xc0200,s3,sizeof(s3),(void*)cpu16_entity,(void**)&cpu16_entity_original);
const u8 s4[]={0x40,0x53,0x57,0x48,0x83,0xec,0x28,0x48,0x83,0xb9,0xe8,0x00,0x00,0x00,0x00,0x48};cpu_detail_hook(0x1e2ea0,s4,sizeof(s4),(void*)cpu16_script,(void**)&cpu16_script_original);
}
