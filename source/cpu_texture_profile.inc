static i32 h21_copy_ascii(const void*,char*,u32);
/* Bounded main-thread attribution only; all native calls and returns preserved. */
typedef u64 (__attribute__((ms_abi))*CPUTextureBitmap)(void*,void*,i32);
typedef u64 (__attribute__((ms_abi))*CPUTextureLevel)(void*,u64,i32,void*,i32,void*,i32,i32);
typedef void (__attribute__((ms_abi))*CPUTextureMips)(void*,i32,i32,void*,void*,u64,i32);
static CPUTextureBitmap cpuBitmapOriginal;
static CPUTextureLevel cpuLevelOriginal;
static CPUTextureMips cpuMipsOriginal;
static CPUObjectCall cpuRetireOriginal;
typedef struct {u64 ticks,max,bytes;u32 calls,compressed,generated;} CPUTextureCosts;
static CPUTextureCosts cpuTextureCosts[4];static u32 cpuTextureSlow;
static void cpu_texture_cost(u32 index,u64 start,u64 end,u64 bytes,u32 compressed){
 if(!start||end<start)return;CPUTextureCosts*r=cpuTextureCosts+index;u64 d=end-start;r->ticks+=d;r->calls++;r->bytes+=bytes;r->compressed+=compressed;if(d>r->max)r->max=d;
}
static void cpu_texture_trial_begin(void*,void*,i32);
static void cpu_texture_trial_end(void);
static void cpu_texture_trial_install(void);
static u64 __attribute__((ms_abi)) cpu_bitmap_call(void*p,void*b,i32 index){
 u64 t=cpu_detail_begin();cpu_texture_trial_begin(p,b,index);u64 result=cpuBitmapOriginal(p,b,index),end=0;cpu_texture_trial_end();if(t)cpuCounter(&end);cpu_texture_cost(0,t,end,0,0);
 if(t&&end-t>cpuFreq/500&&cpuTextureSlow<12){cpuTextureSlow++;char name[65];name[0]=0;u8*q=(u8*)p+0x10;const char*src=*(u64*)((u8*)p+0x28)>15?*(const char**)q:(const char*)q;h21_copy_ascii(src,name,sizeof(name));ext_Log(">>> CPU_TEXTURE_SLOW %.4f ms dimensions %d/%d/%d compressed %u mips %d type %d name %s",1000.0*(end-t)/cpuFreq,*(i32*)((u8*)p+0xb0),*(i32*)((u8*)p+0xb4),*(i32*)((u8*)p+0xb8),*(u8*)((u8*)p+0xea),*(i32*)((u8*)p+0xdc),*(i32*)((u8*)p+0xac),name);}
 return result;
}
static u64 __attribute__((ms_abi)) cpu_level_call(void*p,u64 texture,i32 level,void*data,i32 bytes,void*size,i32 format,i32 face){
 u64 t=cpu_detail_begin();u64 result=cpuLevelOriginal(p,texture,level,data,bytes,size,format,face),end=0;if(t)cpuCounter(&end);cpu_texture_cost(1,t,end,bytes>0?(u32)bytes:0,t?*(u8*)((u8*)p+0xea):0);return result;
}
static void __attribute__((ms_abi)) cpu_mips_call(void*p,i32 target,i32 format,void*size,void*data,u64 bytes,i32 face){
 u64 t=cpu_detail_begin();cpuMipsOriginal(p,target,format,size,data,bytes,face);u64 end=0;if(t)cpuCounter(&end);cpu_texture_cost(2,t,end,0,0);
}
static void __attribute__((ms_abi)) cpu_retire_call(void*p){
 u64 t=cpu_detail_begin();cpuRetireOriginal(p);u64 end=0;if(t)cpuCounter(&end);cpu_texture_cost(3,t,end,0,0);
}
static void cpu_texture_install(void){
 if(!CPU_WORK_PROFILE)return;
 const u8 bitmap[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c};
 const u8 level[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x41,0x54};
 const u8 retire[]={0x48,0x89,0x5c,0x24,0x10,0x56,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0x28,0x01,0,0,0x33};
 cpu_detail_hook(0x569cf0,bitmap,sizeof(bitmap),(void*)cpu_bitmap_call,(void**)&cpuBitmapOriginal);
 cpu_detail_hook(0x568670,level,sizeof(level),(void*)cpu_level_call,(void**)&cpuLevelOriginal);
 cpu_detail_hook(0x5684a0,level,sizeof(level),(void*)cpu_mips_call,(void**)&cpuMipsOriginal);
 cpu_detail_hook(0x56a820,retire,sizeof(retire),(void*)cpu_retire_call,(void**)&cpuRetireOriginal);
 cpu_texture_trial_install();
}
static void cpu_texture_report(void){
 if(!CPU_WORK_PROFILE)return;for(u32 i=0;i<4;i++){CPUTextureCosts*r=cpuTextureCosts+i;ext_Log(">>> CPU_TEXTURE_COST row %u slot %u calls %u total_ms %.4f max_ms %.4f bytes %llu compressed %u",cpuRenderRows,i,r->calls,1000.0*r->ticks/cpuFreq,1000.0*r->max/cpuFreq,(unsigned long long)r->bytes,r->compressed);}zero_bytes(cpuTextureCosts,sizeof(cpuTextureCosts));
}

#include "cpu_texture_storage_trial.inc"
