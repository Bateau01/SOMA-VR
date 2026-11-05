from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build/cpu25-native';b.mkdir(exist_ok=True)
s=(r/'tests/cpu25_clock.inc').read_text()
pre=r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
#define ext_GetModuleHandleA(x) ((void*)GetModuleHandleA(x))
#define ext_GetProcAddress(m,n) ((void*)GetProcAddress((HMODULE)m,n))
#define ext_Log(...) ((void)0)
static u64 cpuFreq;static u32 cpu14Saved;static u64 cpu_detail_begin(void){return 1;}
static int __attribute__((ms_abi)) qpc(u64*p){return QueryPerformanceCounter((LARGE_INTEGER*)p);}
static int(__attribute__((ms_abi))*cpuCounter)(u64*)=qpc;
'''
post=r'''
static u32 __attribute__((ms_abi)) custom(void){return 123;}
static void(*applyForce)(const void*,const float*);static unsigned contacts,forces;
static void gravity(const void*b,float dt,int thread){(void)dt;(void)thread;float f[4]={0,-9.8f,0,0};applyForce(b,f);forces++;}
static void contact(const void*j,float dt,int thread){(void)j;(void)dt;(void)thread;contacts++;}
int main(){SetDllDirectoryA("D:\\SteamLibrary\\steamapps\\common\\SOMA");HMODULE m=LoadLibraryA("Newton.dll");C(m);QueryPerformanceFrequency((LARGE_INTEGER*)&cpuFreq);
void*(*create)(void*,void*)=(void*)GetProcAddress(m,"NewtonCreate");void(*destroy)(void*)=(void*)GetProcAddress(m,"NewtonDestroy");
void*(*sphere)(void*,float,float,float,int,const float*)=(void*)GetProcAddress(m,"NewtonCreateSphere");void*(*body)(void*,void*,const float*)=(void*)GetProcAddress(m,"NewtonCreateBody");
void(*mass)(void*,float,float,float,float)=(void*)GetProcAddress(m,"NewtonBodySetMassMatrix");void(*velocity)(void*,const float*)=(void*)GetProcAddress(m,"NewtonBodySetVelocity");
void(*matrix)(void*,float*)=(void*)GetProcAddress(m,"NewtonBodyGetMatrix");void(*update)(void*,float)=(void*)GetProcAddress(m,"NewtonUpdate");u32(*ticks)(void*,u32)=(void*)GetProcAddress(m,"NewtonReadPerformanceTicks");
C(create&&destroy&&sphere&&body&&mass&&velocity&&matrix&&update&&ticks);
float identity[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,10,0,1},vel[3]={1,2,3},reference[240][16];u64 sums=0;u32 nonzero=0;
for(int rate=60;rate<=120;rate+=60)for(int mode=0;mode<2;mode++){void*w=create(0,0);C(w);void*c=sphere(w,.5f,.5f,.5f,0,0);C(c);void*b=body(w,c,identity);C(b);mass(b,1,.1f,.1f,.1f);velocity(b,vel);
for(int i=0;i<240;i++){u32 active=mode?cpu25_begin(w):0;if(mode)C(active==1);update(w,1.f/rate);u32 t=ticks(w,0);if(mode){nonzero+=t>0;sums+=t;}else C(t==0);cpu25_end(w,active);C(*(void**)((u8*)w+0x2460)==0);C(ticks(w,0)==0);float out[16];matrix(b,out);if(!mode)memcpy(reference[i],out,sizeof(out));else C(memcmp(reference[i],out,sizeof(out))==0);}
C(reference[239][12]>.5f);if(mode){cpu25SetClock(w,custom);C(cpu25_begin(w)==0);C(*(void**)((u8*)w+0x2460)==(void*)custom);cpu25SetClock(w,0);cpu14Saved=1;C(cpu25_begin(w)==0);cpu14Saved=0;}
destroy(w);}
void*(*box)(void*,float,float,float,int,const float*)=(void*)GetProcAddress(m,"NewtonCreateBox");
void(*forceCallback)(void*,void*)=(void*)GetProcAddress(m,"NewtonBodySetForceAndTorqueCallback");
void(*materialCallback)(void*,int,int,void*,void*,void*)=(void*)GetProcAddress(m,"NewtonMaterialSetCollisionCallback");
void(*threads)(void*,int)=(void*)GetProcAddress(m,"NewtonSetThreadsCount");
applyForce=(void*)GetProcAddress(m,"NewtonBodySetForce");C(box&&forceCallback&&materialCallback&&threads&&applyForce);
unsigned referenceContacts[240],referenceForces[240];
for(int rate=60;rate<=120;rate+=60)for(int mode=0;mode<2;mode++){
void*w=create(0,0);C(w);threads(w,1);contacts=forces=0;float floorM[16];memcpy(floorM,identity,sizeof(floorM));floorM[13]=0;body(w,box(w,20,1,20,0,0),floorM);floorM[13]=2;
void*b=body(w,sphere(w,.5f,.5f,.5f,0,0),floorM);mass(b,1,.1f,.1f,.1f);forceCallback(b,gravity);materialCallback(w,0,0,0,0,contact);
for(int i=0;i<240;i++){u32 active=mode?cpu25_begin(w):0;if(mode)C(active==1);update(w,1.f/rate);cpu25_end(w,active);C(*(void**)((u8*)w+0x2460)==0);float out[16];matrix(b,out);if(!mode){memcpy(reference[i],out,sizeof(out));referenceContacts[i]=contacts;referenceForces[i]=forces;}else{C(memcmp(reference[i],out,sizeof(out))==0);C(referenceContacts[i]==contacts);C(referenceForces[i]==forces);}}
C(contacts>0&&forces>0);C(reference[239][13]>.9f&&reference[239][13]<1.1f);destroy(w);
}
printf("PASS actualNewton60/120Hz480 falling/resting contact trajectories exact; native contact and force callback counts match every step\n");
C(nonzero>0);printf("PASS actualNewton60/120Hz480 trajectory comparisons exact; customclock preserved; default restored every step; nonzero %u sum_us %llu\n",nonzero,sums);}
'''
(b/'test.c').write_text(pre+s+post)
subprocess.run([sys.argv[1],'cc','-O2',str(b/'test.c'),'-o',str(b/'test.exe')],check=True)
x=subprocess.run([str(b/'test.exe')],capture_output=True,text=True,timeout=60);print(x.stdout+x.stderr)
(r/'audit/cpu25-native-unit.json').write_text(json.dumps(dict(scope='Actual Newton DLL isolated sphere trajectory and clock lifecycle, not fullgame physics regression',exit=x.returncode,output=x.stdout+x.stderr,source_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2));raise SystemExit(x.returncode)
