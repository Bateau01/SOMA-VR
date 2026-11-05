#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cmath>
using P=void*;
using i32=int;using u8=unsigned char;using u32=unsigned;
static const void*(*p_h14GetCollision)(const void*);static void(*p_h14GetMatrix)(const void*,float*);static int h20_mem_readable(void*p,int){return p!=nullptr;}
using JBRecoveryFaces=int(*)(const void*,const float*,const float*,const float**,int*,int*,int*,int,int*);static JBRecoveryFaces jbRecoveryFaces;static void(*jbRecoveryBounds)(const void*,const float*,float*,float*);
float (*p_h43CollisionRayCast)(const void*,const float*,const float*,float*,int*);
int h9_good(float f,float bound){return std::isfinite(f)&&fabsf(f)<bound;}
void h14_transform_point(const float*m,const float*p,float*out){for(int j=0;j<3;j++)out[j]=m[j]*p[0]+m[4+j]*p[1]+m[8+j]*p[2]+m[12+j];}
void h14_rigid_inverse(const float*m,float*out){memset(out,0,64);out[15]=1;for(int i=0;i<3;i++)for(int j=0;j<3;j++)out[i*4+j]=m[j*4+i];for(int j=0;j<3;j++)out[12+j]=-(out[j]*m[12]+out[4+j]*m[13]+out[8+j]*m[14]);}
#include "jb_recovery_endpoint_guard.inc"
static i32 jb_recovery_tree_empty(const void* body,const float* lo,const float* hi){
 // Broadphase leaves can include nearby bodies outside the query. Refine by
 // their current native collision bounds before considering shape-specific data.
 float bodyM[16],bodyLo[4],bodyHi[4];p_h14GetMatrix(body,bodyM);
 const void* bodyCollision=p_h14GetCollision(body);if(!bodyCollision)return 0;
 jbRecoveryBounds(bodyCollision,bodyM,bodyLo,bodyHi);
 i32 apart=0;for(i32 a=0;a<3;a++){
  if(!h9_good(bodyLo[a],100000)||!h9_good(bodyHi[a],100000)||bodyLo[a]>bodyHi[a])return 0;
  if(bodyHi[a]<lo[a]||bodyLo[a]>hi[a])apart=1;
 }
 if(apart)return 1;

 const u8* c=(const u8*)p_h14GetCollision(body);
 if(!c||!jbRecoveryFaces||!h20_mem_readable((void*)c,0xa0)||*(const u32*)(c+0x68)!=9||*(const void**)(c+0x98))return 0;
 const float* offset=(const float*)(c+0x10);
 for(i32 i=0;i<16;i++)if(!h9_good(offset[i],2)||(offset[i]-(i%5==0?1.f:0.f)>.00001f||offset[i]-(i%5==0?1.f:0.f)<-.00001f))return 0;
 float bm[16],inverse[16];p_h14GetMatrix(body,bm);h14_rigid_inverse(bm,inverse);
 float localLo[3]={1e20f,1e20f,1e20f},localHi[3]={-1e20f,-1e20f,-1e20f};
 for(i32 corner=0;corner<8;corner++){
  float wp[3],lp[3];for(i32 a=0;a<3;a++)wp[a]=(corner&(1<<a))?hi[a]:lo[a];
  h14_transform_point(inverse,wp,lp);
  for(i32 a=0;a<3;a++){if(!h9_good(lp[a],100000))return 0;if(lp[a]<localLo[a])localLo[a]=lp[a];if(lp[a]>localHi[a])localHi[a]=lp[a];}
 }
 const float* vertices=0;i32 count=0,stride=0,indices[96],attributes[96];
 i32 faces=jbRecoveryFaces(c,localLo,localHi,&vertices,&count,&stride,indices,96,attributes);
 if(faces==0)return 1;
 // The API returns triangles from intersected tree leaves, including nearby
 // triangles outside the box. A full output buffer is ambiguous: reject it.
 if(faces<0||faces>=32||!vertices||count<=0||count>1000000||stride!=12)return 0;
 for(i32 face=0;face<faces;face++){
  float a[3]={1e20f,1e20f,1e20f},b[3]={-1e20f,-1e20f,-1e20f};
  for(i32 v=0;v<3;v++){
   i32 index=indices[face*3+v];if(index<0||index>=count)return 0;
   const float* p=(const float*)((const u8*)vertices+(u32)index*(u32)stride);
   for(i32 k=0;k<3;k++){if(!h9_good(p[k],100000))return 0;if(p[k]<a[k])a[k]=p[k];if(p[k]>b[k])b[k]=p[k];}
  }
  i32 apart=0;for(i32 k=0;k<3;k++)if(b[k]<localLo[k]||a[k]>localHi[k])apart=1;
  if(!apart)return 0;
 }
 return 1;
}
static int hits;static const void* bodies[256];static void nearBody(const void*b,void*){if(hits<256)bodies[hits++]=b;}
int main(int argc,char**argv){
 if(argc!=2)return 2;setbuf(stdout,nullptr);auto dll=LoadLibraryA(argv[1]);if(!dll)return 3;
#define API(n,t) auto n=reinterpret_cast<t>(GetProcAddress(dll,#n));if(!n)return 4;
 API(NewtonCreate,P(*)(P,P));API(NewtonDestroy,void(*)(P));
 API(NewtonCollisionCalculateAABB,void(*)(const void*,const float*,float*,float*));jbRecoveryBounds=NewtonCollisionCalculateAABB;
 API(NewtonBodyGetCollision,const void*(*)(const void*));p_h14GetCollision=NewtonBodyGetCollision;
 API(NewtonBodyGetMatrix,void(*)(const void*,float*));p_h14GetMatrix=NewtonBodyGetMatrix;
 API(NewtonTreeCollisionGetVertexListIndexListInAABB,JBRecoveryFaces);jbRecoveryFaces=NewtonTreeCollisionGetVertexListIndexListInAABB;
 API(NewtonCreateBody,P(*)(P,P,const float*));
 API(NewtonDestroyBody,void(*)(P,P));
 API(NewtonWorldForEachBodyInAABBDo,void(*)(P,const float*,const float*,void(*)(const void*,void*),void*));
 API(NewtonCreateBox,P(*)(P,float,float,float,int,const float*));
 API(NewtonCreateTreeCollision,P(*)(P,int));
 API(NewtonTreeCollisionBeginBuild,void(*)(P));
 API(NewtonTreeCollisionAddFace,void(*)(P,int,const float*,int,int));
 API(NewtonTreeCollisionEndBuild,void(*)(P,int));
 API(NewtonReleaseCollision,void(*)(P,P));
 API(NewtonCollisionPointDistance,int(*)(P,const float*,P,const float*,float*,float*,int));
 API(NewtonCollisionRayCast,float(*)(P,const float*,const float*,float*,int*));
 p_h43CollisionRayCast=reinterpret_cast<decltype(p_h43CollisionRayCast)>(NewtonCollisionRayCast);
 P world=NewtonCreate(nullptr,nullptr);float matrix[16]={};matrix[0]=matrix[5]=matrix[10]=matrix[15]=1;
 P shapes[4]={NewtonCreateBox(world,.002f,2,2,1,nullptr),NewtonCreateBox(world,2,2,2,2,nullptr),NewtonCreateTreeCollision(world,3),NewtonCreateTreeCollision(world,4)};
 float face[]={0,-1,-1,0,-1,1,0,1,1,0,1,-1};
 NewtonTreeCollisionBeginBuild(shapes[2]);NewtonTreeCollisionAddFace(shapes[2],4,face,12,0);NewtonTreeCollisionEndBuild(shapes[2],1);NewtonTreeCollisionBeginBuild(shapes[3]);for(int side=-1;side<=1;side+=2){float wall[]={float(side*4),-5,-5,float(side*4),-5,5,float(side*4),5,5,float(side*4),5,-5};NewtonTreeCollisionAddFace(shapes[3],4,wall,12,0);}NewtonTreeCollisionEndBuild(shapes[3],1);
 for(int shape=0;shape<3;shape++)for(int test=0;test<3;test++){
  float p[4]={test==0?0:test==1?.4f:-.4f,0,0,0},c[4]={1e30f,1e30f,1e30f,0},n[4]={};
  int outside=NewtonCollisionPointDistance(world,p,shapes[shape],matrix,c,n,0);
  float a[4]={-.3f,0,0,0},b[4]={.3f,0,0,0};int id=0;
  float forward=NewtonCollisionRayCast(shapes[shape],a,b,n,&id),reverse=NewtonCollisionRayCast(shapes[shape],b,a,n,&id);
  printf("shape %d point %.3f outside %d contact %.6g %.6g %.6g forward %.6g reverse %.6g\n",shape,p[0],outside,c[0],c[1],c[2],forward,reverse);
 }
 int checks=0,failures=0;
 for(int shape=0;shape<4;shape++)for(int pose=0;pose<3;pose++)for(int outside=0;outside<2;outside++){
  float m[16]={};m[0]=m[5]=m[10]=m[15]=1;
  if(pose){m[12]=.4f;m[13]=-.3f;m[14]=.7f;}
  if(pose==2){m[0]=m[10]=0;m[2]=-1;m[8]=1;}
  float local[3]={outside?2.f:0.f,0,0},center[3],lo[3],hi[3];h14_transform_point(m,local,center);
  for(int a=0;a<3;a++){lo[a]=center[a]-.04f;hi[a]=center[a]+.04f;}
  P body=NewtonCreateBody(world,shapes[shape],m);hits=0;
  NewtonWorldForEachBodyInAABBDo(world,lo,hi,nearBody,nullptr);
  printf("shapeMeta %d kind %u debug %p offset",shape,*(unsigned*)((char*)shapes[shape]+0x68),*(void**)((char*)shapes[shape]+0x98));for(int j=0;j<16;j++)printf(" %.4g",((float*)((char*)shapes[shape]+0x10))[j]);puts("");int clear=1;for(int i=0;i<hits;i++)if(!jb_recovery_tree_empty(bodies[i],lo,hi))clear=0;NewtonDestroyBody(world,body);++checks;if(clear!=(shape==3?1:outside))++failures;
  printf("guard shape %d pose %d outside %d clear %d\n",shape,pose,outside,clear);
 }
 for(auto s:shapes)NewtonReleaseCollision(world,s);NewtonDestroy(world);printf("guard checks %d failures %d\n",checks,failures);return failures?1:0;
}
