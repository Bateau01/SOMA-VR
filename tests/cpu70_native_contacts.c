#include <windows.h>
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
static int(*nativeCollide)(void*,int,void*,const float*,void*,const float*,float*,float*,float*,int);
static void*(*createWorld)(void*,void*);static void(*destroyWorld)(void*);
static void*(*createBox)(void*,float,float,float,int,const float*);
static void*(*createSphere)(void*,float,float,float,int,const float*);
static u8 original(void*world,void*av,const float*am,void*bv,const float*bm,void*dv,int limit,u8 correct,int thread){
 Shape*a=av,*b=bv;H508CollideData*d=dv;d->count=0;int na=a->type==7?a->count:1,nb=b->type==7?b->count:1;float ma[16],mb[16];for(int i=0;i<4;i++)for(int j=0;j<4;j++){ma[i*4+j]=am[j*4+i];mb[i*4+j]=bm[j*4+i];}
 for(int i=0;i<na&&d->count<limit;i++)for(int j=0;j<nb&&d->count<limit;j++){
  Shape*ca=a->type==7?a->children[i]:a;Shape*cb=b->type==7?b->children[j]:b;float points[96],normals[96],depth[32];primitiveCalls++;
  int n=nativeCollide(world,limit-d->count,ca->collision,ma,cb->collision,mb,points,normals,depth,thread);if(n>limit-d->count)n=limit-d->count;
  for(int q=0;q<n;q++){H508Contact*c=d->begin+d->count++;memset(c,0,sizeof(*c));memcpy(c->point,points+q*3,12);memcpy(c->normal,normals+q*3,12);c->depth=depth[q];if(correct&&a->flip){float v[3]={c->point[0]-am[3],c->point[1]-am[7],c->point[2]-am[11]};if(h10_dot(v,c->normal)>0)for(int k=0;k<3;k++)c->normal[k]=-c->normal[k];}}
 }
 return d->count>0;
}
#define p_h508CheckShapeCollision original
#include "../source/ark_query_ct.inc"
static void* vt[9];static Shape target,source,items[168],fingers[24];
static void init(Shape* s,float x){memset(s,0,sizeof(*s));s->vt=vt;s->collision=s;for(int k=0;k<3;k++){s->lo[k]=-0.025f;s->hi[k]=0.025f;}s->lo[0]+=x;s->hi[0]+=x;}

int main(void){
 SetDllDirectoryA("D:\\SteamLibrary\\steamapps\\common\\SOMA");HMODULE dll=LoadLibraryA("Newton.dll");if(!dll)return 10;
#define LOAD(v,n) v=(void*)GetProcAddress(dll,n);if(!v)return 11
 LOAD(nativeCollide,"NewtonCollisionCollide");LOAD(createWorld,"NewtonCreate");LOAD(destroyWorld,"NewtonDestroy");LOAD(createBox,"NewtonCreateBox");LOAD(createSphere,"NewtonCreateSphere");LOAD(g_ctShapeBounds,"NewtonCollisionCalculateAABB");LOAD(g_ctShapeInfo,"NewtonCollisionGetInfo");LOAD(g_ctShapeSupport,"NewtonCollisionSupportVertex");
 void*w=createWorld(0,0);vt[7]=child;vt[8]=count;init(&source,0);init(&target,0);source.type=7;source.count=8;target.type=7;target.count=24;
 float id[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
 for(int i=0;i<8;i++){init(fingers+i,0);source.children[i]=fingers+i;float m[16];memcpy(m,id,64);m[12]=(i%4-1.5f)*.025f;m[14]=(i/4)*.04f;fingers[i].collision=createBox(w,.03f,.04f,.05f,0,m);}
 for(int j=0;j<24;j++){init(items+j,0);target.children[j]=items+j;float m[16];memcpy(m,id,64);m[12]=(j%6-2.5f)*.04f;m[14]=(j/6-1.5f)*.04f;items[j].collision=j%2?createBox(w,.025f,.04f,.05f,0,m):createSphere(w,.025f,.025f,.025f,0,m);}
 source.collision=fingers[0].collision;unsigned hits=0,clear=0,errors=0,refCalls=0,optCalls=0;
 for(int t=0;t<1800;t++){
  float am[16],bm[16];memcpy(am,id,64);memcpy(bm,id,64);float a=t*.071f;am[0]=am[10]=cosf(a);am[2]=sinf(a);am[8]=-sinf(a);am[3]=(t%31-15)*.021f;am[7]=(t%11-5)*.019f;am[11]=(t%17-8)*.017f;
  a=t*.043f;bm[0]=bm[10]=cosf(a);bm[2]=sinf(a);bm[8]=-sinf(a);bm[3]=(t%3)*.013f;
  source.type=t%3?7:0;source.flip=t%2;int limit=(t%3==0)?1:(t%3==1)?8:32;
  H508Contact rc[32]={0},oc[32]={0};H508CollideData rd={0},od={0};rd.begin=rc;rd.end=rd.cap=rc+32;od.begin=oc;od.end=od.cap=oc+32;
  primitiveCalls=0;u8 r=original(w,&source,am,&target,bm,&rd,limit,1,0);refCalls+=primitiveCalls;
  g_ctQueryCache.shape=0;primitiveCalls=0;u8 o=ct_check_shape_collision(w,&source,am,&target,bm,&od,limit,1,0);optCalls+=primitiveCalls;
  int same=r==o&&rd.count==od.count;
  if(same)for(int i=0;i<rd.count;i++)for(int k=0;k<7;k++)if(fabsf((&rc[i].point[0])[k]-(&oc[i].point[0])[k])>.00001f)same=0;
  if(!same){errors++;if(errors<6)printf("MISMATCH t=%d contact=%d/%d\n",t,rd.count,od.count);}if(r)hits++;else clear++;
 }
 printf("NATIVE contact comparisons=1800 hit=%u clear=%u mismatch=%u primitive_calls=%u/%u\n",hits,clear,errors,refCalls,optCalls);destroyWorld(w);return errors?1:0;
}
