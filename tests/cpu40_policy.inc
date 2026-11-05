/* CPU40 private scheduling: only serial measurements authorize parallel work.
   Every job/step is still executed. World identities are compared, not queried. */
static const void*c38World;static unsigned c38Step,c38Pairs,c38Enabled,c38Cooldown,c40ParallelAge;static unsigned long long c38Cost;
static unsigned c38_select(const void*w,unsigned pairs,unsigned step,unsigned enabled,unsigned long long ticksPerSecond){
 c38Enabled=enabled;
 if(c38World!=w||step<=c38Step){c38World=w;c38Cost=0;c38Pairs=0;c38Cooldown=0;c40ParallelAge=0;}
 c38Step=step;
 if(c38Pairs&&((unsigned long long)pairs>2ull*c38Pairs||(unsigned long long)c38Pairs>2ull*pairs)){c38Cost=0;c38Cooldown=0;c40ParallelAge=0;}
 unsigned n=0,blocked=c38Cooldown;if(c38Cooldown)c38Cooldown--;
 if(enabled&&!blocked&&pairs>=2&&c38Pairs&&c40ParallelAge<16){
  if(c38Cost>=(ticksPerSecond*35u)/100000u)n=8;
  else if(c38Cost>=ticksPerSecond/10000u)n=4;
 }
 c38Pairs=pairs;return n;
}
static void c38_observe(unsigned long long cost,unsigned long long largest,unsigned jobs){
 if(jobs>1){c40ParallelAge++;if(largest>cost-cost/4u)c38Cooldown=32;}
 else {c38Cost=cost;c40ParallelAge=0;}
}
