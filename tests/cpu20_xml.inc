/* Private Steam-only retirement trial. Main-thread owned memory, no worker. */
static void*cpu20Roots[8],*cpu20Stack[256],*cpu20Eligible[2];
static u32 cpu20Head,cpu20Count,cpu20Depth,cpu20LastFrame;
static u64 cpu20Accepted,cpu20Nodes,cpu20Fallback,cpu20Slices,cpu20Ticks,cpu20Max;
static void (__attribute__((ms_abi))*cpu20Delete)(void*);
static void*cpu20ElementVT,*cpu20TextVT,*cpu20DocumentVT;
static u32 cpu20ShuttingDown;
static void* (__attribute__((ms_abi))*cpu20ShutdownOriginal)(void*,u32);
static i32 cpu20_enqueue(void*p){
 if(cpu20Count==8)return 0;
 cpu20Roots[(cpu20Head+cpu20Count)%8]=p;cpu20Count++;cpu20Accepted++;return 1;
}
static void cpu20_one(void){
 if(!cpu20Count)return;
 if(!cpu20Depth)cpu20Stack[cpu20Depth++]=cpu20Roots[cpu20Head];
 void*p=cpu20Stack[cpu20Depth-1];void*vt=*(void**)p;
 if(vt==cpu20ElementVT||vt==cpu20TextVT||vt==cpu20DocumentVT){
  void**h=*(void***)((u8*)p+0x48);void**n=h[0];
  if(n!=h&&cpu20Depth<256){
   void**next=n[0];h[0]=next;next[1]=h;(*(u64*)((u8*)p+0x50))--;
   void*child=n[2];cpu20Delete(n);
   if(child)cpu20Stack[cpu20Depth++]=child;
   return;
  }
  if(n!=h)cpu20Fallback++;
 }else cpu20Fallback++;
 ((void*(__attribute__((ms_abi))*)(void*,u32))**(void***)p)(p,1);
 cpu20Nodes++;cpu20Depth--;
 if(!cpu20Depth){cpu20Roots[cpu20Head]=0;cpu20Head=(cpu20Head+1)%8;cpu20Count--;}
}
static void cpu20_scope(void*p){
 cpu20Eligible[0]=cpu20Eligible[1]=0;
 if(!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 if(*(u32*)((u8*)p+0x54)!=26)return;
 for(u32 i=0;i<2;i++)cpu20Eligible[i]=*(void**)((u8*)p+0xa8+i*8);
}
static i32 cpu20_retire(void*p,u32 flags){
 if(!cpu20ShutdownOriginal||cpu20ShuttingDown||flags!=1||!cpuThreadId||cpuThreadId()!=cpuMainThread)return 0;
 if(p!=cpu20Eligible[0]&&p!=cpu20Eligible[1])return 0;
 if(!p||*(void**)p!=cpu20DocumentVT)return 0;
 return cpu20_enqueue(p);
}
static void cpu20_drain(void){
 if(!cpu20Count||!cpuFreq||!cpuCounter||!cpuThreadId||cpuThreadId()!=cpuMainThread)return;
 if(cpu20LastFrame==g_frameCounter)return;cpu20LastFrame=g_frameCounter;
 u64 a=0,b=0;cpuCounter(&a);b=a;u32 count=0;
 /* Clock checks amortized over 16 operations; never defer a native callback. */
 do{cpu20_one();count++;if(!(count&15)||!cpu20Count)cpuCounter(&b);}while(cpu20Count&&b-a<cpuFreq/1000&&count<8192);
 cpu20Slices++;cpu20Ticks+=b-a;if(b-a>cpu20Max)cpu20Max=b-a;
 cpu14_event(26,count,a,b,cpu20Count);
}
static void* __attribute__((ms_abi)) cpu20_shutdown(void*p,u32 flags){
 cpu20ShuttingDown=1;cpu20Eligible[0]=cpu20Eligible[1]=0;
 u32 pending=cpu20Count;u64 before=cpu20Nodes;
 if(cpuThreadId&&cpuThreadId()==cpuMainThread)while(cpu20Count)cpu20_one();
 ext_Log(">>> CPU20_SHUTDOWN pending_before %u pending_after %u nodes %llu",pending,cpu20Count,cpu20Nodes-before);
 return cpu20ShutdownOriginal(p,flags);
}
static void cpu20_init(void){
 u8*b=(u8*)ext_GetModuleHandleA(0);
 cpu20Delete=(void*)(b+0x64ae54);cpu20ElementVT=b+0x6d4ad8;cpu20TextVT=b+0x6d4a58;cpu20DocumentVT=b+0x6d4be8;
 const u8 sig[]={0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x8b,0xda,0x48,0x8b,0xf9,0xe8};
 cpu_detail_hook(0x147cc0,sig,sizeof(sig),(void*)cpu20_shutdown,(void**)&cpu20ShutdownOriginal);
}
