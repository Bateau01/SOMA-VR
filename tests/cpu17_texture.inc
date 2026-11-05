/* Private attribution: original GL calls, arguments and context preserved. */
static u32 cpu17RetireDepth;
static void (__attribute__((ms_abi))*cpu17DeleteOriginal)(i32,const u32*);
static void (__attribute__((ms_abi))*cpu17StorageOriginal)(u32,i32,u32,i32,i32);
static void (__attribute__((ms_abi))*cpu17SubOriginal)(u32,i32,i32,i32,i32,i32,u32,i32,const void*);
static void (__attribute__((ms_abi))*cpu17ChildrenOriginal)(void*);
static void cpu17_end(u32 kind,u64 start,u64 value){if(start){u64 end=0;cpuCounter(&end);cpu14_event(16,kind,start,end,value);}}
static void __attribute__((ms_abi)) cpu17_delete(i32 n,const u32*ids){u64 t=cpu17RetireDepth?cpu_detail_begin():0;cpu17DeleteOriginal(n,ids);cpu17_end(0,t,(u32)n);}
static void __attribute__((ms_abi)) cpu17_storage(u32 target,i32 n,u32 fmt,i32 w,i32 h){u64 t=cpu_detail_begin();cpu17StorageOriginal(target,n,fmt,w,h);cpu17_end(1,t,((u64)(u32)w<<32)|(u32)h);}
static void __attribute__((ms_abi)) cpu17_sub(u32 target,i32 level,i32 x,i32 y,i32 w,i32 h,u32 fmt,i32 bytes,const void*data){u64 t=cpu_detail_begin();cpu17SubOriginal(target,level,x,y,w,h,fmt,bytes,data);cpu17_end(2,t,(u32)bytes);}
static void __attribute__((ms_abi)) cpu17_children(void*p){u64 t=cpu17RetireDepth?cpu_detail_begin():0;cpu17ChildrenOriginal(p);cpu17_end(3,t,0);}
static void cpu17_install(void){
 u8*b=ext_GetModuleHandleA(0);u8*t=b+0x56a820;
 const u8 signature[]={0x48,0x89,0x5c,0x24,0x10,0x56,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0x28,0x01,0,0,0x33};
 for(u32 i=0;i<sizeof(signature);i++)if(t[i]!=signature[i])return;
 void*ogl=ext_GetModuleHandleA("opengl32.dll");void*expected=ext_GetProcAddress(ogl,"glDeleteTextures");
 void**slot=0;for(u32 i=0;i<80;i++)if(t[i]==0xff&&t[i+1]==0x15){slot=(void**)(t+i+6+*(i32*)(t+i+2));break;}
 if(!slot||*slot!=expected||!expected){ext_Log(">>> CPU17 import rejected");return;}
 i32(__attribute__((ms_abi))*protect)(void*,u64,u32,u32*)=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"VirtualProtect");
 u32 old=0,unused=0;if(!protect||!protect(slot,8,4,&old))return;
 cpu17DeleteOriginal=(void*)*slot;*slot=(void*)cpu17_delete;protect(slot,8,old,&unused);
 const u8 childSig[]={0x40,0x56,0x48,0x83,0xec,0x40,0x48,0x89,0x5c,0x24,0x50,0x48,0x8b,0x19,0x48,0x8b};cpu_detail_hook(0x2f6460,childSig,sizeof(childSig),(void*)cpu17_children,(void**)&cpu17ChildrenOriginal);
 ext_Log(">>> CPU17 texture retirement observer ready");
}
