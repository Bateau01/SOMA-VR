#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <stddef.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
typedef struct {u8 pad[24];float point[3],normal[3],depth;u32 tail;} H508Contact;
typedef struct {u8 pad[24];H508Contact *begin,*end,*cap;u8 pad2[8];i32 count;u32 tail;} H508CollideData;
typedef struct Shape {void** vt;u8 pad[20];i32 type;u8 pad2[64];u8 flip;u8 pad3[175];void* collision;int count;struct Shape* children[256];float lo[3],hi[3];} Shape;
_Static_assert(offsetof(Shape,type)==0x1c,"shape type");
_Static_assert(offsetof(Shape,flip)==0x60,"shape flag");
_Static_assert(offsetof(Shape,collision)==0x110,"shape collision");
static u32 g_h14PhysicsSteps=1,primitiveCalls,boundsCalls;
static int h20_mem_readable(const void* p,int n){(void)n;return p!=0;}
static int h25_soma_code_ptr(const void* p){return p!=0;}
static float h9_abs(float f){return fabsf(f);}
static int h9_good(float f,float max){return isfinite(f)&&fabsf(f)<max;}
static float h10_dot(const float* a,const float* b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void h10_copy_f(float* a,const float* b,int n){memcpy(a,b,n*sizeof(float));}
static void zero_bytes(void* p,size_t n){memset(p,0,n);}
static void* ext_GetModuleHandleA(const char* s){(void)s;return 0;}
static void* ext_GetProcAddress(void* p,const char* s){(void)p;(void)s;return 0;}
static int __attribute__((ms_abi)) count(void* p){return ((Shape*)p)->count;}
static void* __attribute__((ms_abi)) child(void* p,int i){return ((Shape*)p)->children[i];}
static void __attribute__((ms_abi)) bounds(const void* p,const float* m,float* lo,float* hi){
    const Shape* s=p;boundsCalls++;
    for(int i=0;i<3;i++){lo[i]=s->lo[i]+m[12+i];hi[i]=s->hi[i]+m[12+i];}
}
static u8 original(void* world,void* av,const float* am,void* bv,const float* bm,void* dv,int limit,u8 correct,int thread){
    (void)world;(void)thread;Shape *a=av,*b=bv;H508CollideData* d=dv;d->count=0;
    int na=a->type==7?a->count:1,nb=b->type==7?b->count:1;
    for(int i=0;i<na&&d->count<limit;i++)for(int j=0;j<nb&&d->count<limit;j++){
        Shape* ca=a->type==7?a->children[i]:a;Shape* cb=b->type==7?b->children[j]:b;primitiveCalls++;
        int hit=1;float depth=999;
        for(int k=0;k<3;k++){
            float alo=ca->lo[k]+am[k*4+3],ahi=ca->hi[k]+am[k*4+3],blo=cb->lo[k]+bm[k*4+3],bhi=cb->hi[k]+bm[k*4+3];
            float dep=fminf(ahi,bhi)-fmaxf(alo,blo);if(dep<0)hit=0;if(dep<depth)depth=dep;
        }
        if(hit){H508Contact* c=&d->begin[d->count++];memset(c,0,sizeof(*c));c->depth=depth;c->normal[0]=1;
            for(int k=0;k<3;k++)c->point[k]=cb->lo[k]+bm[k*4+3];
            if(correct&&a->flip&&c->point[0]>am[3])for(int k=0;k<3;k++)c->normal[k]=-c->normal[k];
        }
    }
    return d->count>0;
}
#define p_h508CheckShapeCollision original
#include "../source/ark_query_ct.inc"
static void* vt[9];static Shape target,source,items[168],fingers[24];
static void init(Shape* s,float x){memset(s,0,sizeof(*s));s->vt=vt;s->collision=s;for(int k=0;k<3;k++){s->lo[k]=-0.025f;s->hi[k]=0.025f;}s->lo[0]+=x;s->hi[0]+=x;}
int main(void){
    vt[7]=(void*)child;vt[8]=(void*)count;g_ctShapeBounds=bounds;
    init(&target,0);target.type=7;target.count=168;
    for(int j=0;j<168;j++){init(items+j,(j-84)*0.02f);target.children[j]=items+j;}
    init(&source,0);source.type=7;source.count=24;source.flip=1;
    for(int i=0;i<24;i++){init(fingers+i,(i-12)*0.012f);source.children[i]=fingers+i;}
    float am[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},bm[16];memcpy(bm,am,sizeof(bm));
    u32 refCalls=0,optCalls=0;int checks=0;
    for(int step=0;step<400;step++){
        g_h14PhysicsSteps=1+step/3;am[3]=(step%41-20)*0.045f;am[7]=(step%7)*0.018f;bm[3]=(step%3)*0.05f;
        source.type=(step%2)?7:0;source.flip=(step%3)?1:0;int limit=1+(step%16);
        H508Contact rc[32]={0},oc[32]={0};H508CollideData rd={0},od={0};rd.begin=rc;rd.end=rd.cap=rc+32;od.begin=oc;od.end=od.cap=oc+32;
        primitiveCalls=0;u8 r=original((void*)1,&source,am,&target,bm,&rd,limit,1,0);refCalls+=primitiveCalls;
        primitiveCalls=0;u8 o=ct_check_shape_collision((void*)1,&source,am,&target,bm,&od,limit,1,0);optCalls+=primitiveCalls;
        if(r!=o||rd.count!=od.count||memcmp(rc,oc,rd.count*sizeof(*rc))){printf("FAIL step %d count %d/%d\n",step,rd.count,od.count);for(int q=0;q<rd.count;q++)printf("%d: %f %f %f / %f %f %f\n",q,rc[q].point[0],rc[q].normal[0],rc[q].depth,oc[q].point[0],oc[q].normal[0],oc[q].depth);return 1;}checks++;
    }
    if(optCalls>=refCalls)return 2;
    for(int step=0;step<100;step++){
        am[3]=(step%17-8)*.032f;am[7]=0;source.type=0;
        H508Contact rc[32]={0},oc[32]={0};H508CollideData rd={0},od={0};rd.begin=rc;rd.end=rd.cap=rc+32;od.begin=oc;od.end=od.cap=oc+32;
        u8 ref=original((void*)1,&source,am,&target,bm,&rd,1,1,0);
        ct_held_queries_begin();
        u8 hit=ct_held_shape_collision((void*)1,&source,am,&target,bm,&od,1,1,0);
        u32 calls=primitiveCalls,bc=boundsCalls;
        ct_held_queries_begin();
        for(int repeat=0;repeat<6;repeat++){
            od.count=-1;memset(oc,0,sizeof(oc));
            u8 again=ct_held_shape_collision((void*)1,&source,am,&target,bm,&od,1,1,0);
            if(hit!=ref||again!=ref||od.count!=rd.count||memcmp(rc,oc,rd.count*sizeof(*rc))||primitiveCalls!=calls||boundsCalls!=bc)return 3;
        }
        ct_held_queries_end();ct_held_queries_end();
        // The next scope must not reuse a previous solve's result.
        ct_held_queries_begin();calls=boundsCalls;
        ct_held_shape_collision((void*)1,&source,am,&target,bm,&od,1,1,0);
        ct_held_queries_end();if(boundsCalls==calls)return 4;
    }
    // First source/target children touch: neither remaining source bounds nor
    // remaining target bounds should be prepared after the first contact.
    source.type=7;source.flip=0;am[3]=-1.536f;am[7]=0;bm[3]=0;
    g_ctQueryCache.shape=0;boundsCalls=0;
    H508Contact ep[32]={0};H508CollideData ed={0};ed.begin=ep;ed.end=ed.cap=ep+32;
    if(!ct_check_shape_collision((void*)1,&source,am,&target,bm,&ed,1,0,0)||boundsCalls!=2)return 5;
    // A changed physics step must reprepare both visited bounds.
    g_h14PhysicsSteps++;boundsCalls=0;
    if(!ct_check_shape_collision((void*)1,&source,am,&target,bm,&ed,1,0,0)||boundsCalls!=2)return 6;
    // A changed target pose within the same step must not reuse old bounds.
    bm[3]=10;boundsCalls=0;
    if(ct_check_shape_collision((void*)1,&source,am,&target,bm,&ed,1,0,0))return 7;
    if(boundsCalls!=168+24)return 8;
    printf("PASS %d ordered-contact/cap/normal/cache cases; primitive tests %u -> %u\n",checks,refCalls,optCalls);
    puts("PASS lazy early exit: only two bounds; step and matrix invalidation");
    puts("PASS 100 nested solver-scope cases, 600 exact-repeat hits and 100 scope invalidations");
    return 0;
}
