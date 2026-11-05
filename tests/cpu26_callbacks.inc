/* Private observer. Callback arguments/results and native contact policy unchanged. */
typedef struct {u64 calls,ticks,max;} CPU26Slot;
static CPU26Slot cpu26Slots[64][3];
static u32 cpu26Owners[64];
static u32 cpu26Active,cpu26Sequence,cpu26Threads,cpu26Invalid;
static void (__attribute__((ms_abi))*cpu26ContactOriginal)(const void*,float,i32);
static i32 (__attribute__((ms_abi))*cpu26ThreadCount)(const void*);
static u64 cpu26_begin_callback(i32 thread){
 if(!__atomic_load_n(&cpu26Active,__ATOMIC_ACQUIRE))return 0;
 (void)thread;u32 owner=cpuThreadId(),base=(owner*2654435761u)>>26;
 for(u32 probe=0;probe<64;probe++){u32 slot=(base+probe)&63,expected=0;
  if(__atomic_compare_exchange_n(&cpu26Owners[slot],&expected,owner,0,__ATOMIC_RELAXED,__ATOMIC_RELAXED)||expected==owner){
   u64 t=0;cpuCounter(&t);if(t&&t<(1ULL<<58))return (t<<6)|slot;break;
  }
 }
 __atomic_fetch_add(&cpu26Invalid,1,__ATOMIC_RELAXED);return 0;
}
static void cpu26_end_callback(u32 kind,i32 thread,u64 start){
 (void)thread;if(!start)return;u64 end=0;cpuCounter(&end);CPU26Slot*s=&cpu26Slots[start&63][kind];u64 dt=end-(start>>6);s->calls++;s->ticks+=dt;if(dt>s->max)s->max=dt;
}
static void __attribute__((ms_abi)) cpu26_contact(const void*j,float dt,i32 thread){
 u64 t=cpu26_begin_callback(thread);cpu26ContactOriginal(j,dt,thread);cpu26_end_callback(1,thread,t);
}
static void cpu26_before(const void*w){
 __atomic_store_n(&cpu26Active,0,__ATOMIC_RELEASE);
 if(!cpu26ThreadCount||!cpu_detail_begin()||cpu14Saved||((cpu26Sequence++)&3u))return;
 i32 n=cpu26ThreadCount(w);if(n<1||n>64)return;cpu26Threads=(u32)n;
 for(u32 i=0;i<64;i++)for(u32 k=0;k<3;k++){cpu26Slots[i][k].calls=cpu26Slots[i][k].ticks=cpu26Slots[i][k].max=0;}
 for(u32 i=0;i<64;i++)cpu26Owners[i]=0;
 cpu26Invalid=0;__atomic_store_n(&cpu26Active,1,__ATOMIC_RELEASE);
}
static void cpu26_after(u64 start,u64 end){
 if(!__atomic_exchange_n(&cpu26Active,0,__ATOMIC_ACQ_REL))return;
 cpu14_event(34,cpu26Threads,start,end,cpu26Invalid);
 u64 mask=0;for(u32 i=0;i<64;i++)if(cpu26Owners[i])mask|=1ULL<<i;cpu14_event(37,cpu26Threads,end,end,mask);
 static u32 first; if(first<4){first++;u32 n=0;for(u32 i=0;i<64;i++)n+=cpu26Owners[i]!=0;ext_Log(">>> CPU26 coverage sample %u actual_threads %u rejected %u",first,n,cpu26Invalid);}
 for(u32 k=0;k<3;k++){u64 ticks=0,calls=0,maximum=0;
  for(u32 i=0;i<64;i++){CPU26Slot*s=&cpu26Slots[i][k];ticks+=s->ticks;calls+=s->calls;if(s->max>maximum)maximum=s->max;}
  /* Identity is aggregate QPC ticks, not a pointer. Point event avoids pretending worker sums are wall spans. */
  cpu14_event(33,k,end,end,ticks);cpu14_event(35,k,end,end,calls);cpu14_event(36,k,end,end,maximum);
 }
}
static void cpu26_install(void){
 const u8 b[]={0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x4c,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41};
 cpu_detail_hook(0x57e0a0,b,sizeof(b),(void*)cpu26_contact,(void**)&cpu26ContactOriginal);
 if(cpu26ContactOriginal)cpu26ThreadCount=(void*)ext_GetProcAddress(ext_GetModuleHandleA("Newton.dll"),"NewtonGetThreadsCount");
 ext_Log(">>> CPU26 callbacks installed existing-overlap-wrapper 1 contact %u threads %u",cpu26ContactOriginal!=0,cpu26ThreadCount!=0);
}
