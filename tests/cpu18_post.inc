/* Private Theta post-update attribution; exact pass-through, no scheduling change. */
static void cpu18_post_end(u32 stage,u64 t){if(t){u64 end=0;cpuCounter(&end);cpu14_event(21,stage,t,end,0);}}
static void (__attribute__((ms_abi))*cpu18VariableOriginal)(void*,float);
static void __attribute__((ms_abi)) cpu18_variable(void*p,float dt){u64 t=cpu_detail_begin();cpu18VariableOriginal(p,dt);cpu18_post_end(0,t);}
static void (__attribute__((ms_abi))*cpu18QueueOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_queue(void*p){u64 t=cpu_detail_begin();cpu18QueueOriginal(p);cpu18_post_end(1,t);}
static void (__attribute__((ms_abi))*cpu18PackOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_pack(void*p){u64 t=cpu_detail_begin();cpu18PackOriginal(p);cpu18_post_end(2,t);}
static void (__attribute__((ms_abi))*cpu18_clearOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_clear(void*p){u64 t=cpu_detail_begin();cpu18_clearOriginal(p);cpu18_post_end(3,t);}
static void (__attribute__((ms_abi))*cpu18_destroyOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_destroy(void*p){u64 t=cpu_detail_begin();cpu18_destroyOriginal(p);cpu18_post_end(4,t);}
static u64 (__attribute__((ms_abi))*cpu18_streamOriginal)(void*,u64);
static u64 __attribute__((ms_abi)) cpu18_stream(void*p,u64 arg){u64 t=cpu_detail_begin();u64 result=cpu18_streamOriginal(p,arg);cpu18_post_end(5,t);return result;}
static void (__attribute__((ms_abi))*cpu18_finishOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_finish(void*p){u64 t=cpu_detail_begin();cpu18_finishOriginal(p);cpu18_post_end(6,t);}
static void (__attribute__((ms_abi))*cpu18PreloadOriginal)(void*,u64);
static void __attribute__((ms_abi)) cpu18_preload(void*p,u64 arg){u64 t=cpu_detail_begin();cpu18PreloadOriginal(p,arg);cpu18_post_end(7,t);}
static void (__attribute__((ms_abi))*cpu18UpdateOriginal)(void*,u64,u64);
static void __attribute__((ms_abi)) cpu18_update(void*p,u64 arg,u64 budget){u64 t=cpu_detail_begin();u32 before=t?*(u32*)((u8*)p+0x54):0;if(t&&before==26){u8*q=p;cpu14_event(24,(u32)*(u64*)(q+0x58),t,t,(*(u64*)(q+0x130)-*(u64*)(q+0x128))/0x30);for(u32 i=0;i<2;i++){void*o=*(void**)(q+0xa8+i*8);if(o)cpu14_event(25,i,t,t,*(u64*)o-(u64)ext_GetModuleHandleA(0));}}cpu18UpdateOriginal(p,arg,budget);if(t){u64 end=0;cpuCounter(&end);cpu14_event(23,before,t,end,*(u32*)((u8*)p+0x54));}}
static void (__attribute__((ms_abi))*cpu18_lookupOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_lookup(void*p){u64 t=cpu_detail_begin();cpu18_lookupOriginal(p);cpu18_post_end(8,t);}
static void (__attribute__((ms_abi))*cpu18_listOriginal)(void*);
static void __attribute__((ms_abi)) cpu18_list(void*p){u64 t=cpu_detail_begin();cpu18_listOriginal(p);cpu18_post_end(9,t);}
static void* (__attribute__((ms_abi))*cpu18_xmlOriginal)(void*,u32 flags);
static void* __attribute__((ms_abi)) cpu18_xml(void*p,u32 flags){u64 t=cpu_detail_begin();void*result=cpu18_xmlOriginal(p,flags);cpu18_post_end(10,t);return result;}
static void cpu18_post_install(void){
const u8 sig_lookup[]={0x40,0x53,0x48,0x83,0xec,0x60,0x48,0x8b,0x51,0x08,0x48,0x8b,0xd9,0x48,0x8b,0x52};cpu_detail_hook(0x467d30,sig_lookup,sizeof(sig_lookup),(void*)cpu18_lookup,(void**)&cpu18_lookupOriginal);
const u8 sig_list[]={0x40,0x53,0x48,0x83,0xec,0x40,0x48,0x8b,0xd9,0xe8,0xd2,0xa7,0xff,0xff,0x4c,0x8d};cpu_detail_hook(0x467770,sig_list,sizeof(sig_list),(void*)cpu18_list,(void**)&cpu18_listOriginal);
const u8 sig_xml[]={0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x8b,0xda,0x48,0x8b,0xf9,0xe8};cpu_detail_hook(0x23d4d0,sig_xml,sizeof(sig_xml),(void*)cpu18_xml,(void**)&cpu18_xmlOriginal);
 const u8 p[]={0x48,0x8b,0xc4,0x57,0x48,0x81,0xec,0x90,0,0,0,0x48,0xc7,0x44,0x24,0x28};
 const u8 u[]={0x40,0x53,0x56,0x48,0x83,0xec,0x28,0x48,0x83,0xb9,0xc8,0x01,0,0,0,0x0f};
 cpu_detail_hook(0x12dc20,p,sizeof(p),(void*)cpu18_preload,(void**)&cpu18PreloadOriginal);
 cpu_detail_hook(0x46b410,u,sizeof(u),(void*)cpu18_update,(void**)&cpu18UpdateOriginal);
const u8 sig_clear[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};cpu_detail_hook(0x104350,sig_clear,sizeof(sig_clear),(void*)cpu18_clear,(void**)&cpu18_clearOriginal);
const u8 sig_destroy[]={0x48,0x89,0x4c,0x24,0x08,0x57,0x48,0x83,0xec,0x30,0x48,0xc7,0x44,0x24,0x20,0xfe};cpu_detail_hook(0x1053b0,sig_destroy,sizeof(sig_destroy),(void*)cpu18_destroy,(void**)&cpu18_destroyOriginal);
const u8 sig_stream[]={0x40,0x57,0x48,0x83,0xec,0x20,0x48,0x83,0xb9,0xf8,0x06,0x00,0x00,0x00,0x48,0x8b};cpu_detail_hook(0x12f1a0,sig_stream,sizeof(sig_stream),(void*)cpu18_stream,(void**)&cpu18_streamOriginal);
const u8 sig_finish[]={0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x48,0x8b,0x89,0xf8,0x06,0x00,0x00};cpu_detail_hook(0x12f2a0,sig_finish,sizeof(sig_finish),(void*)cpu18_finish,(void**)&cpu18_finishOriginal);
 const u8 a[]={0x4c,0x8b,0xdc,0x57,0x48,0x83,0xec,0x70,0x48,0xc7,0x44,0x24,0x20,0xfe,0xff,0xff};
 const u8 b[]={0x48,0x8b,0xc4,0x55,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x8d,0x68,0xa1};
 const u8 c[]={0x48,0x89,0x5c,0x24,0x20,0x48,0x89,0x4c,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41};
 cpu_detail_hook(0x12d390,a,sizeof(a),(void*)cpu18_variable,(void**)&cpu18VariableOriginal);
 cpu_detail_hook(0x132720,b,sizeof(b),(void*)cpu18_queue,(void**)&cpu18QueueOriginal);
 cpu_detail_hook(0x29fcc0,c,sizeof(c),(void*)cpu18_pack,(void**)&cpu18PackOriginal);
 ext_Log(">>> CPU18 post observers %u %u %u",cpu18VariableOriginal!=0,cpu18QueueOriginal!=0,cpu18PackOriginal!=0);
}
