/* Experimental Steam streaming work. No observer, GPU readback or physics hooks.
   Main-thread scopes contain live loader pointers only; retirement owns detached
   XML allocations, never the source world/loader. See CPU29 native evidence. */
#ifndef CPU_STREAMING_OPTIMISATIONS
#define CPU_STREAMING_OPTIMISATIONS 0
#endif
static u32 s29Ready,s29Tried,s29Main,s29Stopping,s29LastFrame;
static u32 (__attribute__((ms_abi))*s29Thread)(void);
static i32 (__attribute__((ms_abi))*s29Clock)(u64*);
static u64 s29Freq;
static void*(__attribute__((ms_abi))*s29Context)(void);
static void*s29GL;
static u8*s29Base;
static void (__attribute__((ms_abi))*s29UpdateOriginal)(void*,u64,u64);
static void (__attribute__((ms_abi))*s29PrepareOriginal)(void*);
static void*(__attribute__((ms_abi))*s29XmlOriginal)(void*,u32);
static void*(__attribute__((ms_abi))*s29ShutdownOriginal)(void*,u32);
static void (__attribute__((ms_abi))*s29ModuleOriginal)(void*,i32,float);
static void (__attribute__((ms_abi))*s29UploadOriginal)(void*);
static void*(__attribute__((ms_abi))*s29MapOriginal)(u32,u32);
static void (__attribute__((ms_abi))*s29DataOriginal)(u32,i64,const void*,u32);
static void (__attribute__((ms_abi))*s29Delete)(void*);
static void*s29Eligible[2],*s29Expected,*s29Object,*s29Roots[8],*s29Stack[256];
static u32 s29Head,s29Count,s29Depth,s29UploadDepth;
static u64 s29Bytes;
static i32 s29_main(void){return s29Ready&&s29Thread&&s29Thread()==s29Main;}
static void s29_one(void){
 if(!s29Count)return;
 if(!s29Depth)s29Stack[s29Depth++]=s29Roots[s29Head];
 void*p=s29Stack[s29Depth-1];void*vt=*(void**)p;
 if(vt==s29Base+0x6d4ad8||vt==s29Base+0x6d4a58||vt==s29Base+0x6d4be8){
  void**head=*(void***)((u8*)p+0x48),**node=head[0];
  if(node!=head&&s29Depth<256){
   void**next=node[0];head[0]=next;next[1]=head;(*(u64*)((u8*)p+0x50))--;
   void*child=node[2];s29Delete(node);if(child)s29Stack[s29Depth++]=child;return;
  }
 }
 ((void*(__attribute__((ms_abi))*)(void*,u32))**(void***)p)(p,1);
 s29Depth--;if(!s29Depth){s29Roots[s29Head]=0;s29Head=(s29Head+1)%8;s29Count--;}
}
static void s29_drain(void){
 if(!s29Count||!s29_main()||s29LastFrame==g_frameCounter)return;s29LastFrame=g_frameCounter;
 u64 begin=0,end=0;s29Clock(&begin);end=begin;u32 operations=0;
 do{s29_one();operations++;if(!(operations&15)||!s29Count)s29Clock(&end);}
 while(s29Count&&end-begin<s29Freq/1000&&operations<8192);
}
static void*__attribute__((ms_abi)) s29_xml(void*p,u32 flags){
 if(s29_main()&&!s29Stopping&&flags==1&&p&&(p==s29Eligible[0]||p==s29Eligible[1])&&*(void**)p==s29Base+0x6d4be8){
  if(s29Count<8){
   for(u32 i=0;i<s29Count;i++)if(s29Roots[(s29Head+i)%8]==p)return p;
   s29Roots[(s29Head+s29Count)%8]=p;s29Count++;
   for(u32 i=0;i<2;i++)if(s29Eligible[i]==p)s29Eligible[i]=0;
   return p;
  }
 }
 return s29XmlOriginal(p,flags);
}
static void*__attribute__((ms_abi)) s29_shutdown(void*p,u32 flags){
 s29Stopping=1;s29Eligible[0]=s29Eligible[1]=0;
 if(s29_main())while(s29Count)s29_one();
 return s29ShutdownOriginal(p,flags);
}
static void __attribute__((ms_abi)) s29_module(void*p,i32 event,float dt){
 i32 drain=s29Count&&s29_main()&&event==6&&p&&*(void**)p==s29Base+0x6c2b58;
 s29ModuleOriginal(p,event,dt);if(drain)s29_drain();
}
static void __attribute__((ms_abi)) s29_update(void*p,u64 arg,u64 budget){
 if(!s29_main()||!p){s29UpdateOriginal(p,arg,budget);return;}
 void*saved[2]={s29Eligible[0],s29Eligible[1]},*expected=s29Expected;
 s29Eligible[0]=s29Eligible[1]=s29Expected=0;u8*l=p;u32 stage=*(u32*)(l+0x54);
 if(!s29Stopping&&stage==26){s29Eligible[0]=*(void**)(l+0xa8);s29Eligible[1]=*(void**)(l+0xb0);}
 if(stage==6&&s29Context()==s29GL){
  u64 first=*(u64*)(l+0x380),last=*(u64*)(l+0x388),index=*(u64*)(l+0x58);
  if(first&&last>=first&&!((last-first)%8)&&index<(last-first)/8)s29Expected=((void**)first)[index];
 }
 s29UpdateOriginal(p,arg,budget);
 s29Eligible[0]=saved[0];s29Eligible[1]=saved[1];s29Expected=expected;
}
static void __attribute__((ms_abi)) s29_prepare(void*p){
 if(s29_main()&&p&&*(u32*)((u8*)p+0x54)==5){
  u8*w=*(void**)((u8*)p+0x1c8);
  if(w&&!*(void**)(w+0x180)&&!*(u32*)(w+0x198)&&*(void**)(w+0xd8))
   ((u64(__attribute__((ms_abi))*)(u64))(s29Base+0x24f2c0))((u64)w);
 }
 s29PrepareOriginal(p);
}
static i32 s29_pack(void*destination,u64 capacity){
 u8*p=s29Object;if(!p||!p[0xed])return 0;
 u64 first=*(u64*)(p+0x88),last=*(u64*)(p+0x90);
 if(!first||last<first||(last-first)%8)return 0;u64 count=(last-first)/8;if(!count||count>16)return 0;
 const u8*data[16];u32 width[16];u64 vertices=0,stride=0;
 for(u32 i=0;i<count;i++){
  u8*a=((u8**)first)[i];if(!a)return 0;u32 type=*(u32*)(a+8),n=*(u32*)(a+12);
  if(type>2||!n||n>4)return 0;u32 scalar=type==2?1:4;
  u64 units=((u64(__attribute__((ms_abi))*)(void*))(s29Base+0x581e00))(a);
  if(!units||units>capacity/scalar||units%n)return 0;u64 v=units/n;if(i&&v!=vertices)return 0;vertices=v;
  data[i]=((const u8*(__attribute__((ms_abi))*)(void*))(s29Base+0x581dc0))(a);if(!data[i])return 0;
  width[i]=n*scalar;stride+=width[i];
 }
 if(!stride||capacity%stride||capacity/stride!=vertices)return 0;
 u8*dst=destination;
 for(u64 v=0;v<vertices;v++)for(u32 i=0;i<count;i++){
  const u8*src=data[i];u32 n=width[i];
  switch(n){case 16:__builtin_memcpy(dst,src,16);break;case 12:__builtin_memcpy(dst,src,12);break;case 8:__builtin_memcpy(dst,src,8);break;case 4:__builtin_memcpy(dst,src,4);break;default:for(u32 j=0;j<n;j++)dst[j]=src[j];break;}
  dst+=n;data[i]+=n;
 }
 return 1;
}
static i32 s29_upload_active(void){return s29_main()&&s29UploadDepth==1&&s29Context()==s29GL;}
static void*__attribute__((ms_abi)) s29_map(u32 target,u32 access){
 void*result=s29MapOriginal(target,access);
 if(result&&s29_upload_active()&&s29Object==s29Expected&&s29Object&&target==0x8892&&access==0x88b9&&s29Bytes>=65536&&s29Bytes<=67108864&&s29_pack(result,s29Bytes))return 0;
 return result;
}
static void __attribute__((ms_abi)) s29_data(u32 target,i64 bytes,const void*data,u32 usage){
 if(s29_upload_active()&&target==0x8892&&!data)s29Bytes=bytes>0?(u64)bytes:0;
 s29DataOriginal(target,bytes,data,usage);
}
static void __attribute__((ms_abi)) s29_upload(void*p){
 if(!s29_main()){s29UploadOriginal(p);return;}
 void*saved=s29Object;u64 bytes=s29Bytes;s29UploadDepth++;s29Object=p;s29Bytes=0;
 s29UploadOriginal(p);s29Object=saved;s29Bytes=bytes;s29UploadDepth--;
}
static i32 s29_signature(u32 rva,const u8*sig,u32 size){
 u8*p=s29Base+rva;if(!h20_mem_executable(p)||!h20_mem_readable(p,size))return 0;
 for(u32 i=0;i<size;i++)if(p[i]!=sig[i])return 0;return 1;
}
static void s29_install(void){
 if(!CPU_STREAMING_OPTIMISATIONS||s29Tried)return;
 void*gl=ext_GetModuleHandleA("opengl32.dll");if(!gl)return;
 s29Context=(void*)ext_GetProcAddress(gl,"wglGetCurrentContext");if(!s29Context||!s29Context())return;
 s29Tried=1;s29GL=s29Context();s29Base=ext_GetModuleHandleA(0);
 void*k=ext_GetModuleHandleA("kernel32.dll");s29Thread=(void*)ext_GetProcAddress(k,"GetCurrentThreadId");
 s29Clock=(void*)ext_GetProcAddress(k,"QueryPerformanceCounter");i32(__attribute__((ms_abi))*freq)(u64*)=(void*)ext_GetProcAddress(k,"QueryPerformanceFrequency");
 if(!s29Thread||!s29Clock||!freq||!freq(&s29Freq)||!s29Freq)return;s29Main=s29Thread();
 const u8 update[]={0x40,0x53,0x56,0x48,0x83,0xec,0x28,0x48,0x83,0xb9,0xc8,1,0,0,0,0x0f};
 const u8 prepare[]={0x40,0x53,0x57,0x48,0x83,0xec,0x28,0x48,0x8b,0x91,0xe0,2,0,0,0x48,0x89};
 const u8 dtor[]={0x48,0x89,0x5c,0x24,8,0x57,0x48,0x83,0xec,0x20,0x8b,0xda,0x48,0x8b,0xf9,0xe8};
 const u8 module[]={0x48,0x83,0xec,0x28,0x80,0x79,0x32,0,0x4c,0x8b,0xc1,0x0f,0x84,0x0f,1,0};
 const u8 upload[]={0x40,0x53,0x55,0x56,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x20};
 const u8 convert[]={0x4c,0x8b,0xdc,0x41,0x56,0x48,0x83,0xec,0x50,0x48,0x8b,0x81,0x80,1,0,0};
 const u8 count[]={0x48,0x8b,0x41,0x30,0x48,0x8b,0xd1,0x48,0x85,0xc0,0x75,0x45,0x8b,0x49,8};
 const u8 data[]={0x8b,0x51,8,0x85,0xd2,0x74,0x1b,0xff,0xca,0x74,0x11,0xff,0xca,0x75,0x2a,0x48};
 const u8 scalarDelete[]={0xff,0x25,0x56,0xa6,3,0};
 if(!s29_signature(0x24f2c0,convert,sizeof(convert))||!s29_signature(0x581e00,count,sizeof(count))||!s29_signature(0x581dc0,data,sizeof(data))||!s29_signature(0x64ae54,scalarDelete,sizeof(scalarDelete)))return;
 const u32 rva[]={0x46b410,0x45eef0,0x23d4d0,0x147cc0,0x15a390,0x56be20};
 const u8*sig[]={update,prepare,dtor,dtor,module,upload};u32 sizes[]={sizeof(update),sizeof(prepare),sizeof(dtor),sizeof(dtor),sizeof(module),sizeof(upload)};
 void*hooks[]={(void*)s29_update,(void*)s29_prepare,(void*)s29_xml,(void*)s29_shutdown,(void*)s29_module,(void*)s29_upload};
 void**originals[]={(void**)&s29UpdateOriginal,(void**)&s29PrepareOriginal,(void**)&s29XmlOriginal,(void**)&s29ShutdownOriginal,(void**)&s29ModuleOriginal,(void**)&s29UploadOriginal};
 for(u32 i=0;i<6;i++)if(!s29_signature(rva[i],sig[i],sizes[i]))return;
 void*glew=ext_GetModuleHandleA("glew32.dll");void**map=(void*)ext_GetProcAddress(glew,"__glewMapBuffer"),**buf=(void*)ext_GetProcAddress(glew,"__glewBufferData");
 if(!map||!buf||!*map||!*buf)return;
 s29Delete=(void*)(s29Base+0x64ae54);
 for(u32 i=0;i<6;i++)if(ext_MH_CreateHook(s29Base+rva[i],hooks[i],originals[i]))return;
 for(u32 i=0;i<6;i++)if(ext_MH_EnableHook(s29Base+rva[i]))return;
 s29MapOriginal=(void*)*map;s29DataOriginal=(void*)*buf;*map=(void*)s29_map;*buf=(void*)s29_data;
 s29Ready=1;ext_Log(">>> Experimental streaming preparation enabled: bounded XML cleanup, native visibility construction, sequential vertex packing");
}
