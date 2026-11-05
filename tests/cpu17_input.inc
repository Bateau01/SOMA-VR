/* Private input attribution. Originals retain every call and argument. */
static void cpu17_input_end(u32 stage,u64 start){if(start){u64 end=0;cpuCounter(&end);cpu14_event(17,stage,start,end,0);}}
#define CPU17_INPUT(name,stage) \
static void (__attribute__((ms_abi))*name##Original)(void*); \
static void __attribute__((ms_abi)) name(void*p){u64 t=cpu_detail_begin();name##Original(p);cpu17_input_end(stage,t);}
CPU17_INPUT(cpu17_begin,0)
CPU17_INPUT(cpu17_finish,1)
CPU17_INPUT(cpu17_poll,2)
CPU17_INPUT(cpu17_devices,3)
static void (__attribute__((ms_abi))*cpu17ActionsOriginal)(void*,float);
static void __attribute__((ms_abi)) cpu17_actions(void*p,float dt){u64 t=cpu_detail_begin();cpu17ActionsOriginal(p,dt);cpu17_input_end(4,t);}
static void cpu17_input_install(void){
 const u8 a[]={0x40,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x41,0x08,0x48,0x8b,0xf9,0x48,0x89,0x5c};
 const u8 b[]={0x40,0x57,0x48,0x83,0xec,0x20,0x80,0x79,0x3c,0,0x48,0x8b,0xf9,0x74,0x61,0x48};
 const u8 c[]={0x40,0x53,0x48,0x83,0xec,0x60,0x48,0x8b,0xd9,0x48,0x8d,0x4c,0x24,0x20,0xe8,0x55};
 const u8 d[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57};
 const u8 e[]={0x48,0x89,0x5c,0x24,0x10,0x56,0x48,0x83,0xec,0x30,0x48,0x8b,0x41,0x40,0x0f,0x29};
 cpu_detail_hook(0x43b8a0,a,sizeof(a),(void*)cpu17_begin,(void**)&cpu17_beginOriginal);
 cpu_detail_hook(0x43bf60,b,sizeof(b),(void*)cpu17_finish,(void**)&cpu17_finishOriginal);
 cpu_detail_hook(0x43aff0,c,sizeof(c),(void*)cpu17_poll,(void**)&cpu17_pollOriginal);
 cpu_detail_hook(0x2c4c30,d,sizeof(d),(void*)cpu17_devices,(void**)&cpu17_devicesOriginal);
 cpu_detail_hook(0x2c4250,e,sizeof(e),(void*)cpu17_actions,(void**)&cpu17ActionsOriginal);
 ext_Log(">>> CPU17 input observers %u %u %u %u %u",cpu17_beginOriginal!=0,cpu17_finishOriginal!=0,cpu17_pollOriginal!=0,cpu17_devicesOriginal!=0,cpu17ActionsOriginal!=0);
}
