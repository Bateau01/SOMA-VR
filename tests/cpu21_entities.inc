/* Private attribution: native entity/area creation, no scheduling changes. */
static i32 h5748n_copy_tstring(void*,char*,u32);
static void (__attribute__((ms_abi))*cpu21EntityOriginal)(u64,u64,u64,u64,u64,u64,u64,u64,u64,u64,u64);
static void (__attribute__((ms_abi))*cpu21AreaOriginal)(u64,u64,u64,u64,u64,u64,u64,u64,u64,u64);
static u32 cpu21Logs;
static u64 (__attribute__((ms_abi))*cpu21ConvertOriginal)(u64);
static u64 __attribute__((ms_abi)) cpu21_convert(u64 world){
 u64 t=cpu_detail_begin();u64 result=cpu21ConvertOriginal(world);
 if(t){u64 end=0;cpuCounter(&end);cpu14_event(27,2,t,end,0);if(cpu21Logs<24){cpu21Logs++;ext_Log(">>> CPU21_CONTAINER_CONVERT frame %u ms %.4f",g_frameCounter,1000.0*(end-t)/cpuFreq);}}
 return result;
}
static void cpu21_end(u32 kind,u64 t,u64 name){
 if(!t)return;u64 end=0;cpuCounter(&end);cpu14_event(27,kind,t,end,0);
 if(end-t>cpuFreq/500&&cpu21Logs<24){char label[192];label[0]=0;h5748n_copy_tstring((void*)name,label,sizeof(label));cpu21Logs++;ext_Log(">>> CPU21_SLOW kind %u frame %u ms %.4f name %s",kind,g_frameCounter,1000.0*(end-t)/cpuFreq,label);}
}
static void __attribute__((ms_abi)) cpu21_entity(u64 a,u64 b,u64 c,u64 d,u64 e,u64 f,u64 g,u64 h,u64 i,u64 j,u64 k){
 u64 t=cpu_detail_begin();cpu21EntityOriginal(a,b,c,d,e,f,g,h,i,j,k);cpu21_end(0,t,c);
}
static void __attribute__((ms_abi)) cpu21_area(u64 a,u64 b,u64 c,u64 d,u64 e,u64 f,u64 g,u64 h,u64 i,u64 j){
 u64 t=cpu_detail_begin();cpu21AreaOriginal(a,b,c,d,e,f,g,h,i,j);cpu21_end(1,t,c);
}
static void cpu21_install(void){
 const u8 a[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x48,0x89,0x7c,0x24,0x18,0x4c};
 const u8 b[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x48,0x89,0x7c,0x24,0x18,0x55};
 cpu_detail_hook(0x47f050,a,sizeof(a),(void*)cpu21_entity,(void**)&cpu21EntityOriginal);
 cpu_detail_hook(0x46fdc0,b,sizeof(b),(void*)cpu21_area,(void**)&cpu21AreaOriginal);
 const u8 c[]={0x4c,0x8b,0xdc,0x41,0x56,0x48,0x83,0xec,0x50,0x48,0x8b,0x81,0x80,0x01,0x00,0x00};
 cpu_detail_hook(0x24f2c0,c,sizeof(c),(void*)cpu21_convert,(void**)&cpu21ConvertOriginal);
 ext_Log(">>> CPU21_ENTITY_OBSERVERS %u %u",cpu21EntityOriginal!=0,cpu21AreaOriginal!=0);
 ext_Log(">>> CPU21_CONTAINER_OBSERVER %u",cpu21ConvertOriginal!=0);
}
