#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cmath>
using P=void*;
using i32=int;
float (*p_h43CollisionRayCast)(const void*,const float*,const float*,float*,int*);
int h9_good(float f,float bound){return std::isfinite(f)&&fabsf(f)<bound;}
void h14_transform_point(const float*m,const float*p,float*out){for(int j=0;j<3;j++)out[j]=m[j]*p[0]+m[4+j]*p[1]+m[8+j]*p[2]+m[12+j];}
void h14_rigid_inverse(const float*m,float*out){memset(out,0,64);out[15]=1;for(int i=0;i<3;i++)for(int j=0;j<3;j++)out[i*4+j]=m[j*4+i];for(int j=0;j<3;j++)out[12+j]=-(out[j]*m[12]+out[4+j]*m[13]+out[8+j]*m[14]);}
#include "jb_recovery_endpoint_guard.inc"
int main(int argc,char**argv){
 if(argc!=2)return 2;setbuf(stdout,nullptr);auto dll=LoadLibraryA(argv[1]);if(!dll)return 3;
#define API(n,t) auto n=reinterpret_cast<t>(GetProcAddress(dll,#n));if(!n)return 4;
 API(NewtonCreate,P(*)(P,P));API(NewtonDestroy,void(*)(P));
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
 P shapes[3]={NewtonCreateBox(world,.002f,2,2,1,nullptr),NewtonCreateBox(world,2,2,2,2,nullptr),NewtonCreateTreeCollision(world,3)};
 float face[]={0,-1,-1,0,-1,1,0,1,1,0,1,-1};
 NewtonTreeCollisionBeginBuild(shapes[2]);NewtonTreeCollisionAddFace(shapes[2],4,face,12,0);NewtonTreeCollisionEndBuild(shapes[2],1);
 for(int shape=0;shape<3;shape++)for(int test=0;test<3;test++){
  float p[4]={test==0?0:test==1?.4f:-.4f,0,0,0},c[4]={1e30f,1e30f,1e30f,0},n[4]={};
  int outside=NewtonCollisionPointDistance(world,p,shapes[shape],matrix,c,n,0);
  float a[4]={-.3f,0,0,0},b[4]={.3f,0,0,0};int id=0;
  float forward=NewtonCollisionRayCast(shapes[shape],a,b,n,&id),reverse=NewtonCollisionRayCast(shapes[shape],b,a,n,&id);
  printf("shape %d point %.3f outside %d contact %.6g %.6g %.6g forward %.6g reverse %.6g\n",shape,p[0],outside,c[0],c[1],c[2],forward,reverse);
 }
 int checks=0,failures=0;
 for(int shape=0;shape<3;shape++)for(int pose=0;pose<3;pose++)for(int outside=0;outside<2;outside++){
  float m[16]={};m[0]=m[5]=m[10]=m[15]=1;
  if(pose){m[12]=.4f;m[13]=-.3f;m[14]=.7f;}
  if(pose==2){m[0]=m[10]=0;m[2]=-1;m[8]=1;}
  float local[3]={outside?2.f:0.f,0,0},center[3],lo[3],hi[3];h14_transform_point(m,local,center);
  for(int a=0;a<3;a++){lo[a]=center[a]-.04f;hi[a]=center[a]+.04f;}
  int clear=jb_recovery_endpoint_clear(shapes[shape],m,lo,hi);++checks;if(clear!=outside)++failures;
  printf("guard shape %d pose %d outside %d clear %d\n",shape,pose,outside,clear);
 }
 for(auto s:shapes)NewtonReleaseCollision(world,s);NewtonDestroy(world);printf("guard checks %d failures %d\n",checks,failures);return failures?1:0;
}
