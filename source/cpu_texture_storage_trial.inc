#ifndef CPU_TEXTURE_STORAGE
#define CPU_TEXTURE_STORAGE 0
#endif
#ifndef CPU_TEXTURE_MIN_BYTES
#define CPU_TEXTURE_MIN_BYTES 2097152
#endif
#ifndef CPU_TEXTURE_LATC
#define CPU_TEXTURE_LATC 0
#endif

/* CPU4 streaming allocation optimization; enabled only by explicit build option.
   Buffer pointers live only until this synchronous bitmap callback returns. */
typedef void (__attribute__((ms_abi))*CPUCompressed)(u32,i32,u32,i32,i32,i32,i32,const void*);
typedef void (__attribute__((ms_abi))*CPUCompressedSub)(u32,i32,i32,i32,i32,i32,u32,i32,const void*);
typedef void (__attribute__((ms_abi))*CPUStorage)(u32,i32,u32,i32,i32);
typedef void (__attribute__((ms_abi))*CPUTexLevel)(u32,i32,u32,i32*);
typedef void* (__attribute__((ms_abi))*CPUContext)(void);
static CPUCompressed cpuTrialOriginal,cpuTrialShimPointer;
typedef void (__attribute__((ms_abi))*CPUBufferBind)(u32,u32);static CPUBufferBind cpuTrialBufferBind;
static CPUCompressedSub cpuTrialSub;static CPUStorage cpuTrialStorage;static CPUTexLevel cpuTrialLevel;static CPUContext cpuTrialContext;
typedef struct {u32 target,format; i32 level,w,h,border,bytes;const void*data;} CPUUpload;
static struct {u32 depth,count,texture,enabled,reject;void*context;CPUUpload upload[16];} cpuTrial;
static u32 cpuTrialMinBytes=CPU_TEXTURE_MIN_BYTES;
static u32 cpuTrialEnabled,cpuTrialAccepted,cpuTrialRejected,cpuTrialLatc;static void*cpuTrialApiContext;static void**cpuTrialExport;
static void cpu_trial_flush_native(void){
 CPUCompressed original=cpuTrialExport?(CPUCompressed)*cpuTrialExport:cpuTrialOriginal;
 i32 prior=0,unpack=0;ext_glGetIntegerv(0x8069,&prior);ext_glGetIntegerv(0x88ef,&unpack);if(unpack)cpuTrialBufferBind(0x88ec,0);ext_glBindTexture(0xde1,cpuTrial.texture);
 for(u32 i=0;i<cpuTrial.count;i++){CPUUpload*q=cpuTrial.upload+i;original(q->target,q->level,q->format,q->w,q->h,q->border,q->bytes,q->data);}ext_glBindTexture(0xde1,(u32)prior);if(unpack)cpuTrialBufferBind(0x88ec,(u32)unpack);cpuTrial.count=0;cpuTrial.reject=1;
}
static void __attribute__((ms_abi)) cpu_trial_upload(u32 target,i32 level,u32 format,i32 w,i32 h,i32 border,i32 bytes,const void*data){
 CPUCompressed original=cpuTrialExport?(CPUCompressed)*cpuTrialExport:cpuTrialOriginal;
 if(cpuThreadId&&cpuThreadId()==cpuMainThread&&cpuTrial.enabled&&!cpuTrial.reject){
  if(!cpuTrial.count&&level==0&&bytes<(i32)cpuTrialMinBytes){cpuTrial.reject=1;original(target,level,format,w,h,border,bytes,data);return;}
  i32 bound=0,unpack=0;ext_glGetIntegerv(0x8069,&bound);ext_glGetIntegerv(0x88ef,&unpack);
  if(target==0x0de1&&bound==(i32)cpuTrial.texture&&!unpack&&cpuTrial.count<16&&cpuTrialContext()==cpuTrial.context){CPUUpload*q=cpuTrial.upload+cpuTrial.count++;q->target=target;q->level=level;q->format=format;q->w=w;q->h=h;q->border=border;q->bytes=bytes;q->data=data;return;}
  cpu_trial_flush_native();
 }
 original(target,level,format,w,h,border,bytes,data);
}
static void cpu_texture_trial_begin(void*p,void*b,i32 index){
 if(!cpuTrialEnabled||!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 if(cpuTrial.depth++){if(cpuTrial.enabled)cpu_trial_flush_native();return;}
 cpuTrial.enabled=cpuTrial.count=cpuTrial.reject=0;
 if(!cpuStorageStreamingDepth||!p||!b||index<0||*(i32*)((u8*)p+0xac)!=1||*(i32*)((u8*)b+0x68)<2)return;
 u32*first=*(u32**)((u8*)p+0x120);u32*last=*(u32**)((u8*)p+0x128);if(!first||last<=first||index>=last-first)return;
 cpuTrial.texture=first[index];cpuTrial.context=cpuTrialContext();cpuTrial.enabled=cpuTrial.context!=0&&cpuTrial.context==cpuTrialApiContext;
}
static void cpu_texture_trial_end(void){
 if(!cpuTrialEnabled||!cpuThreadId||cpuThreadId()!=cpuMainThread||!cpuTrial.depth)return;
 if(--cpuTrial.depth)return;
 if(!cpuTrial.enabled)return;cpuTrial.enabled=0;
 u32 n=cpuTrial.count;if(!n)return;CPUUpload*q=cpuTrial.upload;
 i32 bound=0,unpack=0,oldWidth=0;ext_glGetIntegerv(0x8069,&bound);ext_glGetIntegerv(0x88ef,&unpack);
 i32 valid=n>0&&!cpuTrial.reject&&bound==(i32)cpuTrial.texture&&!unpack&&cpuTrialContext()==cpuTrial.context;
 if(valid){cpuTrialLevel(0xde1,0,0x1000,&oldWidth);valid=oldWidth==0;}
 u32 block=0;
 if(n){u32 fmt=q[0].format;if(fmt==0x83f0||fmt==0x83f1||fmt==0x8c4c||fmt==0x8c4d||fmt==0x8dbb||fmt==0x8dbc)block=8;else if((cpuTrialLatc&&fmt==0x8c72)||fmt==0x83f2||fmt==0x83f3||fmt==0x8c4e||fmt==0x8c4f||fmt==0x8dbd||fmt==0x8dbe||(fmt>=0x8e8c&&fmt<=0x8e8f))block=16;}
 if(!block||!n||q[0].w<1||q[0].h<1)valid=0;
 if(valid){u32 max=1;for(i32 dim=q[0].w>q[0].h?q[0].w:q[0].h;dim>1;dim>>=1)max++;if(n>max)valid=0;}
 for(u32 i=0;i<n&&valid;i++){i32 w=q[0].w>>i,h=q[0].h>>i;if(w<1)w=1;if(h<1)h=1;u64 bytes=(u64)((w+3)/4)*((h+3)/4)*block;
  if(q[i].level!=(i32)i||q[i].target!=0xde1||q[i].format!=q[0].format||q[i].w!=w||q[i].h!=h||q[i].border||!q[i].data||q[i].bytes<=0||bytes!=(u32)q[i].bytes||w>16384||h>16384)valid=0;
 }
 if(valid){cpuTrialStorage(0xde1,n,q[0].format,q[0].w,q[0].h);for(u32 i=0;i<n;i++)cpuTrialSub(0xde1,q[i].level,0,0,q[i].w,q[i].h,q[i].format,q[i].bytes,q[i].data);cpuTrialAccepted++;}
 else{cpu_trial_flush_native();if(n)cpuTrialRejected++;}
 if(CPU_WORK_PROFILE&&(cpuTrialAccepted+cpuTrialRejected)<=12&&n)ext_Log(">>> CPU4_STORAGE decision %s levels %u first %dx%d accepted %u rejected %u format %x level %d oldWidth %d bound %d texture %u reject %u",valid?"immutable":"native",n,q[0].w,q[0].h,cpuTrialAccepted,cpuTrialRejected,q[0].format,q[0].level,oldWidth,bound,cpuTrial.texture,cpuTrial.reject);
 cpuTrial.count=0;
}
static void cpu_texture_trial_install(void){
 if(!CPU_WORK_PROFILE&&!CPU_TEXTURE_STORAGE)return;
 i32 requestLatc=CPU_TEXTURE_LATC;
 if(CPU_WORK_PROFILE){void*f=ext_fopen("cpu4_texture_storage_trial.txt","rb");if(!f)return;char on=0;ext_fread(&on,1,1,f);ext_fclose(f);if(on!='1'&&on!='2'&&on!='3')return;requestLatc=on=='2'||on=='3';cpuTrialMinBytes=on=='3'?65536u:2097152u;}
 void*ogl=ext_GetModuleHandleA("opengl32.dll");void*glew=ext_GetModuleHandleA("glew32.dll");if(!ogl||!glew)return;
 void*(__attribute__((ms_abi))*get)(const char*)=(void*)ext_GetProcAddress(ogl,"wglGetProcAddress");if(!get)return;
 cpuTrialBufferBind=(void*)get("glBindBuffer");cpuTrialStorage=(void*)get("glTexStorage2D");cpuTrialSub=(void*)get("glCompressedTexSubImage2D");cpuTrialLevel=(void*)ext_GetProcAddress(ogl,"glGetTexLevelParameteriv");cpuTrialContext=(void*)ext_GetProcAddress(ogl,"wglGetCurrentContext");
 void**exported=(void*)ext_GetProcAddress(glew,"__glewCompressedTexImage2D");void***slot=(void*)((u8*)ext_GetModuleHandleA(0)+0x686780);
 if(!cpuTrialBufferBind||!cpuTrialStorage||!cpuTrialSub||!cpuTrialLevel||!cpuTrialContext||!exported||*slot!=exported||!*exported){ext_Log(">>> CPU4_STORAGE API/import guard rejected");return;}
 // Query once in this GL context; no format conversion or per-upload capability query.
 // GL4.3 includes ARB_internalformat_query2 (0x826f INTERNALFORMAT_SUPPORTED).
 if(requestLatc){
  i32 major=0,minor=0;ext_glGetIntegerv(0x821b,&major);ext_glGetIntegerv(0x821c,&minor);
  void(__attribute__((ms_abi))*query)(u32,u32,u32,i32,i32*)=(void*)get("glGetInternalformativ");
  const char*(__attribute__((ms_abi))*stringi)(u32,u32)=(void*)get("glGetStringi");
  if((major>4||(major==4&&minor>=3))&&(u64)query>3&&(u64)query!=(u64)-1&&(u64)stringi>3&&(u64)stringi!=(u64)-1){
   i32 count=0,hasLatc=0;ext_glGetIntegerv(0x821d,&count);
   for(i32 i=0;i<count&&i<4096&&!hasLatc;i++){const char*name=stringi(0x1f03,i);const char*expected="GL_EXT_texture_compression_latc";u32 j=0;if(name){while(expected[j]&&name[j]==expected[j])j++;hasLatc=!expected[j]&&!name[j];}}
   if(hasLatc){i32 supported=0;query(0xde1,0x8c72,0x826f,1,&supported);cpuTrialLatc=supported==1;}
  }
 }
 i32(__attribute__((ms_abi))*protect)(void*,u64,u32,u32*)=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"VirtualProtect");u32 old=0,unused=0;if(!protect||!protect(slot,8,4,&old))return;
 cpuTrialExport=exported;cpuTrialApiContext=cpuTrialContext();cpuTrialOriginal=(void*)*exported;cpuTrialShimPointer=cpu_trial_upload;*slot=(void**)&cpuTrialShimPointer;protect(slot,8,old,&unused);cpuTrialEnabled=1;if(CPU_WORK_PROFILE)ext_Log(">>> CPU8_STORAGE_POLICY minimum_base_bytes %u",cpuTrialMinBytes);ext_Log(">>> TEXTURE STORAGE: compressed 2D allocation reuse enabled; native fallback retained, exact LATC2 %u",cpuTrialLatc);
}

static void __attribute__((ms_abi)) cpu_storage_manager_call(void*p,float dt){
 if(cpuThreadId&&cpuThreadId()==cpuMainThread){cpuStorageStreamingDepth++;cpuTextureOriginal(p,dt);cpuStorageStreamingDepth--;}else cpuTextureOriginal(p,dt);
}
static u64 __attribute__((ms_abi)) cpu_storage_bitmap_call(void*p,void*b,i32 index){
 cpu_texture_trial_begin(p,b,index);u64 result=cpuBitmapOriginal(p,b,index);cpu_texture_trial_end();return result;
}
#include "cpu_texture_release.inc"
static void cpu_texture_production_install(void){
 if(!CPU_TEXTURE_STORAGE||CPU_WORK_PROFILE)return;static i32 attempted;if(attempted)return;
 void*ogl=ext_GetModuleHandleA("opengl32.dll");if(!ogl)return;CPUContext context=(void*)ext_GetProcAddress(ogl,"wglGetCurrentContext");if(!context||!context())return;
 attempted=1;cpuThreadId=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"GetCurrentThreadId");if(!cpuThreadId)return;cpuMainThread=cpuThreadId();
 u8*t=(u8*)ext_GetModuleHandleA(0)+0x569cf0;const u8 sig[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c};for(u32 i=0;i<sizeof(sig);i++)if(t[i]!=sig[i]){ext_Log(">>> TEXTURE STORAGE: unsupported bitmap function; native retained");return;}
 u8*manager=(u8*)ext_GetModuleHandleA(0)+0x2df7e0;const u8 managerSig[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x56,0x48,0x83,0xec,0x40};for(u32 i=0;i<sizeof(managerSig);i++)if(manager[i]!=managerSig[i])return;
 if(ext_MH_CreateHook(manager,(void*)cpu_storage_manager_call,(void**)&cpuTextureOriginal))return;
 i32 create=ext_MH_CreateHook(t,(void*)cpu_storage_bitmap_call,(void**)&cpuBitmapOriginal);if(create)return;
 i32 enabled=ext_MH_EnableHook(t);if(enabled||ext_MH_EnableHook(manager))return;cpu_texture_trial_install();cpu_texture_release_install();
}
