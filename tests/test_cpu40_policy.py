"""Synthetic scheduling decisions, separate from native/game validation."""
from pathlib import Path
import subprocess,sys,json
r=Path(__file__).resolve().parents[1];b=r/'build/cpu40-policy';b.mkdir(exist_ok=True)
body=r'''
#include <stdio.h>
#define C(x) do{if(!(x)){printf("FAIL line %d\n",__LINE__);return 1;}}while(0)
'''
case=r'''
int main(){void*w=(void*)1;unsigned step=1;unsigned long long hz=1000000;
C(c38_select(w,64,step++,1,hz)==0);c38_observe(500,0,0);
for(int k=0;k<16;k++){C(c38_select(w,64,step++,1,hz)==8);c38_observe(800,150,8);}
C(c38_select(w,64,step++,1,hz)==0);c38_observe(10,0,0);
C(c38_select(w,64,step++,1,hz)==0);c38_observe(500,0,0);
C(c38_select(w,64,step++,1,hz)==8);c38_observe(800,790,8);
for(int k=0;k<32;k++){C(c38_select(w,64+(k%2),step++,1,hz)==0);c38_observe(500,0,0);}
C(c38_select(w,64,step++,1,hz)==8);c38_observe(800,150,8);
C(c38_select((void*)2,64,step++,1,hz)==0);c38_observe(500,0,0);
C(c38_select((void*)2,64,step++,0,hz)==0);c38_observe(500,0,0);
C(c38_select((void*)2,300,step++,1,hz)==0);c38_observe(500,0,0);
C(c38_select((void*)2,300,1,1,hz)==0);
puts("PASS probes, cheap-work recovery, imbalance cooldown, world/step/count reset, disabled selection");return 0;}
'''
results=[]
for name in ('cpu38','cpu40'):
 p=b/(name+'.c');p.write_text(body+(r/('tests/'+name+'_policy.inc')).read_text()+case)
 exe=b/(name+'.exe');subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(exe)],check=True)
 x=subprocess.run([str(exe)],capture_output=True,text=True);results.append(dict(policy=name,exit=x.returncode,output=x.stdout))
(r/'audit/cpu40-policy.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));assert results[0]['exit']!=0 and results[1]['exit']==0
