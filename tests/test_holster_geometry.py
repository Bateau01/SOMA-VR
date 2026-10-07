from pathlib import Path
import ctypes as c,math,subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build'
source='#include <math.h>\ntypedef int i32;\n#define ext_Sqrtf sqrtf\n'+(R/'source/holster_grip_ef.inc').read_text()
source+='\n__declspec(dllexport) int test(const float*h,const float*r,const float*a,const float*p,float*o){return s26ef_holster_matrix(h,r,a,p,o);}\n'
p=B/'holster_geometry_test.c';p.write_text(source);dll=B/'holster_geometry_test.dll'
subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-o',str(dll)],check=True)
lib=c.CDLL(str(dll));f=lib.test;F=c.c_float;f.argtypes=[c.POINTER(F)]*5;checks=0
rotations=[[1,0,0,0,1,0,0,0,1],[0,1,0,0,0,1,1,0,0],[1,0,0,0,0,1,0,-1,0]]
for angle in [-3,-1.5,-.1,0,.6,1.8,3.1]:
 for scale in [.1,.7,1,1.4,3]:
  co,si=math.cos(angle),math.sin(angle)
  hand=[co*scale,si*scale,0,0,-si*scale,co*scale,0,0,0,0,scale,0,42,3,-7,1]
  for rot in rotations:
   anchor=[.025,-.013,.15];contact=[42.13,3.2,-7.1];out=(F*16)(*([99]*16))
   assert f((F*16)(*hand),(F*9)(*rot),(F*3)(*anchor),(F*3)(*contact),out)
   for axis in range(3):assert abs(sum(out[axis*4+j]**2 for j in range(3))-1)<1e-5
   for row in range(3):assert abs(sum(out[col*4+row]*anchor[col] for col in range(3))+out[12+row]-contact[row])<1e-5
   expected=[co*rot[0]-si*rot[1],si*rot[0]+co*rot[1],rot[2]]
   assert all(abs(out[i]-expected[i])<1e-5 for i in range(3));checks+=1
hand=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];rot=rotations[0]
for index,value in [(0,float('nan')),(4,float('inf')),(10,-1),(0,0)]:
 bad=hand.copy();bad[index]=value;out=(F*16)(*([99]*16))
 assert not f((F*16)(*bad),(F*9)(*rot),(F*3)(0,0,0),(F*3)(0,0,0),out)
 assert list(out)==[99]*16;checks+=1
for bad in [[-1,0,0,0,1,0,0,0,1],[2,0,0,0,1,0,0,0,1],[1,0,0,1,0,0,0,0,1]]:
 out=(F*16)(*([99]*16));assert not f((F*16)(*hand),(F*9)(*bad),(F*3)(0,0,0),(F*3)(0,0,0),out);assert list(out)==[99]*16;checks+=1
result={'passed':True,'checks':checks,'scope':'Pure geometry only; item profiles and physical latch not yet integrated'}
(B/'holster_geometry_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
