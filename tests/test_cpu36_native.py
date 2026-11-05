"""Many-contact native SSE worker prototype; not game callback coverage."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu36-native';b.mkdir(exist_ok=True)
pre=r"""
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define C(x) do{if(!(x)){printf("FAIL line %d\n",__LINE__);exit(1);}}while(0)
static void(*force)(const void*,const float*);static unsigned forces,contacts;
static void gravity(const void*b,float dt,int thread){float f[4]={0,-9.8f,0,0};force(b,f);__atomic_fetch_add(&forces,1,__ATOMIC_RELAXED);}
static void contact(const void*j,float dt,int thread){__atomic_fetch_add(&contacts,1,__ATOMIC_RELAXED);}
"""
post=r"""
static float reference[240][96][16];static unsigned rc[240],rf[240];
int main(){SetDllDirectoryA("D:\\SteamLibrary\\steamapps\\common\\SOMA");HMODULE m=LoadLibraryA("Newton.dll");C(m);
void*(*create)(void*,void*)=(void*)GetProcAddress(m,"NewtonCreate");void(*destroy)(void*)=(void*)GetProcAddress(m,"NewtonDestroy");
void*(*sphere)(void*,float,float,float,int,const float*)=(void*)GetProcAddress(m,"NewtonCreateSphere");void*(*body)(void*,void*,const float*)=(void*)GetProcAddress(m,"NewtonCreateBody");
void*(*box)(void*,float,float,float,int,const float*)=(void*)GetProcAddress(m,"NewtonCreateBox");
void(*mass)(void*,float,float,float,float)=(void*)GetProcAddress(m,"NewtonBodySetMassMatrix");void(*matrix)(void*,float*)=(void*)GetProcAddress(m,"NewtonBodyGetMatrix");void(*update)(void*,float)=(void*)GetProcAddress(m,"NewtonUpdate");
void(*fc)(void*,void*)=(void*)GetProcAddress(m,"NewtonBodySetForceAndTorqueCallback");void(*mc)(void*,int,int,void*,void*,void*)=(void*)GetProcAddress(m,"NewtonMaterialSetCollisionCallback");
void(*threads)(void*,int)=(void*)GetProcAddress(m,"NewtonSetThreadsCount");void(*platform)(void*,int)=(void*)GetProcAddress(m,"NewtonSetPlatformArchitecture");
force=(void*)GetProcAddress(m,"NewtonBodySetForce");C(create&&destroy&&sphere&&body&&box&&mass&&matrix&&update&&fc&&mc&&threads&&platform&&force);
c36Execute=(void*)((char*)m+0x1bf50);c36Queue=(void*)((char*)m+0x8aa0);c36Join=(void*)((char*)m+0x8e40);
LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);int failures=0;
for(int scene=0;scene<3;scene++)for(int rate=60;rate<=120;rate+=60){double timings[2]={0};unsigned long long before=c36Runs;double maxdelta=0;unsigned countdiff=0;
for(int mode=0;mode<2;mode++){
void*w=create(0,0);C(w);threads(w,8);platform(w,1);C(*(int*)((char*)w+0x2138)==1);
float mat[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};body(w,box(w,40,1,40,0,0),mat);
int n=scene==1?64:96;void*bs[96];void*c=sphere(w,.5f,.5f,.5f,0,0);
if(scene==2){void*(*hull)(void*,int,const float*,int,float,int,const float*)=(void*)GetProcAddress(m,"NewtonCreateConvexHull");C(hull);float cloud[128*3];for(int v=0;v<128;v++){double y=1.-2.*(v+.5)/128.;double radius=sqrt(1.-y*y);cloud[v*3]=.5f*(float)(cos(v*2.3999632297)*radius);cloud[v*3+1]=.5f*(float)y;cloud[v*3+2]=.5f*(float)(sin(v*2.3999632297)*radius);}c=hull(w,128,cloud,12,.0001f,0,0);C(c);}
void(*autosleep)(void*,int)=(void*)GetProcAddress(m,"NewtonBodySetAutoSleep");C(autosleep);
for(int i=0;i<n;i++){mat[12]=scene==1?(i%4)*.96f:(i%12)*1.5f;mat[14]=scene==1?((i/4)%4)*.96f:(i/12)*1.5f;mat[13]=scene==1?1.1f+(i/16)*.96f:1.1f;bs[i]=body(w,c,mat);mass(bs[i],1,.1f,.1f,.1f);fc(bs[i],gravity);if(scene==2)autosleep(bs[i],0);}
mc(w,0,0,0,0,contact);contacts=forces=0;
void**job=(void**)((char*)w+0xa0+0x13c0);void*old=*job;C(*(void**)old==(void*)c36Execute);void*vt[1]={(void*)c36_job};if(mode)*job=vt;
for(int i=0;i<240;i++){LARGE_INTEGER a,z;QueryPerformanceCounter(&a);update(w,1.f/rate);QueryPerformanceCounter(&z);if(i>=60)timings[mode]+=1000.0*(z.QuadPart-a.QuadPart)/freq.QuadPart;
for(int j=0;j<n;j++){float out[16];matrix(bs[j],out);for(int k=0;k<16;k++){C(isfinite(out[k]));if(mode){double delta=fabs(out[k]-reference[i][j][k]);if(delta>maxdelta)maxdelta=delta;}else reference[i][j][k]=out[k];}}
if(!mode){rc[i]=contacts;rf[i]=forces;}else countdiff+=(rc[i]!=contacts||rf[i]!=forces);
}
*job=old;destroy(w);
}
unsigned long long runs=c36Runs-before;C(runs>0);printf("CASE scene=%d hz=%d max_matrix_delta=%.9g callback_count_mismatch_steps=%u parallel_steps=%llu reference_ms=%.6f candidate_ms=%.6f\n",scene,rate,maxdelta,countdiff,runs,timings[0]/180,timings[1]/180);if(maxdelta>0.0001||countdiff)failures++;
}
printf("RESULT failures=%d; native standalone only\n",failures);return failures?1:0;
}
"""
s=pre+(r/'tests/cpu36_parallel.inc').read_text()+post;(b/'test.c').write_text(s)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=90)
(r/'audit/cpu36-native-unit.json').write_text(json.dumps(dict(scope=__doc__,exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));print(x.stdout+x.stderr);raise SystemExit(x.returncode)
