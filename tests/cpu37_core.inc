/* Private synchronous native-job scheduling. No native descriptor mutation. */
#ifndef C37_MIN_PAIRS
#define C37_MIN_PAIRS 32
#endif
typedef unsigned long long C37Tick;
typedef struct C37Context C37Context;
typedef struct {void**vt;int index,pad,stride,limit,mode;float dt;void*world;C37Context*ctx;} C37Job;
struct C37Context {unsigned mx,n,requested,count;C37Tick start,queued,joined,begin[8],end[8];};
static void(*c37Execute)(void*);static void(*c37Queue)(void*,void*);static void(*c37Join)(void*);
static unsigned c37_getmx(void){unsigned x;__asm__ volatile("stmxcsr %0":"=m"(x));return x;}
static void c37_setmx(unsigned x){__asm__ volatile("ldmxcsr %0"::"m"(x));}
static void c37_worker(void*p){C37Job*j=p;C37Context*c=j->ctx;unsigned old=c37_getmx();c37_setmx(c->mx);c->begin[j->index]=C37_NOW();c37Execute(j);c->end[j->index]=C37_NOW();c37_setmx(old);}
static void c37_job(void*p){
 C37Job*j=p;if(!C37_MAIN()||j->mode!=1||j->stride!=1||j->index!=0){c37Execute(p);return;}
 C37Context c={0};c.count=(unsigned)j->limit;c.requested=C37_MODE(j);c.mx=c37_getmx();c.start=C37_NOW();
 int threads=*(int*)((unsigned char*)j->world+0x2250);
 if(c.requested&&j->limit>=C37_MIN_PAIRS&&threads>=2&&threads<=8){c.n=c.requested;if(c.n>(unsigned)threads)c.n=threads;if(c.n>c.count)c.n=c.count;}
 if(!c.n){c37Execute(p);c.queued=c.start;c.joined=C37_NOW();C37_REPORT(&c);return;}
 C37Job jobs[8];void*vt[1]={(void*)c37_worker};
 for(unsigned i=0;i<c.n;i++){C37Job*q=jobs+i;q->vt=vt;q->index=(int)i;q->pad=0;q->stride=(int)c.n;q->limit=((j->limit+(int)c.n-1-(int)i)/(int)c.n)*(int)c.n;q->mode=1;q->dt=j->dt;q->world=j->world;q->ctx=&c;}
 for(unsigned i=0;i<c.n;i++)c37Queue((unsigned char*)j->world+0x2250,jobs+i);
 c.queued=C37_NOW();c37Join((unsigned char*)j->world+0x2250);c.joined=C37_NOW();C37_REPORT(&c);
}
