/* Private candidate. Only iXmlNode destructor's child-list clear call.
   Retain the existing empty sentinel rather than allocate its immediate replacement.
   Native child destructors, their order and node frees remain synchronous. */
static void (__attribute__((ms_abi))*cpu19Original)(void*);
static void (__attribute__((ms_abi))*cpu19Delete)(void*);
static void*cpu19Caller;
static u64 cpu19Calls;
static void cpu19_clear(void*p){
 void**head=*(void***)p;
 for(void**n=head[0];n!=head;n=n[0]){
  void*child=n[2];
  if(child)((void*(__attribute__((ms_abi))*)(void*,u32))**(void***)child)(child,1);
 }
 void**n=head[0];head[0]=head;head[1]=head;((u64*)p)[1]=0;
 while(n!=head){void**next=n[0];cpu19Delete(n);n=next;}
 __atomic_fetch_add(&cpu19Calls,1ULL,__ATOMIC_RELAXED);
}
static void __attribute__((ms_abi)) cpu19_clear_hook(void*p){
 if(__builtin_return_address(0)!=cpu19Caller){cpu19Original(p);return;}
 cpu19_clear(p);
}
static void cpu19_install(void){
 u8*b=(u8*)ext_GetModuleHandleA(0);
 const u8 call[]={0xe8,0x9e,0x62,0x0b,0};
 for(u32 i=0;i<5;i++)if(b[0x23bcbd+i]!=call[i])return;
 cpu19Caller=b+0x23bcc2;
 cpu19Delete=(void*)(b+0x64ae54);
 const u8 sig[]={0x48,0x89,0x5c,0x24,0x18,0x56,0x48,0x83,0xec,0x40,0x48,0x8b,0x01,0x48,0x8b,0xf1};
 cpu_detail_hook(0x2f1f60,sig,sizeof(sig),(void*)cpu19_clear_hook,(void**)&cpu19Original);
 ext_Log(">>> CPU19 private XML destructor sentinel trial %u",cpu19Original!=0);
}
