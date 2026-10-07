"""Test the production DFR mask, including asymmetric eye projections."""
from pathlib import Path
import ctypes as c,subprocess,sys,json,math
R=Path(__file__).resolve().parents[1];B=R/'build';s=(R/'source/foveation_tuning_ei.inc').read_text(encoding='utf-8-sig');s=s[:s.index('/* Render-thread-only')]
code='#include <math.h>\ntypedef unsigned char u8;typedef unsigned u32;typedef int i32;\n#define ext_Sqrtf sqrtf\n#define ext_Sinf sinf\n#define ext_Cosf cosf\n'+'\nstatic u32 g_s26eiMeasureEpoch;\n'+s.replace('static i32 s26ef_rate_mask','__declspec(dllexport) i32 s26ef_rate_mask')
p=B/'foveation_mask_test.c';p.write_text(code);dll=B/'foveation_mask_test.dll';subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-o',str(dll)],check=True)
l=c.CDLL(str(dll));fn=l.s26ef_rate_mask;fn.argtypes=[c.POINTER(c.c_ubyte)]+[c.c_int]*6+[c.POINTER(c.c_float)]*2;fn.restype=c.c_int
checks=0
for w,h in [(64,64),(1920,1080),(2492,2568),(3000,3000),(4096,2048),(8192,8192)]:
 tw,th=(w+15)//16,(h+15)//16
 for px,py in [(0,0),(.2,-.1),(-.2,.1)]:
  p=(c.c_float*16)(1,0,0,0,0,1,0,0,px,py,-1,-1,0,0,-.2,0)
  for gx,gy in [(0,0),(.3,0),(-.3,0),(0,.3),(0,-.3)]:
   n=math.sqrt(gx*gx+gy*gy+1);g=(c.c_float*3)(gx/n,gy/n,-1/n)
   out=(c.c_ubyte*(tw*th+16))(*([231]*(tw*th+16)))
   assert fn(out,tw,th,w,h,16,16,p,g)==1
   assert list(out[tw*th:])==[231]*16;assert set(out[:tw*th])<={0,1}
   ix=int(((gx-px)+1)*w/32);iy=int(((gy-py)+1)*h/32)
   if 0<=ix<tw and 0<=iy<th:assert out[iy*tw+ix]==0
   checks+=1
  for bad in [(float('nan'),0,-1),(0,0,0),(0,0,.5),(0,0,-2)]:
   out=(c.c_ubyte*(tw*th))(*([231]*(tw*th)));assert fn(out,tw,th,w,h,16,16,p,(c.c_float*3)(*bad))==0;assert set(out)=={231};checks+=1
result={'passed':True,'cases':checks,'covers':['asymmetric projection','gaze movement','partial tiles','8192 eye resolution','invalid gaze fail-open to full quality','buffer bounds']}
(B/'foveation_mask_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
