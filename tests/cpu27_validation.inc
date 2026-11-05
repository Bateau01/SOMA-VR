/* Invocation-local query reuse only: no cached engine pointers or permissions. */
static i32 cpu27_region_contains(const H20MBI* m,const void* p,u64 n){
    u64 a=(u64)p,b=(u64)m->BaseAddress,e=b+m->RegionSize;
    return a>=b&&a+n>=a&&a+n<=e;
}
static i32 cpu27_wrapper_readable(void* w){
    H20MBI m;
    if(!w||!h20_mem_query((u8*)w+0x2e0,&m)||m.State!=0x1000u)return 0;
    u32 pr=m.Protect;
    if((pr&0x100u)||(pr&0xffu)==0x01u||!cpu27_region_contains(&m,(u8*)w+0x2e0,1))return 0;
    if(cpu27_region_contains(&m,(u8*)w+0x258,4)&&
       cpu27_region_contains(&m,(u8*)w+0x240,4)&&
       cpu27_region_contains(&m,(u8*)w+0x0e4,1))return 1;
    return h20_mem_readable((u8*)w+0x258,4)&&h20_mem_readable((u8*)w+0x240,4)&&h20_mem_readable((u8*)w+0x0e4,1);
}
