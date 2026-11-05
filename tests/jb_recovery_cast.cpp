// Native Newton capability check only; isolated world, no game hand or object writes.
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cstdlib>
using P=void*;
struct Hit{float p[4],n[4],sn[4],depth;int id;P body;};
static_assert(sizeof(Hit)==64);
using Filter=unsigned(*)(P,P,P);
unsigned include(P,P,P){return 1;}
void matrix(float*m,float x,float y,float z){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;m[12]=x;m[13]=y;m[14]=z;}
int main(int argc,char**argv){
 if(argc!=4)return 2;setbuf(stdout,nullptr);auto dll=LoadLibraryA(argv[1]);if(!dll)return 3;
#define API(n,t) auto n=reinterpret_cast<t>(GetProcAddress(dll,#n));if(!n)return 4;
 API(NewtonCreate,P(*)(P,P));API(NewtonDestroy,void(*)(P));
 API(NewtonCreateBox,P(*)(P,float,float,float,int,const float*));
 API(NewtonCreateCompoundCollision,P(*)(P,int,P*,int));
 API(NewtonCreateBody,P(*)(P,P,const float*));
 API(NewtonReleaseCollision,void(*)(P,P));
 API(NewtonWorldConvexCast,int(*)(P,const float*,const float*,P,float*,P,Filter,Hit*,int,int));
 API(NewtonCollisionCalculateAABB,void(*)(P,const float*,float*,float*));
 API(NewtonCollisionCollide,int(*)(P,int,P,const float*,P,const float*,float*,float*,float*,int));
 P world=NewtonCreate(nullptr,nullptr);float m[16];matrix(m,.2f,0,0);
 P wall=NewtonCreateBox(world,float(atof(argv[3])),2,2,1,nullptr);P body=NewtonCreateBody(world,wall,m);
 P child[2];matrix(m,0,.04f,0);child[0]=NewtonCreateBox(world,.06f,.04f,.08f,2,m);
 matrix(m,0,-.04f,0);child[1]=NewtonCreateBox(world,.06f,.04f,.08f,3,m);
 P compound=NewtonCreateCompoundCollision(world,2,child,4);
 P test=strcmp(argv[2],"compound")==0?compound:child[0];int errors=0;
 for(int scenario=0;scenario<3;++scenario){
  matrix(m,scenario==2?.2f:0,0,0);float end[3]={scenario==0?.4f:scenario==1?-.4f:.4f,0,0};
  float lo[4],hi[4];NewtonCollisionCalculateAABB(test,m,lo,hi);
  Hit hit[8]{};float fraction=1;
  printf("begin %s scenario %d bounds %.5f %.5f\n",argv[2],scenario,lo[0],hi[0]);
  float wallM[16],points[96],normals[96],depth[32];matrix(wallM,.2f,0,0);
  int overlap=NewtonCollisionCollide(world,32,test,m,wall,wallM,points,normals,depth,0);
  int count=NewtonWorldConvexCast(world,m,end,test,&fraction,nullptr,include,hit,8,0);
  printf("result count %d fraction %.6f wall %d\n",count,fraction,count?hit[0].body==body:0);
  printf("start overlap %d\n",overlap);
  float reverseM[16],reverseEnd[3]={m[12],m[13],m[14]},reverseFraction=1;
  matrix(reverseM,end[0],end[1],end[2]);Hit reverseHit[8]{};
  int reverse=NewtonWorldConvexCast(world,reverseM,reverseEnd,test,&reverseFraction,nullptr,include,reverseHit,8,0);
  printf("reverse count %d fraction %.6f\n",reverse,reverseFraction);
  // Separate overlap can miss deep thin-wall containment too. Both directions
  // must be clear before a recovery corridor can be treated as unobstructed.
  if((scenario==2&&reverse==0)||(scenario==1&&reverse!=0)||(scenario!=2&&overlap!=0))++errors;
  if(!std::isfinite(fraction)||(scenario==0&&(!count||hit[0].body!=body||fraction<=0||fraction>=1))||(scenario==1&&count))++errors;
  // Initial overlap is reported for investigation, never assumed to be clear.
 }
 NewtonReleaseCollision(world,compound);for(auto c:child)NewtonReleaseCollision(world,c);
 NewtonReleaseCollision(world,wall);NewtonDestroy(world);
 printf("errors %d; capability check, not recovery validation\n",errors);return errors?1:0;
}
