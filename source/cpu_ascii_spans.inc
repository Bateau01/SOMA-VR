/* S26CPU1: synchronous bounded metadata read. A span lives only in this call;
   no object, type, permission, body or world state is cached. Preserve the
   original cap/ASCII/length rules and partial output on failure. */
#ifndef CPU_STRING_SPANS
#define CPU_STRING_SPANS 0
#endif
#ifndef CPU_STRING_ORACLE
#define CPU_STRING_ORACLE 0
#endif
static i32 cpu_ascii_original(const void*p,char*out,u32 cap){
 if(!p||!out||cap<6||!h20_mem_readable(p,1))return 0;const unsigned char*s=p;u32 n=0,alpha=0;
 for(;n+1<cap&&n<63;++n){if(!h20_mem_readable(s+n,1))return 0;unsigned char c=s[n];if(c==0)break;if(c<32||c>126)return 0;if((c>='A'&&c<='Z')||(c>='a'&&c<='z'))alpha++;out[n]=(char)c;}
 if(n<4||alpha<2||n>=63)return 0;out[n]=0;return 1;
}
static i32 cpu_ascii_spans(const void*p,char*out,u32 cap){
 if(!p||!out||cap<6)return 0;const unsigned char*s=p;u32 n=0,alpha=0;u64 end=0;
 for(;n+1<cap&&n<63;++n){
  u64 a=(u64)(s+n);
  if(!end||a>=end){
   H20MBI m;if(!h20_mem_query(s+n,&m)||m.State!=0x1000u)return 0;
   u32 pr=m.Protect;if((pr&0x100u)||(pr&0xffu)==0x01u)return 0;
   u64 begin=(u64)m.BaseAddress;end=begin+m.RegionSize;
   if(a<begin||a+1<a||a+1>end)return 0;
  }
  unsigned char c=s[n];if(c==0)break;if(c<32||c>126)return 0;
  if((c>='A'&&c<='Z')||(c>='a'&&c<='z'))alpha++;out[n]=(char)c;
 }
 if(n<4||alpha<2||n>=63)return 0;out[n]=0;return 1;
}
static i32 h21_copy_ascii(const void*p,char*out,u32 cap){
#if CPU_WORK_PROFILE
 if(cpuAsciiBaseline)return cpu_ascii_original(p,out,cap);
#endif
 if(!CPU_STRING_SPANS)return cpu_ascii_original(p,out,cap);
 if(CPU_STRING_ORACLE&&out&&cap>=6&&cap<=256){
  char baseline[256];for(u32 i=0;i<cap;i++)baseline[i]=out[i];
  i32 expected=cpu_ascii_original(p,baseline,cap),result=cpu_ascii_spans(p,out,cap);u32 same=expected==result;
  for(u32 i=0;i<cap;i++)if(baseline[i]!=out[i])same=0;
  static u32 calls,failures;++calls;if(!same&&failures++<16)ext_Log(">>> CPU_STRING_MISMATCH cap %u expected %d actual %d",cap,expected,result);
  if(calls==1||calls==100||calls==1000||calls==10000)ext_Log(">>> CPU_STRING_ORACLE calls %u failures %u",calls,failures);
  return result;
 }
 return cpu_ascii_spans(p,out,cap);
}
