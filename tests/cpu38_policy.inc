/* Private policy: timing affects scheduling only, never contact eligibility. */
static const void*c38World;static unsigned c38Step,c38Pairs,c38Enabled,c38Cooldown;static unsigned long long c38Cost;
static unsigned c38_select(const void*w,unsigned pairs,unsigned step,unsigned enabled,unsigned long long ticksPerSecond){
 c38Enabled=enabled;
 if(c38World!=w||step<=c38Step){c38World=w;c38Cost=0;c38Pairs=0;c38Cooldown=0;}
 c38Step=step;unsigned n=0;if(c38Pairs!=pairs)c38Cooldown=0;unsigned blocked=c38Cooldown;if(c38Cooldown)c38Cooldown--;
 if(enabled&&!blocked&&pairs>=2&&c38Pairs&&pairs<=c38Pairs*2u&&c38Pairs<=pairs*2u){
  if(c38Cost>=(ticksPerSecond*35u)/100000u)n=8;
  else if(c38Cost>=ticksPerSecond/10000u)n=4;
 }
 c38Pairs=pairs;return n;
}
static void c38_observe(unsigned long long cost,unsigned long long largest,unsigned jobs){c38Cost=cost;if(jobs>1&&largest>cost-cost/4u)c38Cooldown=32;}
