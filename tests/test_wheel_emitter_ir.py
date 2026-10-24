from pathlib import Path
import subprocess,sys
r=Path.cwd();s=(r/'source/s26n.c').read_text();a=s.index('    g_h576baWheelPhase+=angleStep-');b=s.index('    float mag=h9_abs(speed);',a);block=s[a:b]
head='''#include <math.h>
#include <stdio.h>
static float g_h576baWheelPhase;
static float h10_dot(float*a,float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static float emit(float angleStep,float dt,float angular){float omega[3]={0,angular,0},pin[3]={0,1,0};
'''
code=head+block+'''return speed;}
int main(void){for(int hz=60;hz<=120;hz+=60){g_h576baWheelPhase=0;float integral=0;int previous=0,gaps=0,caps=0;for(int n=1;n<=hz;n++){int sample=n*90/hz;float delta=(sample-previous)*3.5f/90;previous=sample;if(delta==0)gaps++;float target=emit(delta,1.0f/hz,3.5f);if(target>=4)caps++;integral+=target/hz;}printf("hz=%d gaps=%d caps=%d targetIntegral=%.6f\\n",hz,gaps,caps,integral);if(hz==120&&!(gaps==30&&caps==90&&integral<3.2f))return 1;}return 0;}
'''
p=r/'build/wheel_emitter_ir.c';p.write_text(code)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout);assert v.returncode==0
(r/'docs/v109-evidence/wheel_emitter_ir.txt').write_text('Extracted production arithmetic; idealized constant body velocity, synthetic90Hz orbital deltas. No geometry, real tracking, callbacks or native scene validation.\n'+v.stdout)
