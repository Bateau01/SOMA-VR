from pathlib import Path
import subprocess,json,sys
R=Path(__file__).resolve().parents[1];T=R/'build';T.mkdir(exist_ok=True)
s=(R/'source/s26n.c').read_text()
def fun(name):
 a=s.index('static ',s.index(name+'(',s.index('#include "shoulders_r.inc"'))-12);b=s.index('{',a)+1;d=1
 while d:
  d+=(s[b]=='{')-(s[b]=='}');b+=1
 return s[a:b]
head=r'''#include <math.h>
#include <assert.h>
#include <stdio.h>
typedef int i32;
#define ext_Cosf cosf
#define ext_Sinf sinf
static struct{int valid;float yaw;}g_s26rShoulders={1,0};
static int g_h5745YawZeroSet;
static float g_h5745YawInvC=1,g_h5745YawInvS,base[3],metric=1,gameYaw;
static int available=1;
static void s26r_update_shoulders(void){}
static int h576an_body_slot_base(float*p){for(int i=0;i<3;i++)p[i]=base[i];return available;}
static float h5755ea_world_units_per_meter(void){return metric;}
static float s26r_shoulder_yaw(void){return gameYaw;}
'''
tests=r'''
int main(){int count=0;
 for(int scale=0;scale<3;scale++)for(int turn=-6;turn<=6;turn++)for(int side=-1;side<=1;side+=2){
  metric=scale==0?.7f:scale==1?1:1.4f;gameYaw=turn*.5f;
  float x=side*.18f,y=-.2f,z=.09f,a[3],b[3];
  base[0]=10;base[1]=2;base[2]=-4;assert(h576an_body_slot_anchor(x,y,z,a));
  assert(fabsf(a[1]-(2+metric*y))<1e-5f);
  assert(fabsf(hypotf(a[0]-10,a[2]+4)-metric*hypotf(x,z))<1e-5f);
  base[0]+=.3f;base[1]-=.5f;base[2]-=.1f;assert(h576an_body_slot_anchor(x,y,z,b));
  assert(fabsf(b[0]-a[0]-.3f)<1e-5f&&fabsf(b[1]-a[1]+.5f)<1e-5f&&fabsf(b[2]-a[2]+.1f)<1e-5f);
  for(int recenter=0;recenter<2;recenter++){
   g_h5745YawZeroSet=recenter;g_h5745YawInvC=cosf(.35f);g_h5745YawInvS=sinf(.35f);
   g_s26rShoulders.yaw=gameYaw;float ox,oy,expected=gameYaw+(recenter?.7f:0);
   s26bv_body_move(.3f,.8f,&ox,&oy);
   assert(fabsf(hypotf(ox,oy)-hypotf(.3f,.8f))<1e-5f);
   assert(fabsf(ox-(cosf(expected)*.3f-sinf(expected)*.8f))<1e-5f);
   assert(fabsf(oy-(sinf(expected)*.3f+cosf(expected)*.8f))<1e-5f);count++;
  }
 }
 available=0;float out[3]={99,99,99};assert(!h576an_body_slot_anchor(0,0,0,out)&&out[0]==99);
 assert(!h576an_body_slot_anchor(0,0,0,0));
 g_s26rShoulders.valid=0;float x,y;s26bv_body_move(.3f,.8f,&x,&y);assert(x==.3f&&y==.8f);
 printf("PASS %d transform cases: both slots, world scales, leaning/crouching translation, yaw, recenter, locomotion speed preservation and invalid-state fallbacks.\n",count);
}'''
p=T/'transforms.c';p.write_text(head+fun('s26bv_body_move')+fun('h576an_body_slot_anchor')+tests)
z=Path(sys.argv[1])
subprocess.run([str(z),'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout);(T/'transforms.json').write_text(json.dumps(dict(exit=r.returncode,result=r.stdout,scope='Production anchor and Body movement functions with mocked tracking-to-game base; synthetic checks, not hardware testing.'),indent=2))
