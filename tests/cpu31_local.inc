/* Private invocation-local readable-region proof. No permissions are cached. */
typedef struct {void* wrapper;H20MBI region;i32 valid;} CPU31View;
static i32 cpu31_readable(CPU31View*v,void*w,const void*p,u64 n){
 u64 a=(u64)p,b=(u64)v->region.BaseAddress,e=b+v->region.RegionSize;
 if(v->valid&&v->wrapper==w&&a>=b&&a+n>=a&&e>=b&&a+n<=e)return 1;
 H20MBI m;if(!h20_mem_query(p,&m)||m.State!=0x1000u)return 0;
 u32 pr=m.Protect;b=(u64)m.BaseAddress;e=b+m.RegionSize;
 if((pr&0x100u)||(pr&0xffu)==0x01u||a<b||a+n<a||a+n>e)return 0;
 v->wrapper=w;v->region=m;v->valid=1;return 1;
}
static i32 cpu31_rocker(const void*,CPU31View*);
