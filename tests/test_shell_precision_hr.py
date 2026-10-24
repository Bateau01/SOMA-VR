"""Floating-point palm-shell geometry; no native dispatch or headset test."""
from pathlib import Path
import subprocess,sys,json,re
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text()
baseline='--baseline' in sys.argv
m=re.search(r'static float s26hr_shell_ray_gap\(float dist\)\{[^}]+\}',s)
helper=m.group() if m else ''
code=r'''
#include <cmath>
#include <cstdio>
#define H483_CURTAIN_RAY_M .080f
#define H483_CURTAIN_SHELL_M .040f
'''+helper+r'''
int main(){int misses=0,checks=0;
 for(int i=0;i<360;i++)for(int side=0;side<2;side++){
 float angle=i*.01745329252f,dir[3]={cosf(angle),0,sinf(angle)};
 float center[3]={37.2859f,11.1278f,17.2291f};
 float dist=side ? .080f : 0.f;
 float start[3],hit[3],d[3];
 for(int k=0;k<3;k++){start[k]=center[k]-dir[k]*(H483_CURTAIN_RAY_M*.5f);hit[k]=start[k]+dir[k]*dist;d[k]=hit[k]-center[k];}
 float gap=GAP;
 checks++;if(gap>H483_CURTAIN_SHELL_M)misses++;
 }
 EXTRA
 printf("checks=%d endpoint_false_rejections=%d\n",checks,misses);
 return misses?1:0;
}
'''
code=code.replace('GAP','sqrtf(d[0]*d[0]+d[1]*d[1]+d[2]*d[2])' if baseline else 's26hr_shell_ray_gap(dist)')
code=code.replace('EXTRA','' if baseline else r'''
 for(int i=-20;i<=100;i++){
  float dist=i*.001f,gap=s26hr_shell_ray_gap(dist);
  double expected=fabs((double)dist-(double)(H483_CURTAIN_RAY_M*.5f));
  checks++;if(fabs((double)gap-expected)>1e-8)misses++;
  if(i<0||i>80){checks++;if(gap<=H483_CURTAIN_SHELL_M)misses++;}
 }
''')
if not baseline:assert helper,'candidate helper missing'
p=R/'build/shell_precision_hr.cpp';p.write_text(code)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
out={'exit':v.returncode,'output':v.stdout+v.stderr,'scope':__doc__}
(R/'docs/v109-evidence'/('shell_precision_baseline.json' if baseline else 'shell_precision_candidate.json')).write_text(json.dumps(out,indent=2))
print(out['output']);raise SystemExit(v.returncode)
