"""Compiled production wheel gesture branch: baseline rejection at120 and equal-time candidate acceptance. No engine or tracking simulation."""
from pathlib import Path
import subprocess,sys,re
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
s=(R/'source/s26n.c').read_text();old=(R/'tests/fixtures/in_baseline/wheel_branch.c').read_text()
def branch(s,start):
 a=s.index(start);b=s.index('    g_h576baWheelOrbit[hand]=orbit;',a)
 return s[a:b]
head='''#include <stdio.h>
#include <math.h>
static unsigned g_s26gdRateMultiplier=1;
static float s26gd_tick_amount(float x){return x/g_s26gdRateMultiplier;}
static float h9_abs(float x){return fabsf(x);}
static int g_h576baWheelOrbitPackets,g_h576baWheelWristPackets,g_h576baWheelBlendPackets;
'''
head += "\n".join(re.findall(r"^#define H576(?:AZ_WHEEL_ANGLE|BA_WHEEL_WRIST)[^\n]+",s,re.M))+"\n"
body=head
for name,text,begin in [('before',old,'    if(h9_abs(orbit)>H576AZ_WHEEL_ANGLE_STEP_CAP_RAD)'),('after',s,'    // S26IN: these are per-step angles')]:
 body+='static float '+name+'(float orbit,float wrist,float radius){\n'+branch(text,begin)+'return angle;}\n'
body+='''int main(void){int checks=0;
#define C(x) do{checks++;if(!(x)){printf("FAIL line%d %s\\n",__LINE__,#x);return 1;}}while(0)
 g_s26gdRateMultiplier=1;C(before(.09f/60,0,.2f)>0);
 g_s26gdRateMultiplier=2;C(before(.09f/120,0,.2f)==0);C(after(.09f/120,0,.2f)>0);
 for(int k=-200;k<=200;k++)for(int c=0;c<3;c++)for(int r=0;r<3;r++){
 float speed=k*.05f,rad=.02f+r*.09f,o=c==1?0:speed,w=c==0?0:speed*.8f;
 g_s26gdRateMultiplier=1;float a=after(o/60,w/60,rad);C(a==before(o/60,w/60,rad));
 g_s26gdRateMultiplier=2;float b=after(o/120,w/120,rad);C(fabsf(a*60-b*120)<.0001f);
 }
 printf("PASS %d checks; baseline slow-turn120 rejection reproduced;60 identical;120 equal-time orbit/wrist/blend/reversal/cap\\n",checks);return 0;}
'''
p=B/'wheel_rate_in.c';p.write_text(body);exe=p.with_suffix('.exe');subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
