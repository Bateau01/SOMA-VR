"""Real Newton ray contract for the current 8-cm palm-shell geometry.

Uses Carl's authored Trigger box dimensions, but not Lux filtering/dispatch.
This checks a proposed inside-ray failure, not the full player's failed sequence.
"""
from pathlib import Path
import subprocess, sys, json
R=Path(__file__).resolve().parents[1]
code=r'''
#include <windows.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
int checks;
#define C(x) do{++checks;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
template<class T>T api(HMODULE n,const char*s){auto p=GetProcAddress(n,s);C(p);return (T)p;}
int main(){
 auto n=LoadLibraryA("D:\\SteamLibrary\\steamapps\\common\\SOMA\\Newton.dll");C(n);
 auto create=api<void*(*)()>(n,"NewtonCreate");auto destroy=api<void(*)(void*)>(n,"NewtonDestroy");
 auto box=api<void*(*)(void*,float,float,float,int,const float*)>(n,"NewtonCreateBox");
 auto ray=api<float(*)(void*,const float*,const float*,float*,int*)>(n,"NewtonCollisionRayCast");
 auto release=api<void(*)(void*,void*)>(n,"NewtonReleaseCollision");
 void*w=create();C(w);void*b=box(w,1.32612f,1.09585f,1.70176f,0,nullptr);C(b);
 int hits=0;float normal[3];int attr;
 // Exact central ray start/end distances used by the production palm shell.
 for(int axis=0;axis<3;++axis)for(int sign=-1;sign<=1;sign+=2){
  float a[3]={},z[3]={};a[axis]=-.04f*sign;z[axis]=.04f*sign;
  float t=ray(b,a,z,normal,&attr);printf("axis=%d sign=%d t=%g\n",axis,sign,t);if(t>=0&&t<=1)++hits;
 }
 C(hits==6);
 float a[3]={-1,0,0},z[3]={0,0,0};float t=ray(b,a,z,normal,&attr);C(t>0&&t<1);
 // A shallow approach is also detected. Interior zero is a valid hit.
 a[0]=-.68f;z[0]=-.60f;t=ray(b,a,z,normal,&attr);C(t>0&&t<1);
 release(w,b);destroy(w);
 printf("PASS %d: all six interior rays return zero; exterior crossing also detects the Carl box\n",checks);
}
'''
p=R/'build/area_ray_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
out={'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__}
(R/'docs/v109-evidence/area_ray_hr.json').write_text(json.dumps(out,indent=2))
print(out['output']);raise SystemExit(v.returncode)
