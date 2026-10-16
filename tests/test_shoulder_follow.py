from pathlib import Path
import subprocess,json,sys
F=Path(__file__).resolve().parents[1];T=F/'build';T.mkdir(exist_ok=True)
prefix=(F/'source/shoulders_r.inc').read_text().split('static void s26r_update_shoulders')[0]
old=(F/'tests/fixtures/shoulders_fu_before.inc').read_text().split('static void s26r_update_shoulders')[0]
head='''#include <math.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int i32;typedef uint32_t u32;typedef int64_t i64;typedef unsigned char u8;
static float h9_abs(float x){return fabsf(x);}
static float h5755eb_wrap_pi(float x){while(x>3.141592654f)x-=6.283185307f;while(x< -3.141592654f)x+=6.283185307f;return x;}
'''
names=['S26RShoulders','g_s26rShoulders','g_s26rShoulderLogs','s26r_angle','s26r_shoulder_step','s26fg_shoulder_step']
before=''.join('#define '+n+' old_'+n+'\n' for n in names)+old+''.join('#undef '+n+'\n' for n in names)
test=r'''
static float rad(float d){return d*0.01745329252f;}
static float error(float a,float b){return fabsf(s26r_angle(a-b));}
int main(){
 int rates[]={72,90,120,144};float final[4];
 for(int r=0;r<4;r++){
  int hz=rates[r];i64 now=1000000000LL,dt=1000000000LL/hz;
  S26RShoulders a={0},b={0},hip={0};old_S26RShoulders before={0};
  s26r_shoulder_step(&a,now,1,1,0,1,0,0);s26r_shoulder_step(&b,now,1,1,0,0,0,0);
  s26fg_shoulder_step(&hip,now,1,1,0,1,0,0,1,0);
  old_s26r_shoulder_step(&before,now,1,1,0,1,0,0);
  for(int frame=1;frame<=hz*3;frame++){
   now+=dt;float target=rad(90)*fminf((float)frame/hz,1);
   float prev=a.yaw;
   s26r_shoulder_step(&a,now,1,1,target,1,0,0);
   s26r_shoulder_step(&b,now,1,1,target,0,0,0);
   s26fg_shoulder_step(&hip,now,1,1,0,1,0,0,1,target);
   old_s26r_shoulder_step(&before,now,1,1,target,1,0,0);
   assert(error(a.yaw,b.yaw)<1e-6f); // reaching never freezes the shared heading
   assert(error(a.yaw,prev)<=rad(360)/hz+0.0001f);
   assert(a.yaw<=target+.0001f); // no predicted overshoot
  }
  assert(before.yaw==0);assert(error(a.yaw,rad(90))<rad(.1f));assert(error(hip.yaw,rad(90))<rad(.1f));
  final[r]=a.yaw;
  float same=a.yaw;s26r_shoulder_step(&a,now,1,1,rad(-90),1,0,0);assert(a.yaw==same);
  now+=dt;s26fg_shoulder_step(&hip,now,1,1,rad(-90),1,0,0,0,0);
  assert(error(hip.yaw,rad(90))<=rad(360)/hz+.001f); // tracker loss never snaps
  now+=dt;s26fg_shoulder_step(&hip,now,1,1,0,1,0,0,1,rad(20));
  assert(hip.trackerSeen);assert(isfinite(hip.yaw));
  s26r_shoulder_step(&a,now,2,1,rad(20),1,0,0);assert(error(a.yaw,rad(20))<.001f);
  s26r_shoulder_step(&a,now+500000000LL,2,1,rad(40),1,0,0);assert(error(a.yaw,rad(40))<.001f);
  s26r_shoulder_step(&a,now,2,0,0,1,0,0);assert(!a.valid&&!a.reach&&!a.headSeen);
 }
 for(int i=1;i<4;i++)assert(error(final[0],final[i])<rad(.1f));
 S26RShoulders s={0};i64 t=1000000000;
 s26r_shoulder_step(&s,t,1,1,rad(179),0,0,0);
 s26r_shoulder_step(&s,t+10000000,1,1,rad(-179),1,0,0);
 assert(error(s.yaw,rad(179))<rad(1));assert(s26r_angle(s.yaw-rad(179))>0);
 // Head reference holds through vertical pitch and reacquires with hysteresis.
 assert(s26fv_head_reference(&s,rad(35),1)==rad(35));
 assert(s26fv_head_reference(&s,rad(-145),.1f)==rad(35));
 assert(s26fv_head_reference(&s,rad(-145),.3f)==rad(35));
 assert(s26fv_head_reference(&s,rad(40),.4f)==rad(40));
 // Hands only corroborate within the trusted angular range, never steer 180 degrees.
 S26RShoulders c={0};s26r_shoulder_step(&c,t,1,1,0,0,rad(180),1);assert(c.yaw==0);
 // Sudden reversal remains bounded and finite.
 for(int f=1;f<400;f++){
  float p=c.yaw,target=f<200?rad(120):rad(-120);
  s26r_shoulder_step(&c,t+(i64)f*10000000,1,1,target,1,0,0);
  assert(isfinite(c.yaw));assert(error(c.yaw,p)<=rad(3.6f)+.001f);
 }
 puts("PASS: old reach freeze reproduced; continuous head/hip following; 72/90/120/144 Hz; bounded turns/reversals; no overshoot; wrap; duplicate XR time; recenter/gap/loss; tracker changes; vertical pitch hysteresis; hand corroboration.");
}
'''
p=T/'heading.c';p.write_text(head+before+prefix+test)
z=Path(sys.argv[1])
subprocess.run([str(z),'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],text=True,capture_output=True)
assert r.returncode==0,r.stderr
print(r.stdout)
(T/'heading.json').write_text(json.dumps(dict(exit=r.returncode,result=r.stdout,scope='Extracted production heading functions with synthetic tracked poses; no headset verification.'),indent=2))
