"""Production calibration/crouch dispatcher, synthetic tracked poses and script calls."""
from pathlib import Path
import argparse,subprocess,json,re
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[1];s=(r/'source/s26n.c').read_text(encoding='utf-8')
def fn(name):
    start=re.search(r'static (?:i32|void) '+name+r'\([^;{}]*\)\s*\{',s).start()
    i=s.index('{',start)+1;depth=1
    while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
    return s[start:i]
cal='static i32 s26hr_calibrate_height(void){g_s26nHeightValid=0;return 1;}' if a.baseline else fn('s26hr_calibrate_height')
c=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
typedef unsigned u32;typedef int i32;typedef unsigned char u8;
u32 g_s26nCrouchMode=2,g_s26nCrouchOwned,g_s26nCrouchPoll,g_s26nHeadValidFrame=100,g_frameCounter=100;
u8 g_s26nHeadHeightFresh=1,g_s26nHeightValid,g_s26nCrouchLow;
float g_s26nStandingY,head[3]={0,1.8f,0};
int g_h576mScriptRuntimePublished=1,on=1,running=1,origin=1,paused=1,calls,down;
int p2_xr_on(){return on;}int p2_xr_running(){return running;}int p2_xr_origin_set(){return origin;}
int h5754h_pause_active(){return paused;}float* p2_eye_mid(){return head;}
void h5754h_script_method(const char* s){calls++;down=!strcmp(s,"HPL3VR_PhysicalCrouchDown");}
'''+cal+'\n'+fn('s26n_dispatch_crouch')+r'''
int main(){
 if(!s26hr_calibrate_height())return 1;
 head[1]=1.4f;paused=0;s26n_dispatch_crouch();
 if(!down){puts("FAIL: paused calibration lost the upright reference before resume");return 2;}
 for(int mode=0;mode<2;mode++){g_s26nCrouchMode=mode;calls=0;g_frameCounter+=6;g_s26nHeadValidFrame=g_frameCounter;s26n_dispatch_crouch();if(calls)return 3;}
 g_s26nCrouchMode=2;g_s26nCrouchOwned=0;
 for(int invalid=0;invalid<6;invalid++){
  on=running=origin=g_s26nHeadHeightFresh=1;g_s26nHeadValidFrame=g_frameCounter;head[1]=2;
  if(invalid==0)on=0;if(invalid==1)running=0;if(invalid==2)origin=0;
  if(invalid==3)g_s26nHeadHeightFresh=0;if(invalid==4)g_s26nHeadValidFrame=g_frameCounter-3;if(invalid==5)head[1]=NAN;
  if(s26hr_calibrate_height()||fabsf(g_s26nStandingY-1.8f)>.001f)return 4;
 }
 on=running=origin=g_s26nHeadHeightFresh=1;head[1]=1.8f;g_frameCounter+=6;g_s26nHeadValidFrame=g_frameCounter;
 s26n_dispatch_crouch();if(down)return 5;
 puts("PASS: request-time paused reference, button modes unchanged, tracking rejection preserves calibration, stand-up release");return 0;
}
'''
name='height_baseline' if a.baseline else 'height_candidate';b=r/'build';f=b/(name+'.c');f.write_text(c)
subprocess.run([a.zig,'cc','-O2',str(f),'-o',str(f.with_suffix('.exe'))],check=True)
v=subprocess.run([str(f.with_suffix('.exe'))],capture_output=True,text=True)
(r/'docs/v109-evidence'/f'{name}.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':__doc__},indent=2))
print(v.stdout);raise SystemExit(v.returncode)
