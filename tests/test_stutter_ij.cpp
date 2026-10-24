
#include <cstdio>
#include <cstring>
#undef NDEBUG
#include <cassert>
using u64=unsigned long long;using u32=unsigned;using i32=int;
#define H5755EG_P_COUNT 14
u32 g_frameCounter,g_h14PhysicsSteps,g_h5755bhPresentationState=1,g_h5750vPrimeWrapperActive,g_h522PairUsed[2];void*g_h14GripBody[2];float g_lastStickX[2],g_lastStickY[2];long long g_h5755egQpcFreq=10000000;
u32 thread(){return 1;}auto p_h5755egGetCurrentThreadId=thread;int writes=0;bool fail=false;
void h5755eg_prof_try_init(){}void ext_Log(const char*,...){}
int make_sibling_path(char*p,unsigned n,const char*s){snprintf(p,n,"%s",s);return 1;}
void*ext_fopen(const char*p,const char*m){return fail?nullptr:fopen(p,m);}int ext_fclose(void*p){return fclose((FILE*)p);}u64 ext_fwrite(const void*p,u64 a,u64 b,void*f){writes++;return fwrite(p,a,b,(FILE*)f);}
#include "../source/stutter_ej.inc"
int main(){u64 ticks[14]={42};s26ej_trace_push(1,1,ticks,0);assert(g_s26ejTraceCount==0&&writes==0);assert(s26ej_trace_command(0));for(u32 i=0;i<S26EJ_TRACE_CAP+10;i++){g_frameCounter=i;s26ej_trace_push(1,i,ticks,0);}assert(g_s26ejTraceCount==S26EJ_TRACE_CAP&&writes==0);assert(s26ej_trace_command(1));assert(!s26ej_trace_command(2)&&s26ej_trace_command(3));FILE*f=fopen("hpl3vr_stutter.bin","rb");u64 h[8];assert(fread(h,64,1,f)==1&&h[4]==S26EJ_TRACE_CAP&&h[2]==sizeof(S26EJTrace));S26EJTrace row;assert(fread(&row,sizeof(row),1,f)==1&&row.frame==10&&row.ticks[0]==42);fseek(f,0,SEEK_END);assert(ftell(f)==64+S26EJ_TRACE_CAP*sizeof(row));fclose(f);assert(s26ej_trace_command(0));assert(g_s26ejTraceCount==0);fail=true;assert(!s26ej_trace_command(1)&&!s26ej_trace_command(3));puts("PASS OFF, START, bounded wrap, no hot-path writes, chronological SAVE, restart and write failure");}
