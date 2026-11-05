/* Private CPU23 attribution plus explicitly opted-in CPU24 experiment. Live scope only. */
static u32 cpu23BufferLogs,cpu23Eligible;static void*cpu24Expected,*cpu24Object;
static void cpu23_install(void);
static void cpu23_buffer_snapshot(void* loader){
 cpu24Expected=0;cpu23Eligible=0;u64 t=cpu_detail_begin();if(!t||!loader)return;cpu23_install();
 u8*p=loader;if(*(u32*)(p+0x54)!=6)return;
 u64 begin=*(u64*)(p+0x380),end=*(u64*)(p+0x388),index=*(u64*)(p+0x58);
 if(!begin||end<begin||index>=(end-begin)/8)return;
 u64 object=((u64*)begin)[index];if(!object)return;
 cpu24Expected=(void*)object;cpu23Eligible=1;u64 vt=*(u64*)object,base=(u64)ext_GetModuleHandleA(0),target=*(u64*)(vt+0x68);
 cpu14_event(28,(u32)index,t,t,target-base);
 if(cpu23BufferLogs<4){cpu23BufferLogs++;ext_Log(">>> CPU23_BUFFER index %llu count %llu vtable_rva %llx finalize_rva %llx",index,(end-begin)/8,vt-base,target-base);}
}

static u32 cpu23Scope,cpu23Ready,cpu23UploadLogs;
static void (__attribute__((ms_abi))*cpu23UploadOriginal)(void*);
static void* (__attribute__((ms_abi))*cpu23MapOriginal)(u32,u32);
static u8 (__attribute__((ms_abi))*cpu23UnmapOriginal)(u32);
static void (__attribute__((ms_abi))*cpu23DataOriginal)(u32,i64,const void*,u32);
#ifndef CPU23_STAGING
#define CPU23_STAGING 0
#endif
#ifndef CPU24_PACK
#define CPU24_PACK 0
#endif
static i32 cpu24_native_pack(void*,u64);static void cpu24_verify_gpu(u32,u8);
static void*cpu23Scratch,*cpu23Mapped;static u64 cpu23Bytes;static u32 cpu23CanStage;
static void* (__attribute__((ms_abi))*cpu23Copy)(void*,const void*,u64);
static u64 cpu23_start(void){return cpu23Scope?cpu_detail_begin():0;}
static void cpu23_end(u32 kind,u64 t,u64 value){if(t){u64 e=0;cpuCounter(&e);cpu14_event(29,kind,t,e,value);}}
static void* __attribute__((ms_abi)) cpu23_map(u32 a,u32 b){u64 t=cpu23_start();void*r=cpu23MapOriginal(a,b);cpu23_end(1,t,a);if(CPU24_PACK&&t&&cpu23Scope==1&&cpu24Object==cpu24Expected&&cpu24Object&&a==0x8892&&b==0x88b9&&r&&cpu23Bytes>=65536&&cpu23Bytes<=67108864&&cpu24_native_pack(r,cpu23Bytes)){cpu14_event(31,0,t,t,cpu23Bytes);return 0;}
 if(CPU23_STAGING&&t&&cpu23CanStage&&a==0x8892&&b==0x88b9&&r&&cpu23Bytes>=65536&&cpu23Bytes<=67108864&&!cpu23Scratch&&cpu23Copy){void*s=ext_malloc(cpu23Bytes);if(s){cpu23Scratch=s;cpu23Mapped=r;cpu14_event(30,0,t,t,cpu23Bytes);return s;}}
 return r;}
static u8 __attribute__((ms_abi)) cpu23_unmap(u32 a){u64 t=cpu23_start();if(t&&a==0x8892&&cpu23Scratch){cpu23Copy(cpu23Mapped,cpu23Scratch,cpu23Bytes);ext_free(cpu23Scratch);cpu23Scratch=cpu23Mapped=0;}u8 r=cpu23UnmapOriginal(a);if(CPU24_PACK&&t)cpu24_verify_gpu(a,r);cpu23_end(2,t,a);return r;}
static void __attribute__((ms_abi)) cpu23_data(u32 a,i64 b,const void*c,u32 d){u64 t=cpu23_start();if(t&&a==0x8892&&!c)cpu23Bytes=b>0?(u64)b:0;cpu23DataOriginal(a,b,c,d);cpu23_end(3,t,b);}
static void __attribute__((ms_abi)) cpu23_upload(void*p){
 u64 t=cpu_detail_begin();if(t){cpu23Scope++;cpu23CanStage=cpu23Eligible&&((u8*)p)[0xed]&&cpu23Scope==1;cpu23Bytes=0;cpu24Object=p;}
 cpu23UploadOriginal(p);
 if(t){cpu24Object=0;cpu23CanStage=0;cpu23Scope--;cpu23_end(0,t,((u8*)p)[0xed]);if(cpu23UploadLogs<12){cpu23UploadLogs++;ext_Log(">>> CPU23_UPLOAD interleaved %u arrays %llu",((u8*)p)[0xed],(*(u64*)((u8*)p+0x90)-*(u64*)((u8*)p+0x88))/8);}}
}
static void cpu23_install(void){
 if(cpu23Ready)return;cpu23Ready=1;cpu23Copy=(void*)ext_GetProcAddress(ext_GetModuleHandleA("msvcrt.dll"),"memcpy");
 void*g=ext_GetModuleHandleA("glew32.dll");
 void**m=(void**)ext_GetProcAddress(g,"__glewMapBuffer"),**u=(void**)ext_GetProcAddress(g,"__glewUnmapBuffer"),**d=(void**)ext_GetProcAddress(g,"__glewBufferData");
 if(!m||!u||!d||!*m||!*u||!*d){ext_Log(">>> CPU23_GL_OBSERVER unavailable");return;}
 const u8 sig[]={0x40,0x53,0x55,0x56,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x20};
 cpu_detail_hook(0x56be20,sig,sizeof(sig),(void*)cpu23_upload,(void**)&cpu23UploadOriginal);
 if(!cpu23UploadOriginal)return;
 cpu23MapOriginal=(void*)*m;cpu23UnmapOriginal=(void*)*u;cpu23DataOriginal=(void*)*d;
 *m=(void*)cpu23_map;*u=(void*)cpu23_unmap;*d=(void*)cpu23_data;
 ext_Log(">>> CPU23_GL_OBSERVER ready; original calls and arguments preserved");
}

#ifndef CPU24_VERIFY
#define CPU24_VERIFY 0
#endif
static u8*cpu24Reference;static u64 cpu24ReferenceBytes;
static i32 cpu24_native_pack(void*dst,u64 bytes){
#if CPU24_PACK
 u8*p=cpu24Object;if(!p||!p[0xed])return 0;
 u64 begin=*(u64*)(p+0x88),end=*(u64*)(p+0x90);if(!begin||end<begin||(end-begin)%8)return 0;u64 n=(end-begin)/8;if(!n||n>16)return 0;
 u8*base=ext_GetModuleHandleA(0);u64(__attribute__((ms_abi))*count)(void*)=(void*)(base+0x581e00);const u8*(__attribute__((ms_abi))*data)(void*)=(void*)(base+0x581dc0);
 CPU24Attr a[16];
 for(u32 i=0;i<(u32)n;i++){u8*q=((u8**)begin)[i];if(!q)return 0;u32 type=*(u32*)(q+8),components=*(u32*)(q+12);if(type>2||!components||components>4)return 0;u32 scalar=type==2?1:4;u64 units=count(q);if(units>bytes/scalar)return 0;a[i].src=data(q);a[i].bytes=units*scalar;a[i].width=components*scalar;}
 i32 result=cpu24_pack(dst,bytes,a,(u32)n);
#if CPU24_VERIFY
 if(result&&cpu23Copy&&!cpu24Reference){cpu24Reference=ext_malloc(bytes);if(cpu24Reference){cpu24ReferenceBytes=bytes;u64 offset=0,stride=0;for(u32 i=0;i<(u32)n;i++)stride+=a[i].width;for(u32 i=0;i<(u32)n;i++){for(u64 v=0;v<a[i].bytes/a[i].width;v++)cpu23Copy(cpu24Reference+v*stride+offset,a[i].src+v*a[i].width,a[i].width);offset+=a[i].width;}}}
#endif
 return result;
#else
 (void)dst;(void)bytes;return 0;
#endif
}

static void cpu24_verify_gpu(u32 target,u8 unmapped){
#if CPU24_VERIFY
 if(target!=0x8892||!cpu24Reference)return;
 void**slot=(void**)ext_GetProcAddress(ext_GetModuleHandleA("glew32.dll"),"__glewGetBufferSubData");
 void(__attribute__((ms_abi))*readback)(u32,i64,i64,void*)=slot?(void*)*slot:0;
 u8*chunk=ext_malloc(4194304);u64 compared=0,mismatch=0;
 if(unmapped&&readback&&chunk)for(u64 offset=0;offset<cpu24ReferenceBytes;){u64 n=cpu24ReferenceBytes-offset;if(n>4194304)n=4194304;readback(target,offset,n,chunk);for(u64 k=0;k<n;k++)mismatch+=chunk[k]!=cpu24Reference[offset+k];compared+=n;offset+=n;}
 ext_Log(">>> CPU24_GPU_PARITY bytes %llu compared %llu mismatches %llu unmap %u",cpu24ReferenceBytes,compared,mismatch,unmapped);
 if(chunk)ext_free(chunk);ext_free(cpu24Reference);cpu24Reference=0;cpu24ReferenceBytes=0;
#else
 (void)target;(void)unmapped;
#endif
}
