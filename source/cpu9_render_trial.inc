/* Native render-list scheduling; compile-time gated to the verified Steam layout. Each native job executes once.
   Scope is stack-owned inside render-list compilation; no retained job data.
   No visibility or per-eye output reuse. Other job families use native queue. */
typedef struct{void*pool;void*jobs[64];u32 count,aborted;} CPU9Batch;
static CPU9Batch*cpu9Batch;
static u32 cpu9Ready,cpu9Forced;
static void (__attribute__((ms_abi))*cpu9DispatchOriginal)(void*);
static void (__attribute__((ms_abi))*cpu9CompileOriginal)(void*,u64,u8,void*);
static void (__attribute__((ms_abi))*cpu9RenderOriginal)(void*);
static u32 cpu9Mode,cpu9RenderCount,cpu9Done,cpu9Failed,cpu9Fallback;
static u64 cpu9RenderTicks[2];static u32 cpu9RenderSamples[2];
static void cpu9_fallback(CPU9Batch*b){
 for(u32 i=0;i<b->count;i++)cpuQueueOriginal(b->pool,b->jobs[i],0);
 b->count=0;b->aborted=1;if(CPU_WORK_PROFILE)cpu9Fallback++;
}
static i32 cpu9_capture(void*pool,void*job,u8 dispatch){
 if(!cpu9Ready||!cpuThreadId||cpuThreadId()!=cpuMainThread)return 0;
 CPU9Batch*b=cpu9Batch;if(!b||b->aborted||pool!=b->pool)return 0;
 if(dispatch||!job||*(u64*)job!=cpuJobBase+0x6e9f58||b->count>=64){cpu9_fallback(b);return 0;}
 b->jobs[b->count++]=job;return 1;
}
static void cpu9_before_wait(void*pool){
 if(!cpu9Ready||!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 CPU9Batch*b=cpu9Batch;
 if(b&&!b->aborted&&pool==b->pool){
  cpu9Batch=0;
  for(u32 i=0;i<b->count;i++){
   void*j=b->jobs[i];void (__attribute__((ms_abi))*run)(void*)=(void*)*(u64*)(*(u64*)j+8);
   run(j);if(CPU_WORK_PROFILE){cpu9Done++;if(!*((u8*)j+0x18))cpu9Failed++;}
  }
  b->count=0;cpu9Batch=b;
 }
}
static void __attribute__((ms_abi)) cpu9_dispatch(void*pool){cpu9_before_wait(pool);cpu9DispatchOriginal(pool);}
static void __attribute__((ms_abi)) cpu9_compile(void*list,u64 mask,u8 option,void*pool){
 if(!cpu9Ready||!cpuThreadId||cpuThreadId()!=cpuMainThread||cpu9Batch||!(CPU_WORK_PROFILE?(cpu9Forced==1||(!cpu9Forced&&cpu9Mode)):CPU_RENDER_JOBS)){cpu9CompileOriginal(list,mask,option,pool);return;}
 CPU9Batch batch;zero_bytes(&batch,sizeof(batch));batch.pool=pool;cpu9Batch=&batch;
 cpu9CompileOriginal(list,mask,option,pool);
 if(batch.count)cpu9_fallback(&batch);
 cpu9Batch=0;
}
static void __attribute__((ms_abi)) cpu9_render(void*r){
 u64 begin=cpu_detail_begin();u32 mode=cpu9Forced?(cpu9Forced==1):(begin?((cpu9RenderCount/60)&1):0);
 cpu9Mode=mode;cpu9RenderOriginal(r);cpu9Mode=0;
 if(begin){u64 end=0;cpuCounter(&end);cpu9RenderTicks[mode]+=end-begin;cpu9RenderSamples[mode]++;cpu9RenderCount++;
 if(cpu9RenderCount%60==0){ext_Log(">>> CPU9_RENDER block %u mode %u calls %u mean_ms %.6f jobs_done %u failed %u fallback %u",cpu9RenderCount/60,mode,cpu9RenderSamples[mode],1000.0*cpu9RenderTicks[mode]/cpuFreq/cpu9RenderSamples[mode],cpu9Done,cpu9Failed,cpu9Fallback);cpu9RenderTicks[mode]=0;cpu9RenderSamples[mode]=0;}}
}
#ifndef CPU9_CONTRACT
/* Install as a group. Any signature/create/enable failure leaves all wrappers
   forwarding native calls. No job is captured until every hook is active. */
static void __attribute__((ms_abi)) cpu_queue_call(void*,void*,u8);
static void cpu9_install(void){
 static u32 tried;if(tried||(!CPU_RENDER_JOBS&&!CPU_WORK_PROFILE))return;tried=1;
 cpuThreadId=(void*)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"GetCurrentThreadId");
 if(!cpuThreadId)return;cpuMainThread=cpuThreadId();cpuJobBase=(u64)ext_GetModuleHandleA(0);
 const u8 a[]={0x40,0x53,0x48,0x83,0xec,0x20,0x80,0x79,0x38,0,0x48,0x8b,0xd9};
 const u8 b[]={0x44,0x88,0x44,0x24,0x18,0x55,0x56,0x57,0x41,0x54,0x48,0x83,0xec,0x28};
 const u8 c[]={0x40,0x56,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x83,0xc1,0x30,0x48,0x89,0x6c,0x24,0x38};
 const u8 d[]={0x48,0x83,0xec,0x28,0x48,0x85,0xd2,0x74,0x1c,0x4c,0x8b,0x49,0x18,0x48,0x8b,0x01};
 const u8 e[]={0x40,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0x38,0x04,0,0};
 u32 rvas[]={0x388030,0x376550,0x387e50,0x3880a0,0x2894a0};
 const u8*sigs[]={a,b,c,d,e};u32 sizes[]={sizeof(a),sizeof(b),sizeof(c),sizeof(d),sizeof(e)};
 void*hooks[]={(void*)cpu9_dispatch,(void*)cpu9_compile,(void*)cpu_wait_call,(void*)cpu_queue_call,(void*)cpu9_render};
 void**originals[]={(void**)&cpu9DispatchOriginal,(void**)&cpu9CompileOriginal,(void**)&cpuWaitOriginal,(void**)&cpuQueueOriginal,(void**)&cpu9RenderOriginal};
 u32 n=CPU_WORK_PROFILE?5:4;
 if(!h20_mem_readable((void*)(cpuJobBase+0x6e9f60),8)||*(u64*)(cpuJobBase+0x6e9f60)!=cpuJobBase+0x377470)return;
 for(u32 i=0;i<n;i++){u8*t=(u8*)cpuJobBase+rvas[i];if(!h20_mem_executable(t))return;for(u32 j=0;j<sizes[i];j++)if(t[j]!=sigs[i][j])return;}
 for(u32 i=0;i<n;i++)if(ext_MH_CreateHook((void*)(cpuJobBase+rvas[i]),hooks[i],originals[i]))return;
 for(u32 i=0;i<n;i++)if(ext_MH_EnableHook((void*)(cpuJobBase+rvas[i])))return;
 if(CPU_WORK_PROFILE){void*f=ext_fopen("cpu9_render_mode.txt","rb");if(f){char x=0;ext_fread(&x,1,1,f);ext_fclose(f);cpu9Forced=x=='1'?1:x=='2'?2:0;}}
 cpu9Ready=1;ext_Log(">>> Render-list scheduling enabled; native per-eye output; mode %u",CPU_WORK_PROFILE?cpu9Forced:1);
}
static void cpu_render_production_install(void){if(CPU_RENDER_JOBS&&!CPU_WORK_PROFILE)cpu9_install();}

#endif
