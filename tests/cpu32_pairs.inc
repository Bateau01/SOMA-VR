/* Private per-Newton-step opaque pair accounting. No retained address is dereferenced. */
typedef struct {u64 a,b,calls,rejected,ticks;} CPU32Pair;
static CPU32Pair cpu32Pairs[64][128];
static u64 cpu32Lost[64];
static void cpu32_reset(void){
 for(u32 i=0;i<64;i++){cpu32Lost[i]=0;for(u32 j=0;j<128;j++)cpu32Pairs[i][j].calls=0;}
}
static void cpu32_pair(u64 start,u64 end,const void*a,const void*b,i32 accepted){
 if(!start)return;
 u32 slot=start&63;u64 aa=(u64)a,bb=(u64)b;
 u32 hash=(u32)(((aa>>4)*2654435761ULL)^((bb>>4)*2246822519ULL))&127;
 for(u32 n=0;n<128;n++){
  CPU32Pair*p=&cpu32Pairs[slot][(hash+n)&127];
  if(!p->calls){p->a=aa;p->b=bb;p->rejected=p->ticks=0;}
  else if(p->a!=aa||p->b!=bb)continue;
  p->calls++;p->rejected+=!accepted;p->ticks+=end-(start>>6);return;
 }
 cpu32Lost[slot]++;
}
static void cpu32_after(u64 start,u64 end){
 /* Called only for a completed sampled step, after the existing registry is closed. */
 u64 lost=0,total=0;for(u32 i=0;i<64;i++){lost+=cpu32Lost[i];for(u32 j=0;j<128;j++)total+=cpu32Pairs[i][j].calls;}
 cpu14_event(40,0,end,end,lost);cpu14_event(41,0,end,end,total);
 if(end-start<cpuFreq/1000)return;
 /* Top individual worker/pair buckets; intentionally not a global pair ranking. */
 for(u32 rank=0;rank<4;rank++){
  CPU32Pair*best=0;u32 worker=0;
  for(u32 i=0;i<64;i++)for(u32 j=0;j<128;j++){CPU32Pair*p=&cpu32Pairs[i][j];if(p->calls&&(!best||p->ticks>best->ticks)){best=p;worker=i;}}
  if(!best)break;u32 detail=(worker<<8)|rank;
  cpu14_event(42,detail,end,end,best->a);cpu14_event(43,detail,end,end,best->b);
  cpu14_event(44,detail,end,end,best->calls);cpu14_event(45,detail,end,end,best->rejected);cpu14_event(46,detail,end,end,best->ticks);
  best->calls=0;
 }
}
