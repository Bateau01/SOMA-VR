// Standalone Newton 2.36 probe. No HPL objects, callbacks or game modifications.
#include <windows.h>
#include <cstdio>
#include <cmath>
#include <cstring>
using P=void*;
struct Hit {float point[4],normal[4],surfaceNormal[4],penetration;int id;P body;};
static_assert(sizeof(Hit)==64);
using Filter=unsigned(*)(P,P,P);
unsigned include(P,P,P){return 1;}
unsigned exclude(P,P,P){return 0;}
void matrix(float* m,float x,float y,float z){memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;m[12]=x;m[13]=y;m[14]=z;}
int main(int argc,char**argv){
 if(argc!=2)return 2;auto dll=LoadLibraryA(argv[1]);if(!dll)return 3;
#define API(name,type) auto name=reinterpret_cast<type>(GetProcAddress(dll,#name));if(!name){printf("missing %s\n",#name);return 4;}
 API(NewtonCreate,P(*)(P,P));API(NewtonDestroy,void(*)(P));
 API(NewtonCreateBox,P(*)(P,float,float,float,int,const float*));
 API(NewtonCreateBody,P(*)(P,P,const float*));
 API(NewtonReleaseCollision,void(*)(P,P));
 API(NewtonWorldConvexCast,int(*)(P,const float*,const float*,P,float*,P,Filter,Hit*,int,int));
 API(NewtonCollisionCollide,int(*)(P,int,P,const float*,P,const float*,float*,float*,float*,int));
 LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);int errors=0;
 for(int scene=0;scene<4;scene++){
  P w=NewtonCreate(nullptr,nullptr);float obstacleMatrix[16],start[16],end[3];
  // wall with gap, clear travel, tangent floor, initial overlap.
  matrix(obstacleMatrix,scene==2?0:.35f,scene==2?-.05f:1,0);
  P obstacle=NewtonCreateBox(w,scene==2?10:.1f,scene==2?.1f:2,10,0,nullptr);
  NewtonCreateBody(w,obstacle,obstacleMatrix);
  P shape=NewtonCreateBox(w,.5f,1.8f,.5f,1,nullptr);
  matrix(start,scene==3?.2f:0,scene==2?.9f:1,0);
  end[0]=start[12]+(scene==1?-.1f:.1f);end[1]=start[13];end[2]=0;
  Hit hits[32]{};float t=1;int count=NewtonWorldConvexCast(w,start,end,shape,&t,nullptr,include,hits,32,0);
  float ignoredT=1;int ignored=NewtonWorldConvexCast(w,start,end,shape,&ignoredT,nullptr,exclude,hits,32,0);
  if(ignored!=0||!std::isfinite(t)||(scene==0&&count==0)||(scene==1&&count!=0))errors++;
  printf("scene=%d contacts=%d fraction=%.7f excluded=%d\n",scene,count,t,ignored);
  volatile int sink=0;
  for(int distance=0;distance<2;distance++){
  float travel=distance?.1f:.005f;end[0]=start[12]+(scene==1?-travel:travel);
  for(int mode=0;mode<2;mode++){
   LARGE_INTEGER a,b;QueryPerformanceCounter(&a);
   for(int repeat=0;repeat<20000;repeat++){
    if(mode==0){float hit=1;sink=sink+NewtonWorldConvexCast(w,start,end,shape,&hit,nullptr,include,hits,32,0);}
    else {float pos[16],points[96],normals[96],depth[32];memcpy(pos,start,64);
     // Same direct pair at start and endpoints: narrow-phase microbenchmark only,
     // not HPL AABB enumeration/filtering or the production slide algorithm.
     int steps=int(travel/.01f)+1;
     for(int step=0;step<=steps;step++){pos[12]=start[12]+(end[0]-start[12])*step/float(steps);
      sink=sink+NewtonCollisionCollide(w,32,shape,pos,obstacle,obstacleMatrix,points,normals,depth,0);}
    }
   }
   QueryPerformanceCounter(&b);printf("scene=%d travel=%.3f mode=%s microseconds_per_request=%.4f checksum=%d\n",scene,travel,mode?"start_plus_pair_overlaps":"world_sweep",1e6*double(b.QuadPart-a.QuadPart)/freq.QuadPart/20000,sink);
  }
  }
  NewtonReleaseCollision(w,shape);NewtonReleaseCollision(w,obstacle);NewtonDestroy(w);
 }
 printf("errors=%d; primitive benchmark only, not HPL/game FPS\n",errors);return errors?1:0;
}
