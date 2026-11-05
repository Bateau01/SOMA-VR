"""Private CPU24 bridge with eligibility independent of diagnostic timing."""
def transform(s):
 def replace(a,b):
  nonlocal s
  assert s.count(a)==1,a
  s=s.replace(a,b,1)
 s='''static void*cpu28InstallContext,*cpu28Context;
static void*(__attribute__((ms_abi))*cpu28GetContext)(void);
static i32 cpu28_main(void){return cpuThreadId&&cpuThreadId()==cpuMainThread;}
static i32 cpu28_active(void);
'''+s
 replace('cpu24Expected=0;cpu23Eligible=0;u64 t=cpu_detail_begin();if(!t||!loader)return;cpu23_install();','if(!cpu28_main())return;cpu24Expected=0;cpu23Eligible=0;u64 t=cpu_detail_begin();if(!loader)return;cpu23_install();if(!p_s26efContext||!cpu28InstallContext||p_s26efContext()!=cpu28InstallContext)return;')
 replace('static u64 cpu23_start(void){return cpu23Scope?cpu_detail_begin():0;}','static i32 cpu28_active(void){return cpu28_main()&&cpu23Scope==1&&cpu28Context&&p_s26efContext&&p_s26efContext()==cpu28Context;}\nstatic u64 cpu23_start(void){return cpu28_active()?cpu_detail_begin():0;}')
 replace('CPU24_PACK&&t&&cpu23Scope==1','CPU24_PACK&&cpu28_active()&&cpu23Scope==1')
 replace('if(CPU24_PACK&&t)cpu24_verify_gpu(a,r);','if(CPU24_PACK&&cpu28_active())cpu24_verify_gpu(a,r);')
 replace('if(t&&a==0x8892&&!c)cpu23Bytes=b>0?(u64)b:0;','if(cpu28_active()&&a==0x8892&&!c)cpu23Bytes=b>0?(u64)b:0;')
 start=s.index('static void __attribute__((ms_abi)) cpu23_upload(void*p){');end=s.index('static void cpu23_install(void){',start)
 s=s[:start]+'''static void __attribute__((ms_abi)) cpu23_upload(void*p){
 if(!cpu28_main()){cpu23UploadOriginal(p);return;}
 u64 t=cpu_detail_begin(),savedBytes=cpu23Bytes;void*savedObject=cpu24Object,*savedContext=cpu28Context;u32 savedStage=cpu23CanStage;
 cpu23Scope++;cpu23Bytes=0;cpu24Object=p;cpu23CanStage=0;
 cpu28Context=(cpu23Scope==1&&p_s26efContext&&p_s26efContext()==cpu28InstallContext)?cpu28InstallContext:0;
 cpu23UploadOriginal(p);
 cpu24Object=savedObject;cpu28Context=savedContext;cpu23Bytes=savedBytes;cpu23CanStage=savedStage;cpu23Scope--;
 cpu23_end(0,t,((u8*)p)[0xed]);
}
'''+s[end:]
 replace('if(cpu23Ready)return;cpu23Ready=1;','if(cpu23Ready)return;if(!cpu28_main()||!p_s26efContext||!p_s26efContext())return;cpu23Ready=1;cpu28InstallContext=p_s26efContext();')
 s=s.replace('p_s26efContext','cpu28GetContext')
 s=s.replace('if(cpu23Ready)return;if(!cpu28_main()', 'if(cpu23Ready)return;if(!cpu28GetContext)cpu28GetContext=(void*)ext_GetProcAddress(ext_GetModuleHandleA("opengl32.dll"),"wglGetCurrentContext");if(!cpu28_main()',1)
 return s
