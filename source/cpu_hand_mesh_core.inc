/* Private same-job expensive tree/compound zero-result reuse.
   No references survive c43_begin/end. No contact or solver pair is removed. */
typedef struct {unsigned epoch;unsigned char in[48],out[48],a[0x208],b[0x208],material[0xa0];} C43Entry;
static C43Entry c43Table[16];static unsigned c43Epoch,c43Active,c43Hits,c43Eligible,c43Miss,c43Mismatch;
static unsigned long long c43Saved;
static void(*c43Kernel)(void*,void*,float,int);
static void c43_copy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;for(unsigned i=0;i<n;i++)a[i]=b[i];}
static int c43_equal(const void*a,const void*b,unsigned n){const unsigned char*x=a,*y=b;for(unsigned i=0;i<n;i++)if(x[i]!=y[i])return 0;return 1;}
static void c43_begin(unsigned enabled){if(++c43Epoch==0){for(unsigned i=0;i<16;i++)c43Table[i].epoch=0;c43Epoch=1;}c43Active=enabled;c43Hits=c43Eligible=c43Miss=c43Mismatch=0;c43Saved=0;}
static void c43_pair(void*w,void*p,float dt,int thread){
 if(thread||!C43_MAIN()||!c43Active){c43Kernel(w,p,dt,thread);return;}
 unsigned char*in=p;const void*a=*(void**)in,*b=*(void**)(in+8),*m=*(void**)(in+24);
 if(*(void**)(in+16)||!C43_TARGET(a,b)){c43Kernel(w,p,dt,thread);return;}
 const unsigned char*sa=*(void**)((const unsigned char*)a+0x200),*sb=*(void**)((const unsigned char*)b+0x200);
 unsigned ta=*(const unsigned*)(sa+0x68),tb=*(const unsigned*)(sb+0x68);
 if(!((ta==5&&tb==9)||(ta==9&&tb==5))){c43Kernel(w,p,dt,thread);return;}
 const unsigned char*tree=ta==9?sa:sb;
 if(*(const void**)(tree+0x98)){c43Kernel(w,p,dt,thread);return;}
 c43Eligible++;unsigned hash=(unsigned)(((unsigned long long)a>>4)^((unsigned long long)b>>7))&15;C43Entry*slot=0;
 for(unsigned i=0;i<4;i++){
  C43Entry*q=c43Table+((hash+i)&15);if(q->epoch!=c43Epoch){slot=q;break;}
  if(!c43_equal(q->in,in,32)||!c43_equal(q->in+40,in+40,8))continue;
  if(!c43_equal(q->a,a,0x208)||!c43_equal(q->b,b,0x208)||!c43_equal(q->material,m,0xa0))continue;
  c43Hits++;
  if(C43_SHADOW){unsigned long long t=C43_NOW();c43Kernel(w,p,dt,thread);c43Saved+=C43_NOW()-t;if(!c43_equal(q->out,in,32)||!c43_equal(q->out+40,in+40,8))c43Mismatch++;}
  else {c43_copy(in,q->out,32);c43_copy(in+40,q->out+40,8);}
  return;
 }
 unsigned char saved[48];c43_copy(saved,p,48);unsigned long long t=C43_NOW();c43Kernel(w,p,dt,thread);unsigned long long cost=C43_NOW()-t;c43Miss++;
 if(slot&&cost>=C43_MIN_TICKS&&*(unsigned*)(in+40)==0&&*(void**)(in+32)==*(void**)(saved+32)){
  slot->epoch=c43Epoch;c43_copy(slot->in,saved,48);c43_copy(slot->out,in,48);c43_copy(slot->a,a,0x208);c43_copy(slot->b,b,0x208);c43_copy(slot->material,m,0xa0);
 }
}
