/* Dedicated writer owns no engine pointers. Hook only after MinHook initialization. */
static void s26ji_logging_install(void){
 typedef u32 (__attribute__((ms_abi))*Name)(void*,unsigned short*,u32);
 typedef void* (__attribute__((ms_abi))*Load)(const unsigned short*,void*,u32);
 typedef i32 (__attribute__((ms_abi))*Start)(const unsigned short*);
 typedef void (__attribute__((ms_abi))*Activate)(void);
 typedef i32 (__attribute__((ms_abi))*Stop)(void);
 const u8 expected[]={0x56,0x53,0x48,0x83,0xec,0x38,0x48,0x8d,0x35};
 for(u32 i=0;i<sizeof(expected);i++)if(((const u8*)(void*)ext_Log)[i]!=expected[i])return;
 void*k=ext_GetModuleHandleA("kernel32.dll");
 Name name=(Name)ext_GetProcAddress(k,"GetModuleFileNameW");Load load=(Load)ext_GetProcAddress(k,"LoadLibraryExW");
 if(!name||!load)return;
 unsigned short path[1024],directory[1024];u32 n=name(p2_base(),path,1024);if(!n||n>=1000)return;
 i32 cut=-1;for(u32 i=0;i<n;i++)if(path[i]=='\\'||path[i]=='/')cut=(i32)i;
 if(cut<0)return;for(i32 i=0;i<cut;i++)directory[i]=path[i];directory[cut]=0;
 const char tail[]="SOMA-VR-Logging.dll";for(u32 i=0;i<sizeof(tail);i++)path[cut+1+(i32)i]=(unsigned short)tail[i];
 void*dll=load(path,0,8u);if(!dll){ext_Log("SOMA VR async logger unavailable; legacy logging retained");return;}
 Start start=(Start)ext_GetProcAddress(dll,"SomaVrLogStart");Activate activate=(Activate)ext_GetProcAddress(dll,"SomaVrLogActivate");
 void*logger=ext_GetProcAddress(dll,"SomaVrLog");Stop stop=(Stop)ext_GetProcAddress(dll,"SomaVrLogStop");
 if(!start||!activate||!logger||!stop||!start(directory))return;
 void*original=0;i32 cr=ext_MH_CreateHook((void*)ext_Log,logger,&original);i32 er=cr?cr:ext_MH_EnableHook((void*)ext_Log);
 if(cr||er){stop();ext_Log("SOMA VR async logger hook failed %d/%d; legacy retained",cr,er);return;}
 activate();ext_Log("SOMA VR async logging active: rotating 4 MiB segments; three previous segments; bounded nonblocking producer queue");
}
