#include <stdio.h>
#include <string.h>
#include <stdint.h>
typedef unsigned char u8;typedef unsigned u32;typedef int i32;
typedef u8 (*PFN_H508_CheckShapeCollision)(void*,void*,const float*,void*,const float*,void*,i32,u8,i32);
static PFN_H508_CheckShapeCollision p_h508CheckShapeCollision;
static struct {void*shape;}g_ctQueryCache;
static u32 tid=10,nativeCalls,optCalls,createCalls,enableCalls;
static u32 thread_id(void){return tid;}
static void*ext_GetModuleHandleA(const char*s){(void)s;return (void*)1;}
static void*ext_GetProcAddress(void*k,const char*s){(void)k;(void)s;return thread_id;}
static int h20_mem_executable(void*p){return p!=0;}
static u8 original(void*w,void*a,const float*am,void*b,const float*bm,void*d,i32 l,u8 c,i32 t){(void)w;(void)a;(void)am;(void)b;(void)bm;(void)d;(void)l;(void)c;(void)t;nativeCalls++;return 7;}
static int ext_MH_CreateHook(void*t,void*d,void**o){(void)t;(void)d;createCalls++;*o=original;return 0;}
static int ext_MH_EnableHook(void*t){(void)t;enableCalls++;return 0;}
static u8 ct_check_shape_collision(void*w,void*a,const float*am,void*b,const float*bm,void*d,i32 l,u8 c,i32 t){(void)w;(void)a;(void)am;(void)b;(void)bm;(void)d;(void)l;(void)c;(void)t;optCalls++;return 9;}
#define CPU_HELD_QUERY 1
#include "../source/cpu_held_query.inc"
#define C(x) do{checks++;if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
int main(void){int checks=0;u8 sig[]={0x48,0x8b,0xc4,0x4c,0x89,0x48,0x20,0x48,0x89,0x50,0x10,0x48,0x89,0x48,0x08,0x55};
 C(!c70_held_begin());p_h508CheckShapeCollision=(void*)sig;c70_held_install();C(c70HeldReady);C(p_h508CheckShapeCollision==original);c70_held_install();C(createCalls==1&&enableCalls==1);
 for(int cycle=0;cycle<100;cycle++){
 C(c70_held_pair(0,0,0,0,0,0,32,1,0)==7);g_ctQueryCache.shape=(void*)1;u32 a=c70_held_begin();C(a&&c70HeldDepth==1&&c70HeldOwner==10);C(!g_ctQueryCache.shape);C(c70_held_pair(0,0,0,0,0,0,32,1,0)==9);
 u32 b=c70_held_begin();C(b&&c70HeldDepth==2);tid=11;C(!c70_held_begin());C(c70_held_pair(0,0,0,0,0,0,32,1,0)==7);c70_held_end(0);C(c70HeldDepth==2);tid=10;c70_held_end(b);C(c70HeldOwner==10&&c70HeldDepth==1);g_ctQueryCache.shape=(void*)3;c70_held_end(a);C(!c70HeldOwner&&!c70HeldDepth&&!g_ctQueryCache.shape);
 }
 C(nativeCalls==200&&optCalls==100);c70HeldReady=c70HeldAttempted=0;sig[0]=0;c70_held_install();C(!c70HeldReady);C(createCalls==1);C(!c70_held_begin());printf("PASS %d scope/thread/nesting/cache/signature assertions\n",checks);return 0;
}
