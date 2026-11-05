typedef struct C37Context C37Context;
/* Event53: requested/actual jobs and held mask, identity=pair count. */
static u64 c37_now(void){u64 q=0;cpuCounter(&q);return q;}
static unsigned c37_mode(void){static const u8 order[8]={0,2,4,8,8,4,2,0};return order[(g_h14PhysicsSteps/60u)%8u];}
static u64 c37Counts[4];
#define C37_NOW() c37_now()
#define C37_MODE(j) c37_mode()
#define C37_MAIN() (cpuThreadId&&cpuThreadId()==cpuMainThread)
#define C37_REPORT(c) c37_report(c)
static void c37_report(C37Context*);
