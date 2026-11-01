/* Experimental conservative compound-leaf rejection. See docs/CPU56_PHYSICS.md. */
#ifndef CPU_LEAF_FILTER
#define CPU_LEAF_FILTER 0
#endif
#if CPU_LEAF_FILTER
static int(*c56Pair)(void*,void*,void*,int),(*c56Leaf)(void*,void*);
static u64 c56Module;static u32 c56LastEpoch;
static unsigned c56Depth,c56Ready;
static void(*c56Motion)(const void*,float,float*,float*);
static void(*c56Com)(const void*,float*);
static float c56_abs(float a){return a<0?-a:a;}
static int c56_orthogonal(const float*m){for(int a=0;a<3;a++)for(int b=0;b<3;b++){float v=0;for(int k=0;k<3;k++)v+=m[a*4+k]*m[b*4+k];if(!h9_good(v,2.f)||c56_abs(v-(a==b?1.f:0.f))>.0001f)return 0;}return 1;}
/* Pair-local reuse: native traversal has no leaf callback on this path, and
   the solver has not run yet. Never reuse these values across native pairs. */
typedef struct {const void*body;float dt;__attribute__((aligned(16))) float vel[4],omega[4],com[4];} C56Motion;
static C56Motion c56MotionCache[2];
static unsigned c56MotionCount;
static void c56_motion(const void*body,float dt,float*vel,float*omega,float*com){
 C56Motion*q=0;for(unsigned i=0;i<c56MotionCount;i++)if(c56MotionCache[i].body==body&&c56MotionCache[i].dt==dt){q=c56MotionCache+i;break;}
 if(!q&&c56MotionCount<2){q=c56MotionCache+c56MotionCount++;q->body=body;q->dt=dt;c56Motion(body,dt,q->vel,q->omega);c56Com(body,q->com);}
 if(q){for(int i=0;i<4;i++){vel[i]=q->vel[i];omega[i]=q->omega[i];com[i]=q->com[i];}}
 else {c56Motion(body,dt,vel,omega);c56Com(body,com);}
}
typedef struct {u32 epoch;const void*shape;float lo[3],hi[3];} C56Bound;
static C56Bound c56Bounds[256];
static int c56_bound(const void*shape,float*lo,float*hi){
 if(c43Epoch<c56LastEpoch){for(int i=0;i<256;i++)c56Bounds[i].epoch=0;}c56LastEpoch=c43Epoch;
 unsigned ix=((u64)shape>>5)&255u;C56Bound*q=c56Bounds+ix;
 if(q->epoch!=c43Epoch||q->shape!=shape){
  void(*bounds)(const void*,const float*,float*,float*)=(void*)(*(void***)shape)[4];
  u32 kind=*(u32*)((const u8*)shape+0x68);u64 method=(u64)bounds-c56Module;if(kind>6||kind==5||(method!=0x6e470&&method!=0x67890))return 0;
  const float*extent=(const float*)((const u8*)shape+(method==0x6e470?0x140:0x80));const float*centre=(const float*)((const u8*)shape+0x90);
  for(int a=0;a<3;a++){float c=method==0x6e470?0:centre[a],e=extent[a];q->lo[a]=c-e;q->hi[a]=c+e;if(!h9_good(q->lo[a],100.f)||!h9_good(q->hi[a],100.f)||e<0)return 0;}
  q->epoch=c43Epoch;q->shape=shape;
 }
 for(int a=0;a<3;a++){lo[a]=q->lo[a];hi[a]=q->hi[a];}return 1;
}
static int c56_empty(void*proxy){
 u8*p=proxy;float dt=*(float*)(p+0xa0),margin=*(float*)(p+0xa4);if(!h9_good(dt,1.f)||dt<=0||!h9_good(margin,1.f)||margin<0)return 0;
 float lows[2][3],highs[2][3];
 for(int b=0;b<2;b++){
  const void*body=*(void**)(p+b*8),*shape=*(void**)(p+0x10+b*8);const float*m=(float*)(p+0x20+b*0x40);if(!c56_orthogonal(m))return 0;
  float lo[3],hi[3];if(!c56_bound(shape,lo,hi))return 0;
  __attribute__((aligned(16))) float vel[4]={0},omega[4]={0},com[4]={0};float pad=margin+.02f;
  if(*(u32*)(p+0xa8)){c56_motion(body,dt,vel,omega,com);const float*bm=(const float*)((const u8*)body+0x40);float radius=0,angle=0;
   for(int a=0;a<3;a++){float x=m[12+a]-bm[12+a];for(int k=0;k<3;k++)x-=bm[k*4+a]*com[k];radius+=c56_abs(x);float extent=c56_abs(lo[a])>c56_abs(hi[a])?c56_abs(lo[a]):c56_abs(hi[a]);radius+=extent;angle+=c56_abs(omega[a])*dt;if(!h9_good(vel[a],1000)||!h9_good(omega[a],1000)||!h9_good(radius,1000))return 0;}if(angle>2)angle=2;pad+=radius*angle;
  }
  for(int a=0;a<3;a++){float l=m[12+a],h=l;for(int k=0;k<3;k++){float x=m[k*4+a]*lo[k],y=m[k*4+a]*hi[k];l+=x<y?x:y;h+=x>y?x:y;}float d=vel[a]*dt;lows[b][a]=l+(d<0?d:0)-pad;highs[b][a]=h+(d>0?d:0)+pad;}
 }
 for(int a=0;a<3;a++)if(highs[0][a]<lows[1][a]||highs[1][a]<lows[0][a])return 1;return 0;
}
static int c56_supported(void*p){for(int b=0;b<2;b++){const u8*s=*(const u8**)((u8*)p+0x10+b*8);u32 k=*(const u32*)(s+0x68);u64 method=(u64)(*(void***)s)[4]-c56Module;if(k>6||k==5||(method!=0x6e470&&method!=0x67890))return 0;}return 1;}
static int c56_leaf(void*w,void*p){
 if(!C43_MAIN()||!c43Active||!c56Depth||!c56_supported(p))return c56Leaf(w,p);
 unsigned csr;__asm__ volatile("stmxcsr %0":"=m"(csr));
 int empty=c56_empty(p);__asm__ volatile("ldmxcsr %0"::"m"(csr));
 if(empty){*(u32*)((u8*)p+0xd0)&=~2u;return 0;}return c56Leaf(w,p);
}
static int c56_pair(void*a,void*b,void*c,int d){if(!C43_MAIN()||!c43Active||!c56Ready||c56Depth)return c56Pair(a,b,c,d);const u8*material=*(const u8**)((u8*)b+0x18);if(!material||*(void**)(material+0xb8))return c56Pair(a,b,c,d);c56MotionCount=0;c56Depth=1;int r=c56Pair(a,b,c,d);c56Depth=0;return r;}
/* Redirect only the compound traversal's CALL, not the shared convex entry.
   A nearby absolute-jump relay preserves the native return address and ABI.
   Installation runs before NewtonUpdate under c44's loaded-module hash guard. */
static int c56_redirect(u8*site,void*target){
 void*k=ext_GetModuleHandleA("kernel32.dll");if(!k)return 0;
 void*(*alloc)(void*,u64,u32,u32)=(void*)ext_GetProcAddress(k,"VirtualAlloc");
 i32(*protect)(void*,u64,u32,u32*)=(void*)ext_GetProcAddress(k,"VirtualProtect");
 i32(*flush)(void*,const void*,u64)=(void*)ext_GetProcAddress(k,"FlushInstructionCache");
 i32(*freepage)(void*,u64,u32)=(void*)ext_GetProcAddress(k,"VirtualFree");
 if(!alloc||!protect||!flush||!freepage)return 0;
 u64 base=(u64)site&~65535ull;u8*relay=0;
 for(u64 d=65536;d<0x40000000ull&&!relay;d+=65536){relay=alloc((void*)(base+d),4096,0x3000,4);if(!relay&&base>d)relay=alloc((void*)(base-d),4096,0x3000,4);}
 if(!relay)return 0;
 i64 delta=(i64)(u64)relay-(i64)(u64)(site+5);if(delta<(-2147483647ll-1)||delta>2147483647ll){freepage(relay,0,0x8000);return 0;}
 relay[0]=0xff;relay[1]=0x25;for(int i=2;i<6;i++)relay[i]=0;c43_copy(relay+6,&target,8);
 u32 old;if(!protect(relay,4096,0x20,&old)){freepage(relay,0,0x8000);return 0;}flush((void*)(i64)-1,relay,14);
 if(!protect(site,5,0x40,&old)){freepage(relay,0,0x8000);return 0;}
 i32 rel=(i32)delta;site[0]=0xe8;c43_copy(site+1,&rel,4);u32 ignored;protect(site,5,old,&ignored);flush((void*)(i64)-1,site,5);return 1;
}
static void c56_install(u8*m){
 c56Module=(u64)m;c56Motion=(void*)(m+0x5e860);c56Com=(void*)ext_GetProcAddress(m,"NewtonBodyGetCentreOfMass");if(!c56Com)return;
 const u8 pair[]={0x44,0x89,0x4c,0x24,0x20,0x48,0x89,0x54,0x24,0x10,0x55,0x53,0x56,0x57,0x41,0x54};
 const u8 leaf[]={0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c,0x24,0x20,0x55,0x41,0x54,0x41,0x56};
 const u8 call[]={0xe8,0x53,0x6e,0x01,0x00};
 if(!c43_equal(m+0x7e340,pair,16)||!c43_equal(m+0x95540,leaf,15)||!c43_equal(m+0x7e6e8,call,5))return;
 c56Leaf=(void*)(m+0x95540);
 if(ext_MH_CreateHook(m+0x7e340,c56_pair,(void**)&c56Pair)||ext_MH_EnableHook(m+0x7e340))return;
 if(!c56_redirect(m+0x7e6e8,c56_leaf))return;
 c56Ready=1;ext_Log(">>> CPU LEAF FILTER: verified compound-local rejection enabled");
}

#else
#define c56_install(m) ((void)0)
#endif
