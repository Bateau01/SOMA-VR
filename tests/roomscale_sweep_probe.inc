/* Research build only. Synchronous script thread, no movement or state writes. */
typedef struct {float p[4],n[4],sn[4],penetration;i32 id;void* body;} RSProbeHit;
typedef u32 (__attribute__((ms_abi)) *RSFilter)(const void*,const void*,void*);
typedef i32 (__attribute__((ms_abi)) *RSCast)(void*,const float*,const float*,const void*,float*,void*,RSFilter,RSProbeHit*,i32,i32);
typedef u8 (__attribute__((ms_abi)) *RSFit)(void*,const float*,u8,i32,float*);
typedef void* (__attribute__((ms_abi)) *RSGet)(const void*);
typedef i32 (__attribute__((ms_abi)) *RSClock)(u64*);
typedef struct {u8* c;void* skip;RSGet userdata;u32 unknown;} RSFilterCtx;
static u32 __attribute__((ms_abi)) rs_filter(const void* body,const void* collision,void* ptr){
 (void)collision;RSFilterCtx* ctx=(RSFilterCtx*)ptr;u8* b=(u8*)ctx->userdata(body);
 if(!b||!h20_mem_readable(b,0x260)){ctx->unknown++;return 0;}
 return b!=ctx->skip && b[0xe4] && b[0x24a] && *(i32*)(b+0x258)>=*(i32*)(ctx->c+0x100) && ((*(u32*)(b+0x240)&*(u32*)(ctx->c+0x50))!=0);
}
static void rs_baseline(RSFit fit,u8* c,const float* start,const float* delta,float* out){
 float push[3];for(i32 k=0;k<3;k++)out[k]=start[k];if(!fit(c,start,0,-1,push))return;
 float len=h10_len3(delta[0],0,delta[2]);i32 steps=(i32)(len/.01f)+1;float step[3]={delta[0]/steps,0,delta[2]/steps};
 for(i32 i=0;i<steps;i++){
  float old[3],next[3];for(i32 k=0;k<3;k++){old[k]=out[k];next[k]=out[k]+step[k];}
  if(fit(c,next,0,-1,push)){for(i32 k=0;k<3;k++)out[k]=next[k];}
  else {float slide[3]={step[0],0,step[2]};for(i32 plane=0;plane<2;plane++){
   push[1]=0;float n=push[0]*push[0]+push[2]*push[2],dot=slide[0]*push[0]+slide[2]*push[2];if(!(n>1e-10f&&n<100)||dot>=0)break;
   slide[0]-=push[0]*dot/n;slide[2]-=push[2]*dot/n;float sl=h10_len3(slide[0],0,slide[2]);if(!(sl>1e-6f&&sl<=len/steps+1e-6f))break;
   for(i32 k=0;k<3;k++)next[k]=out[k]+slide[k];if(fit(c,next,0,-1,push)){for(i32 k=0;k<3;k++)out[k]=next[k];break;}
  }}
  if(h10_len3(out[0]-old[0],0,out[2]-old[2])<1e-6f)break;
 }
}
static void rs_sweep(RSFit fit,RSCast cast,void* world,const void* shape,RSFilterCtx* ctx,const float* start,const float* delta,float* out){
 float push[3],remain[3]={delta[0],0,delta[2]};for(i32 k=0;k<3;k++)out[k]=start[k];if(!fit(ctx->c,start,0,-1,push))return;
 for(i32 plane=0;plane<3;plane++){
  float m[16]={1,0,0,0,0,1,0,0,0,0,1,0,out[0],out[1],out[2],1},end[3]={out[0]+remain[0],out[1],out[2]+remain[2]},t=1;RSProbeHit hits[32];
  i32 count=cast(world,m,end,shape,&t,ctx,rs_filter,hits,32,0);if(!count){for(i32 k=0;k<3;k++)out[k]=end[k];break;}
  if(!(t>=0&&t<=1))break;float len=h10_len3(remain[0],0,remain[2]);float safe=t-(len>1e-6f?.0001f/len:0);if(safe<0)safe=0;
  out[0]+=remain[0]*safe;out[2]+=remain[2]*safe;remain[0]*=1-safe;remain[2]*=1-safe;
  float n=hits[0].n[0]*hits[0].n[0]+hits[0].n[2]*hits[0].n[2];float dot=remain[0]*hits[0].n[0]+remain[2]*hits[0].n[2];if(n<1e-8f||dot>=0)break;
  remain[0]-=hits[0].n[0]*dot/n;remain[2]-=hits[0].n[2]*dot/n;if(h10_len3(remain[0],0,remain[2])<1e-6f)break;
 }
 if(!fit(ctx->c,out,0,-1,push))for(i32 k=0;k<3;k++)out[k]=start[k];
}
static i32 rs_probe(void){
 void* player=h5755ax_current_player();if(!player)return 0;u8* c=*(u8**)((u8*)player+0x170);if(!c||!h20_mem_readable(c,0x7a0))return 0;
 void* nd=ext_GetModuleHandleA("Newton.dll");RSGet worldOf=(RSGet)ext_GetProcAddress(nd,"NewtonBodyGetWorld"),user=(RSGet)ext_GetProcAddress(nd,"NewtonBodyGetUserData");RSCast cast=(RSCast)ext_GetProcAddress(nd,"NewtonWorldConvexCast");
 RSClock clock=(RSClock)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"QueryPerformanceCounter"),freq=(RSClock)ext_GetProcAddress(ext_GetModuleHandleA("kernel32.dll"),"QueryPerformanceFrequency");
 u8* b=*(u8**)(c+0x780);i32 idx=*(i32*)(c+0x770);u8** shapes=*(u8***)(c+0x788);if(!b||!h20_mem_readable(b,0x2f0)||idx<0||idx>8||!h20_mem_readable(shapes,8u*(idx+1))||!worldOf||!user||!cast)return 0;
 u8* shape=shapes[idx];if(!h20_mem_readable(shape,0x118))return 0;void* raw=*(void**)(b+0x2e8);if(!raw||user(raw)!=b)return 0;void* world=worldOf(raw);const void* col=*(void**)(shape+0x110);
 u8* base=(u8*)ext_GetModuleHandleA(0);RSFit fit=(RSFit)(base+RS_FIT_RVA);RSFilterCtx ctx={c,b,user,0};
 float original[3];for(i32 k=0;k<3;k++)original[k]=((float*)(c+0x6c))[k];u64 f;freq(&f);u32 rows=0,different=0,free=0,blocked=0;u64 cost[2]={0,0};
 u32 invalid[2]={0,0},stuck[2]={0,0},bounds[2]={0,0},moreForward[2]={0,0},moreSideways[2]={0,0};float maxDifference=0;
 for(i32 x=-3;x<=3;x++)for(i32 z=-3;z<=3;z++)for(i32 dir=0;dir<8;dir++)for(i32 distance=0;distance<2;distance++){
  float start[3]={original[0]+x*.25f,original[1]+.001f,original[2]+z*.25f},delta[3]={0,0,0},a[3],v[3],push[3];float distanceValue=distance?.1f:.005f;
  if(dir<4)delta[dir<2?0:2]=(dir%2?-1:1)*distanceValue;
  else{delta[0]=((dir-4)&1?-1:1)*distanceValue*.70710678f;delta[2]=((dir-4)&2?-1:1)*distanceValue*.70710678f;}
  if(fit(c,start,0,-1,push))free++;else blocked++;
  for(i32 repeat=0;repeat<2;repeat++)for(i32 mode=0;mode<2;mode++){i32 method=(mode+repeat)%2;u64 t0,t1;clock(&t0);if(method)rs_sweep(fit,cast,world,col,&ctx,start,delta,v);else rs_baseline(fit,c,start,delta,a);clock(&t1);cost[method]+=t1-t0;}
  float forward[2],side[2],length[2];float* outputs[2]={a,v};i32 initialFit=fit(c,start,0,-1,push);
  for(i32 mode=0;mode<2;mode++){float dx=outputs[mode][0]-start[0],dz=outputs[mode][2]-start[2];length[mode]=h10_len3(dx,0,dz);forward[mode]=(dx*delta[0]+dz*delta[2])/distanceValue;side[mode]=h9_abs(dx*delta[2]-dz*delta[0])/distanceValue;
   if(initialFit&&!fit(c,outputs[mode],0,-1,push))invalid[mode]++;
   if(length[mode]>distanceValue+.0001f||outputs[mode][1]!=start[1]||forward[mode]<-.0001f||(!initialFit&&length[mode]>.00001f))bounds[mode]++;
  }
  if(length[0]>.002f&&length[1]<.00001f)stuck[1]++;if(length[1]>.002f&&length[0]<.00001f)stuck[0]++;
  for(i32 mode=0;mode<2;mode++){if(forward[mode]>forward[1-mode]+.002f)moreForward[mode]++;if(side[mode]>side[1-mode]+.002f)moreSideways[mode]++;}
  float err=h10_len3(a[0]-v[0],a[1]-v[1],a[2]-v[2]);if(err>maxDifference)maxDifference=err;if(err>.002f){different++;if(different<=12)ext_Log("RS_COMPARE_DIFF start=%.4f,%.4f,%.4f delta=%.4f,%.4f old=%.5f,%.5f sweep=%.5f,%.5f",(double)start[0],(double)start[1],(double)start[2],(double)delta[0],(double)delta[2],(double)(a[0]-start[0]),(double)(a[2]-start[2]),(double)(v[0]-start[0]),(double)(v[2]-start[2]));}rows++;
 }
 i32 unchanged=1;for(i32 k=0;k<3;k++)if(original[k]!=((float*)(c+0x6c))[k])unchanged=0;
 ext_Log("RS_COMPARE rows=%u free=%u overlap=%u differences=%u unknown=%u baseline_us=%.4f sweep_us=%.4f unchanged=%d",rows,free,blocked,different,ctx.unknown,1e6*(double)cost[0]/((double)f*rows*2),1e6*(double)cost[1]/((double)f*rows*2),unchanged);
 ext_Log("RS_BEHAVIOR old/sweep invalid=%u/%u bounds=%u/%u stuck=%u/%u moreForward=%u/%u moreSideways=%u/%u maxDifference=%.6f",invalid[0],invalid[1],bounds[0],bounds[1],stuck[0],stuck[1],moreForward[0],moreForward[1],moreSideways[0],moreSideways[1],(double)maxDifference);return unchanged;
}
