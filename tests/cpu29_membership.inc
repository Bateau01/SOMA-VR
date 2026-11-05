/* Private compile-boundary oracle; never used for performance measurements.
   Verify every native mesh subentity eligible for insertion is present in the
   manager's complete object set. Temporary pointer table dies before return. */
static void (__attribute__((ms_abi))*cpu29CompileOriginal)(void*,u8);
static u64 cpu29_hash(u64 x){x>>=3;x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;return x;}
static void cpu29_membership(void*world){
 u8*w=world;if(!w)return;u8*c=*(void**)(w+0x180);if(!c)return;
 u64*set=(u64*)(c+0x118);u64 cap=set[9],*entries=(void*)set[11],empty=set[10],dead=set[6];
 if(!entries||!cap||cap>1048576){ext_Log(">>> CPU29_MEMBERSHIP invalid_set");return;}
 u64 n=1;while(n<cap*2)n<<=1;u64*table=ext_malloc(n*8);if(!table){ext_Log(">>> CPU29_MEMBERSHIP allocation_failed");return;}zero_bytes(table,n*8);
 u64 members=0,expected=0,missing=0,invalid=0;
 for(u64 i=0;i<cap;i++){u64 v=entries[i];if(v==empty||(set[7]&&v==dead))continue;if(!v){invalid++;continue;}u64 k=cpu29_hash(v)&(n-1);while(table[k]&&table[k]!=v)k=(k+1)&(n-1);if(!table[k])members++;table[k]=v;}
 for(u32 family=0;family<2;family++){
  void**head=*(void***)(w+0x310+family*0x18);u64 count=*(u64*)(w+0x318+family*0x18),seen=0;if(!head){invalid++;continue;}
  for(void**node=head[0];node!=head&&seen<count;node=node[0],seen++){
   u8*mesh=node[2];if(!mesh){invalid++;continue;}u64 first=*(u64*)(mesh+0x1f0),end=*(u64*)(mesh+0x1f8);if(end<first||(end-first)%8||(end-first)/8>65536){invalid++;continue;}
   for(u64 j=0;j<(end-first)/8;j++){u8*sub=((u8**)first)[j];if(!sub){invalid++;continue;}u8*material=*(void**)(sub+0x1c0);if(!material){invalid++;continue;}if(material[0x174])continue;expected++;u64 v=(u64)sub,k=cpu29_hash(v)&(n-1);while(table[k]&&table[k]!=v)k=(k+1)&(n-1);if(table[k]!=v)missing++;}
  }
  if(seen!=count)invalid++;
 }
 ext_Log(">>> CPU29_MEMBERSHIP members %llu mesh_expected %llu missing %llu invalid %llu compiled %u",members,expected,missing,invalid,*(u32*)(w+0x198));ext_free(table);
}
static void __attribute__((ms_abi)) cpu29_compile(void*w,u8 flag){cpu29CompileOriginal(w,flag);if(cpuThreadId&&cpuThreadId()==cpuMainThread)cpu29_membership(w);}
static void cpu29_install(void){
 const u8 sig[]={0x48,0x8b,0xc4,0x55,0x41,0x54,0x48,0x8d,0x68,0xa1,0x48,0x81,0xec,0xe8,0,0,0};
 cpu_detail_hook(0x24f4d0,sig,sizeof(sig),(void*)cpu29_compile,(void**)&cpu29CompileOriginal);
 ext_Log(">>> CPU29_MEMBERSHIP_ORACLE ready %u",cpu29CompileOriginal!=0);
}
