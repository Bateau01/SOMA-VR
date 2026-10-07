"""DFR configuration, quality ordering, gaze cone and latency/motion guards."""
from pathlib import Path
import ctypes as c,subprocess,sys,math,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head='#include <math.h>\ntypedef unsigned char u8;typedef unsigned u32;typedef int i32;typedef long long i64;\n#define ext_Sqrtf sqrtf\n#define ext_Sinf sinf\n#define ext_Cosf cosf\n'
s=(R/'source/foveation_tuning_ei.inc').read_text(encoding='utf-8-sig')
tail='''
__declspec(dllexport) int config(const char*t,int n){return s26ei_dfr_config((const u8*)t,n);}
__declspec(dllexport) unsigned value(void){return g_s26eiDFRConfig;}
__declspec(dllexport) float guard(long long now,long long when,const float*g,int valid){s26ei_gaze_guard(now,when,g,valid);return g_s26eiGazeGuard;}
__declspec(dllexport) int mask(unsigned char*out,const float*p,const float*g){return s26ef_rate_mask(out,64,64,1024,1024,16,16,p,g);}
'''
p=B/'dfr_tuning.c';p.write_text(head+'\nstatic u32 g_s26eiMeasureEpoch;\n'+s+tail);dll=B/'dfr_tuning.dll';subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-o',str(dll)],check=True)
l=c.CDLL(str(dll));F=c.c_float;P=c.POINTER(F);l.config.argtypes=[c.c_char_p,c.c_int];l.value.restype=c.c_uint;l.guard.argtypes=[c.c_longlong,c.c_longlong,P,c.c_int];l.guard.restype=F;l.mask.argtypes=[c.POINTER(c.c_ubyte),P,P]
checks=0
for inner in range(0,50):
 for outer in range(0,75):
  text=f'{inner:02}{outer:02}11'.encode();old=l.value();valid=10<=inner<=35 and 25<=outer<=60 and outer>=inner+5
  assert bool(l.config(text,len(text)))==valid,(inner,outer)
  if not valid:assert l.value()==old
  checks+=1
for text in [b'',b'254501x',b'254502',b'254521',b'25x501',b'-54501']:
 old=l.value();assert not l.config(text,len(text)) and l.value()==old;checks+=1
p=(F*16)(1,0,0,0,0,1,0,0,0,0,-1,-1,0,0,-.2,0);g=(F*3)(0,0,-1)
l.guard(0,0,g,0)
counts=[]
for text in [b'254501',b'204011',b'153511']:
 assert l.config(text,6);out=(c.c_ubyte*4096)();assert l.mask(out,p,g)
 cost=sum([1,.25,.0625][v] for v in out);counts.append(cost)
 assert out[32*64+32]==0
 checks+=1
assert counts[0]>counts[1]>counts[2]
# Latency widens protected regions and cannot accidentally coarsen them.
l.config(b'153511',6);base=(c.c_ubyte*4096)();l.mask(base,p,g)
a=l.guard(1000000000,920000000,g,1);assert 0<a<=.176301
protected=(c.c_ubyte*4096)();l.mask(protected,p,g);assert all(x<=y for x,y in zip(protected,base));checks+=1
l.config(b'153510',6);disabled=(c.c_ubyte*4096)();l.mask(disabled,p,g);assert list(disabled)==list(base);checks+=1
# Invalid tracking clears history. Rapid gaze shifts widen, then smoothly recover.
assert l.guard(0,0,g,0)==0
l.guard(1000000000,1000000000,g,1);shift=(F*3)(.5,0,-math.sqrt(.75))
boost=l.guard(1010000000,1010000000,shift,1);assert .17<boost<.177
assert l.guard(1010000000,1010000000,shift,1)==boost
later=l.guard(1020000000,1020000000,shift,1);assert 0<later<boost
assert l.guard(2000000000,2000000000,shift,1)==0;checks+=1
# Off-axis gaze still receives a complete sharp cone where visible.
l.config(b'204011',6)
for angle in [-.6,0,.6]:
 g=(F*3)(math.sin(angle),0,-math.cos(angle));out=(c.c_ubyte*4096)();l.mask(out,p,g)
 for y in range(64):
  for x in range(64):
   ray=((x+.5)/32-1,(y+.5)/32-1,-1);dot=sum(ray[i]*g[i] for i in range(3))/math.sqrt(sum(t*t for t in ray))
   if dot>=math.cos(math.radians(20)):assert out[y*64+x]==0
 checks+=1
result={'passed':True,'checks':checks,'estimated_shader_work':counts,'latency_and_motion_protection':True,'off_axis_cone':True}
(B/'dfr_tuning_results.json').write_text(json.dumps(result,indent=2));print(result)
