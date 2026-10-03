"""Execute the production HANDS AND HAPTICS logic (smart grip, grip pressure,
point to press, creature haptics, button hints and their settings bridge)
against mocked engine/OpenXR state. Contract tests only; feel, thresholds and
the native label placement still need an Index headset test.
"""
from pathlib import Path
import re,subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
S=R/'source';s=(S/'s26n.c').read_text()
def fn(name,src=s):
    for m in re.finditer(r'static [A-Za-z0-9_ \*]*\b'+name+r'\(',src):
        start=m.start();brace=src.index('{',m.end());semi=src.find(';',m.end())
        if semi!=-1 and semi<brace:continue
        depth=0
        for i in range(brace,len(src)):
            depth+=(src[i]=='{')-(src[i]=='}')
            if depth==0:return src[start:i+1]+'\n'
    raise SystemExit('function not found: '+name)
types=s[s.index('typedef unsigned char'):s.index('#define XR_SUCCESS')]
defines='\n'.join(x for x in s.splitlines() if x.startswith('#define XR_'))
remap=s[s.index('/* S26N button remapping.'):s.index('static void s26n_buttons_update')]
hint=(S/'hint_ec.inc').read_text();hintLogic=hint[:hint.index('/* Native 3D label surface. */')]
index=(S/'index_ec.inc').read_text();pressure=index[index.index('/* GRIP PRESSURE: 0..1'):]
haptics=(S/'haptics_ec.inc').read_text()
comfort=s[s.index('/* S26EC HANDS AND HAPTICS options'):s.index('static u64 __attribute__((ms_abi)) h5730_run_global_detour(')]
header=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static int checks;
static void zero_bytes(void*p,u64 n){memset(p,0,n);}
static void ext_Log(const char*f,...){(void)f;}
static float ext_Sqrtf(float v){return sqrtf(v);} static float ext_Sinf(float v){return sinf(v);}
static float clamp01(float v){return v<0.0f?0.0f:(v>1.0f?1.0f:v);}
static i32 h20_mem_readable(const void*p,u64 n){(void)n;return p!=0;}
static float h5755ea_world_units_per_meter(void){return 1.0f;}
/* Engine/controller state consumed by the production modules. */
static u8 g_s26diFrameHand[2]={1,1};static u64 fingerPacket[2][5];static int fingersValid[2]={1,1};
static i32 s26q_finger_values(i32 h,i32 f,float out[4]){if(!fingersValid[h])return 0;for(i32 d=0;d<4;d++)out[d]=((float*)&fingerPacket[h][f])[d&1];return 1;}
static float fallbackIndex[2];
static float h10_raw_finger_input(i32 h,i32 f){float cv[4];if(s26q_finger_values(h,f,cv))return f==0?(cv[1]+cv[2])*0.5f:(cv[1]+cv[2]+cv[3])/3.0f;return f==1?fallbackIndex[h]:0.0f;}
static void setFinger(int h,int f,float v){float* p=(float*)&fingerPacket[h][f];p[0]=p[1]=(f==0?v*0.55f:v);}
static void setHand(int h,float t,float i,float m,float r,float l){setFinger(h,0,t);setFinger(h,1,i);setFinger(h,2,m);setFinger(h,3,r);setFinger(h,4,l);}
static const void* g_h14GripBody[2];static u32 g_h30NativeMouseDown;static i32 g_h30NativeUseHand=-1;
static u8 g_s26qAnalogApplied[2];static u32 g_lastSqueezeActive[2]={1,1};static i32 g_lastSqueezeResult[2];static float g_lastSqueeze[2];
static u32 g_s26dlTouchKnown[2],g_s26dlTouched[2];
static float g_h14GrabMass[2];static u8 g_h15GripJointed[2];static u32 g_h14PhysicsSteps;
static float g_h14GripRel[2][16],g_h15GripHandAnchor[2][3],g_h32DriveHandAnchor[2][3];
static int haptics[2],hapticLevel[2];
enum{H576AC_HAPTIC_READY=1,H576AC_HAPTIC_CONFIRM=2,H576AC_HAPTIC_STRONG=3};
static void h576ac_queue_haptic(i32 h,u32 l){haptics[h]++;hapticLevel[h]=(int)l;}
static float g_s26ecForce[2];static u8 g_s26ecForceValid[2],g_s26ecFaceTouch[2][2],g_s26ecFaceTouchValid[2][2],g_s26ecLayers=7;
static u8 g_s26ecRawButtons[14],g_s26ecRawActive[14];
static int gameplay=1,paused=0;static i32 h5755dg_gameplay_vr(void){return gameplay;}static i32 h5754h_pause_active(void){return paused;}
static float tips[2][2][3];
static i32 h14_finger_tip_world(i32 h,i32 f,float c,const float*M,float*o){(void)c;(void)M;memcpy(o,tips[h][f],12);return 1;}
/* Haptic output mock */
static u32 g_frameCounter;static u8 g_h576acHapticReady=1;static Handle g_h576acHapticAction[2]={(Handle)1,(Handle)2};static volatile u32 g_h576acHapticPending[2];
static int applies[2];static float lastAmp[2],lastFreq[2];static i64 lastDur[2];
static i32 mock_apply(Handle s,const XrHapticActionInfo*i,const void*v){(void)s;int h=i->action==(Handle)2;const XrHapticVibration*x=v;applies[h]++;lastAmp[h]=x->amplitude;lastFreq[h]=x->frequency;lastDur[h]=x->duration;return 0;}
static i32 (*pApplyHaptic)(Handle,const XrHapticActionInfo*,const void*)=mock_apply;
typedef struct { u8 storage[16]; u64 size; u64 capacity; } H5730TString;
static H5730TString T(const char*z){H5730TString t;memset(&t,0,sizeof(t));t.size=strlen(z);t.capacity=15;memcpy(t.storage,z,t.size);return t;}
'''
gesture=(S/'gesture_ec.inc').read_text()
grip=(S/'grip_ec.inc').read_text()
main=r'''
static void resetGrip(void){for(int h=0;h<2;h++){s26ec_grip_reset(h);g_lastSqueeze[h]=0;g_lastSqueezeActive[h]=1;g_lastSqueezeResult[h]=0;}g_h14GripBody[0]=g_h14GripBody[1]=0;g_h30NativeMouseDown=0;g_h30NativeUseHand=-1;}
static float tick(int h,float squeeze,i64 t){g_lastSqueeze[h]=squeeze;s26ec_grip_tick(h,t);return g_lastSqueeze[h];}
int main(void){
 const i64 ms=1000000LL;Handle sess=(Handle)7;
 /* ---- settings bridge: VRCOMFORT U/Z/P/K/X/I ---- */
 const char* cls="UZPKXI";unsigned bits[6]={1,2,4,8,16,32};
 g_s26ecSettings=0;
 for(int k=0;k<6;k++){char c[2]={cls[k],0};H5730TString a=T(c),one=T("1"),zero=T("0"),bad=T("2");
  CHECK(s26ec_comfort_option(&a,&one)==1&&s26ec_option(bits[k]));CHECK(s26ec_comfort_option(&a,&bad)==0&&s26ec_option(bits[k]));
  CHECK(s26ec_comfort_option(&a,&zero)==1&&!s26ec_option(bits[k]));CHECK(s26ec_comfort_option(&a,&one)==1);}
 {H5730TString f=T("F"),one=T("1");CHECK(s26ec_comfort_option(&f,&one)==-1);}
 CHECK(g_s26ecSettings==63u);s26ec_set_option(S26EC_SET_ANY_FINGER,0);
 /* ---- finger normalisation ---- */
 S26ECFingers F;setHand(0,1,0.25f,0.5f,0.75f,1);CHECK(s26ec_fingers(0,&F)&&fabsf(F.thumb-1)<1e-5f&&fabsf(F.index-.25f)<1e-5f&&fabsf(s26ec_lower_three(&F)-.75f)<1e-5f);
 g_s26diFrameHand[0]=0;CHECK(!s26ec_fingers(0,&F));g_s26diFrameHand[0]=1;fingersValid[0]=0;CHECK(!s26ec_fingers(0,&F));fingersValid[0]=1;
 /* ---- POINT TO PRESS / ANY FINGER masks ---- */
 setHand(0,.5f,0,.8f,.8f,.8f);CHECK(s26ec_poke_mask(0,0)==2u);              /* point */
 setHand(0,.5f,0,.1f,.1f,.1f);CHECK(s26ec_poke_mask(0,0)==0u);              /* open hand: no new press */
 CHECK(s26ec_poke_mask(0,1)==2u);                                           /* engaged: index extended keeps it */
 setHand(0,.5f,.6f,.8f,.8f,.8f);CHECK(s26ec_poke_mask(0,1)==0u);             /* curled index always lifts */
 s26ec_set_option(S26EC_SET_POINT,0);setHand(0,.5f,0,.1f,.1f,.1f);CHECK(s26ec_poke_mask(0,0)==2u);s26ec_set_option(S26EC_SET_POINT,1);
 s26ec_set_option(S26EC_SET_ANY_FINGER,1);setHand(0,.5f,0,.1f,.9f,.2f);CHECK(s26ec_poke_mask(0,0)==(2u|4u|16u));setHand(0,.5f,.9f,.9f,.9f,.9f);CHECK(s26ec_poke_mask(0,0)==0u);s26ec_set_option(S26EC_SET_ANY_FINGER,0);
 fingersValid[1]=0;fallbackIndex[1]=.2f;CHECK(s26ec_poke_mask(1,0)==2u);fallbackIndex[1]=.6f;CHECK(s26ec_poke_mask(1,0)==0u);fingersValid[1]=1; /* non-skeletal: legacy gate */
 g_s26diFrameHand[1]=0;fallbackIndex[1]=.1f;CHECK(s26ec_poke_mask(1,0)==2u);g_s26diFrameHand[1]=1;
 /* ---- SMART GRIP: pinch ---- */
 resetGrip();setHand(0,.9f,.8f,.1f,.1f,.1f);CHECK(tick(0,.05f,1000*ms)>=.80f&&g_s26ecPinch[0]);
 setHand(0,.45f,.4f,.1f,.1f,.1f);CHECK(tick(0,.05f,1010*ms)>=.80f);         /* hysteresis keeps the pinch */
 setHand(0,.2f,.4f,.1f,.1f,.1f);CHECK(fabsf(tick(0,.05f,1020*ms)-.05f)<1e-5f&&!g_s26ecPinch[0]);
 setHand(0,.9f,.8f,.6f,.6f,.6f);CHECK(fabsf(tick(0,.6f,1030*ms)-.6f)<1e-5f&&!g_s26ecPinch[0]); /* whole hand is not a pinch */
 /* ---- SMART GRIP: closure only ---- */
 resetGrip();setHand(0,.1f,.1f,.9f,.9f,.9f);CHECK(fabsf(tick(0,.95f,2000*ms)-.50f)<1e-5f);   /* cannot start */
 CHECK(tick(0,.95f,2010*ms)>.28f);                                                          /* cannot drop a hold */
 g_s26dlTouchKnown[0]=3;g_s26dlTouched[0]=2;CHECK(fabsf(tick(0,.95f,2020*ms)-.95f)<1e-5f);   /* index resting on trigger = in use */
 g_s26dlTouched[0]=1;CHECK(fabsf(tick(0,.95f,2030*ms)-.95f)<1e-5f);g_s26dlTouchKnown[0]=g_s26dlTouched[0]=0;
 setHand(0,.5f,.5f,.9f,.9f,.9f);CHECK(fabsf(tick(0,.95f,2040*ms)-.95f)<1e-5f);
 /* ---- SMART GRIP: fast opening releases, no instant regrab ---- */
 for(int hz=72;hz<=144;hz+=36){
  resetGrip();i64 t=3000*ms,dt=1000000000LL/hz;g_h14GripBody[0]=(void*)1;setHand(0,.6f,.6f,.95f,.95f,.95f);
  for(int n=0;n<20;n++)CHECK(fabsf(tick(0,.95f,t+=dt)-.95f)<1e-5f);
  int fired=0;float g=.95f;for(int n=0;n<20&&!fired;n++){g-=.06f*(144.0f/hz);setHand(0,.6f,.6f,g,g,g);float e=tick(0,.9f,t+=dt);if(e==0.0f)fired=1;}
  CHECK(fired&&g>.5f);                       /* before the hand is really open */
  g_h14GripBody[0]=0;CHECK(fabsf(tick(0,.85f,t+=dt)-.27f)<1e-5f);  /* released: regrab blocked */
  CHECK(tick(0,.85f,t+=dt)<.28f);
  setHand(0,.6f,.6f,g+.2f,g+.2f,g+.2f);CHECK(fabsf(tick(0,.85f,t+=dt)-.85f)<1e-5f); /* deliberate re-close regrabs */
 }
 resetGrip();{i64 t=4000*ms;setHand(0,.6f,.6f,.95f,.95f,.95f);for(int n=0;n<10;n++)tick(0,.95f,t+=11*ms);
  setHand(0,.6f,.6f,.4f,.4f,.4f);CHECK(fabsf(tick(0,.4f,t+=11*ms)-.4f)<1e-5f);}  /* nothing held: no latch */
 resetGrip();{i64 t=5000*ms;g_h14GripBody[0]=(void*)1;float g=.95f;setHand(0,.6f,.6f,g,g,g);for(int n=0;n<10;n++)tick(0,.95f,t+=11*ms);
  int fired=0;for(int n=0;n<60;n++){g-=.005f;setHand(0,.6f,.6f,g,g,g);if(tick(0,g,t+=11*ms)==0.0f)fired=1;}CHECK(!fired);} /* slow opening: normal path */
 resetGrip();{i64 t=6000*ms;g_h14GripBody[0]=(void*)1;setHand(0,.9f,.8f,.1f,.1f,.1f);for(int n=0;n<10;n++)tick(0,.05f,t+=11*ms);
  setHand(0,.4f,.4f,.1f,.1f,.1f);CHECK(tick(0,.05f,t+=11*ms)==0.0f);g_h14GripBody[0]=0;CHECK(tick(0,.05f,t+=11*ms)<.28f);} /* pinch opening */
 resetGrip();{i64 t=7000*ms;g_h14GripBody[0]=(void*)1;setHand(0,.6f,.6f,.95f,.95f,.95f);for(int n=0;n<10;n++)tick(0,.95f,t+=11*ms);
  setHand(0,.6f,.6f,.6f,.6f,.6f);CHECK(tick(0,.9f,t+=11*ms)==0.0f);g_h14GripBody[0]=0;CHECK(tick(0,.9f,t+=11*ms)<.28f);
  CHECK(fabsf(tick(0,.9f,t+=1600*ms)-.9f)<1e-5f);}  /* latch times out */
 /* untouched controller value: option off, analog swap, invalid fingers, inactive action */
 resetGrip();setHand(0,.1f,.1f,.9f,.9f,.9f);
 s26ec_set_option(S26EC_SET_SMART_GRIP,0);CHECK(fabsf(tick(0,.95f,8000*ms)-.95f)<1e-5f);s26ec_set_option(S26EC_SET_SMART_GRIP,1);
 g_s26qAnalogApplied[0]=1;CHECK(fabsf(tick(0,.95f,8010*ms)-.95f)<1e-5f);g_s26qAnalogApplied[0]=0;
 fingersValid[0]=0;CHECK(fabsf(tick(0,.95f,8020*ms)-.95f)<1e-5f);fingersValid[0]=1;
 g_s26diFrameHand[0]=0;CHECK(fabsf(tick(0,.95f,8030*ms)-.95f)<1e-5f);g_s26diFrameHand[0]=1;
 g_lastSqueezeResult[0]=-1;CHECK(fabsf(tick(0,.95f,8040*ms)-.95f)<1e-5f);g_lastSqueezeResult[0]=0;
 CHECK(fabsf(tick(0,.95f,8050*ms)-.50f)<1e-5f);
 /* ---- pinch seating ---- */
 {float I[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1},bm[16];memcpy(bm,I,64);bm[12]=.30f;bm[13]=1.0f;bm[14]=.2f;
  float contact[3]={.31f,1.0f,.2f};tips[1][0][0]=.33f;tips[1][0][1]=1.01f;tips[1][0][2]=.2f;tips[1][1][0]=.35f;tips[1][1][1]=1.01f;tips[1][1][2]=.2f;
  g_s26ecPinch[1]=1;s26ec_pinch_seat(1,I,I,bm,contact,.2f);CHECK(fabsf(g_h14GripRel[1][12]-.33f)<1e-5f&&fabsf(g_h14GripRel[1][13]-1.01f)<1e-5f);
  CHECK(fabsf(g_h15GripHandAnchor[1][0]-.34f)<1e-5f&&fabsf(g_h32DriveHandAnchor[1][1]-1.01f)<1e-5f);
  memset(g_h14GripRel,0,sizeof(g_h14GripRel));s26ec_pinch_seat(1,I,I,bm,contact,1.5f);CHECK(g_h14GripRel[1][12]==0); /* too heavy */
  tips[1][1][0]=.50f;s26ec_pinch_seat(1,I,I,bm,contact,.2f);CHECK(g_h14GripRel[1][12]==0);                     /* too far */
  g_s26ecPinch[1]=0;tips[1][1][0]=.35f;s26ec_pinch_seat(1,I,I,bm,contact,.2f);CHECK(g_h14GripRel[1][12]==0);}   /* no pinch */
 /* ---- GRIP PRESSURE: heavy slip ---- */
 {const void* box=(void*)9;g_h14GripBody[0]=box;g_h14GrabMass[0]=10;g_s26ecForceValid[0]=1;g_s26ecForce[0]=0;haptics[0]=0;int slipped=0,at=0;
  for(int n=0;n<200&&!slipped;n++){g_h14PhysicsSteps++;if(s26ec_heavy_slip_step(0)){slipped=1;at=n;}}
  CHECK(slipped&&at>=45+23&&haptics[0]==1);
  g_s26ecHoldBody[0]=0;g_s26ecForce[0]=s26ec_heavy_force_needed(10);slipped=0;for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped);
  g_s26ecForce[0]=0;g_h14GripBody[1]=box;g_s26ecForceValid[1]=1;g_s26ecForce[1]=.5f;for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped); /* other hand carries it */
  g_h14GripBody[1]=0;g_s26ecForceValid[0]=0;for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped); /* no force sensing */
  g_s26ecForceValid[0]=1;g_h14GrabMass[0]=2;for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped); /* light */
  g_h14GrabMass[0]=10;g_h15GripJointed[0]=1;for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped);g_h15GripJointed[0]=0;
  s26ec_set_option(S26EC_SET_PRESSURE,0);for(int n=0;n<200;n++){g_h14PhysicsSteps++;slipped|=s26ec_heavy_slip_step(0);}CHECK(!slipped);s26ec_set_option(S26EC_SET_PRESSURE,1);
  CHECK(s26ec_heavy_force_needed(3)==.06f&&s26ec_heavy_force_needed(100)==.35f&&fabsf(s26ec_heavy_force_needed(10)-.20f)<1e-5f);
  g_h14GripBody[0]=0;}
 /* ---- GRIP PRESSURE: tear and wheel ---- */
 g_s26ecForceValid[0]=g_s26ecForceValid[1]=0;CHECK(s26ec_tear_scale(0)==1.0f);i32 v2[2]={1,1};CHECK(s26ec_wheel_cap(v2)==4.0f);
 g_s26ecForceValid[0]=1;g_s26ecForce[0]=.40f;CHECK(fabsf(s26ec_tear_scale(0)-1)<1e-5f);haptics[0]=0;g_s26ecForce[0]=.02f;CHECK(s26ec_tear_scale(0)==0.0f&&haptics[0]==1);
 CHECK(s26ec_tear_scale(0)==0.0f&&haptics[0]==1);g_s26ecForce[0]=.225f;CHECK(fabsf(s26ec_tear_scale(0)-.5f)<1e-4f);
 g_s26ecForce[0]=0;CHECK(fabsf(s26ec_wheel_cap(v2)-1.5f)<1e-5f);g_s26ecForce[0]=1;CHECK(fabsf(s26ec_wheel_cap(v2)-4.0f)<1e-5f);
 i32 vL[2]={1,0};g_s26ecForce[0]=.16f;CHECK(fabsf(s26ec_wheel_cap(vL)-2.75f)<1e-4f);
 s26ec_set_option(S26EC_SET_PRESSURE,0);CHECK(s26ec_tear_scale(0)==1.0f&&s26ec_wheel_cap(v2)==4.0f);s26ec_set_option(S26EC_SET_PRESSURE,1);
 /* ---- CREATURE HAPTICS ---- */
 CHECK(s26ec_static_amplitude(0,0,0,1)==0);float lo=s26ec_static_amplitude(.1f,0,0,1),hi=s26ec_static_amplitude(1,0,0,1);CHECK(lo>0&&hi>lo&&hi<=.75f);
 {float mn=1,mx=0;for(int k=0;k<100;k++){float a=s26ec_static_amplitude(1,1,k*.01f,1);if(a<mn)mn=a;if(a>mx)mx=a;}CHECK(mx-mn>.3f&&mx<=.75f);} /* throb when looked at */
 {H5730TString S_=T("S"),L=T("L"),Q=T("Q"),v=T("550"),bad=T("1e5"),big=T("2000");
  CHECK(s26ec_static_token(&S_,&v)&&g_s26ecStaticMilli==550&&!g_s26ecStaticLooked);CHECK(s26ec_static_token(&L,&v)&&g_s26ecStaticLooked);
  CHECK(!s26ec_static_token(&Q,&v));CHECK(!s26ec_static_token(&S_,&bad)&&g_s26ecStaticMilli==550);CHECK(!s26ec_static_token(&S_,&big));}
#define FRESH() (g_s26ecStaticFrame=g_frameCounter)
 i64 t=100000*ms;memset(applies,0,sizeof(applies));
 for(int n=0;n<90;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}
 CHECK(applies[0]>20&&applies[0]<70&&applies[1]==applies[0]&&lastDur[0]==S26EC_STATIC_PULSE_NS&&lastFreq[0]>=60&&lastFreq[0]<=100);
 g_s26ecSemanticFired[0]=1;int a0=applies[0],a1=applies[1];for(int n=0;n<3;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0&&applies[1]>a1); /* semantic pulse wins */
 g_h576acHapticPending[1]=2;a1=applies[1];for(int n=0;n<6;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[1]==a1);g_h576acHapticPending[1]=0;
 a0=applies[0];g_frameCounter+=60;for(int n=0;n<10;n++){g_frameCounter++;s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0); /* stale */
 {H5730TString S_=T("S"),z=T("0");s26ec_static_token(&S_,&z);}a0=applies[0];for(int n=0;n<10;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0);
 {H5730TString S_=T("S"),v=T("800");s26ec_static_token(&S_,&v);}
 paused=1;a0=applies[0];for(int n=0;n<10;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0);paused=0;
 gameplay=0;for(int n=0;n<10;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0);gameplay=1;
 s26ec_set_option(S26EC_SET_CREATURE,0);for(int n=0;n<10;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]==a0);s26ec_set_option(S26EC_SET_CREATURE,1);
 for(int n=0;n<10;n++){g_frameCounter++;FRESH();s26ec_static_tick(sess,t+=11*ms);}CHECK(applies[0]>a0);
 /* ---- BUTTON HINTS ---- */
 {S26ECHintHand H={-1,-1,0,0,0};i64 h0=200000*ms;
  s26ec_hint_step(&H,0,0,h0,0);for(int n=0;n<25;n++)s26ec_hint_step(&H,0,0,h0+=11*ms,.011f);CHECK(H.alpha==0);  /* rest delay */
  for(int n=0;n<20;n++)s26ec_hint_step(&H,0,0,h0+=11*ms,.011f);CHECK(H.alpha==1&&H.shown==0);
  s26ec_hint_step(&H,0,1,h0+=11*ms,.011f);for(int n=0;n<10;n++)s26ec_hint_step(&H,0,0,h0+=11*ms,.011f);CHECK(H.alpha==0&&H.suppressed); /* press fades until lift */
  for(int n=0;n<60;n++)s26ec_hint_step(&H,0,0,h0+=11*ms,.011f);CHECK(H.alpha==0);
  s26ec_hint_step(&H,-1,0,h0+=11*ms,.011f);for(int n=0;n<50;n++)s26ec_hint_step(&H,1,0,h0+=11*ms,.011f);CHECK(H.alpha==1&&H.shown==1&&!H.suppressed);
  s26ec_hint_step(&H,-1,0,h0+=11*ms,.011f);CHECK(H.alpha<1&&H.shown==1);}
 g_s26ecFaceTouchValid[1][0]=g_s26ecFaceTouchValid[1][1]=g_s26ecFaceTouchValid[0][0]=g_s26ecFaceTouchValid[0][1]=1;
 g_s26ecFaceTouch[1][0]=1;CHECK(s26ec_hint_source(1)==0);g_s26ecFaceTouch[1][1]=1;CHECK(s26ec_hint_source(1)==-1);g_s26ecFaceTouch[1][0]=0;CHECK(s26ec_hint_source(1)==1);
 g_s26ecFaceTouch[0][0]=1;CHECK(s26ec_hint_source(0)==2);g_s26ecFaceTouch[0][0]=0;g_s26ecFaceTouch[0][1]=1;CHECK(s26ec_hint_source(0)==3);
 g_s26ecFaceTouchValid[0][1]=0;CHECK(s26ec_hint_source(0)==-1);g_s26ecFaceTouchValid[0][1]=1;g_s26ecFaceTouch[0][1]=0;
 /* remapped role follows BUTTON BINDINGS: right B shows whatever role uses source 1 */
 g_s26nButtonMap=0x543210u;s26n_binding_swap(3,1);
 g_s26ecFaceTouch[1][0]=0;g_s26ecFaceTouch[1][1]=1;{i64 h0=300000*ms;for(int n=0;n<60;n++)s26ec_hint_tick(h0+=11*ms);}
 {u32 p=g_s26ecHintPacked;CHECK((p>>31)&&((p>>24)&1)==1&&((p>>16)&7)==1&&(i32)((p>>8)&255)-1==3&&(p&255)==255);}
 g_s26ecRawActive[1]=g_s26ecRawButtons[1]=1;{i64 h0=310000*ms;for(int n=0;n<20;n++)s26ec_hint_tick(h0+=11*ms);}CHECK(!(g_s26ecHintPacked>>31));g_s26ecRawButtons[1]=0;
 g_s26ecFaceTouch[1][1]=0;{i64 h0=320000*ms;for(int n=0;n<5;n++)s26ec_hint_tick(h0+=11*ms);}g_s26ecFaceTouch[1][1]=1;
 s26ec_set_option(S26EC_SET_HINTS,0);{i64 h0=330000*ms;for(int n=0;n<60;n++)s26ec_hint_tick(h0+=11*ms);}CHECK(!(g_s26ecHintPacked>>31));s26ec_set_option(S26EC_SET_HINTS,1);
 g_s26ecLayers=3;{i64 h0=340000*ms;for(int n=0;n<60;n++)s26ec_hint_tick(h0+=11*ms);}CHECK(!(g_s26ecHintPacked>>31));g_s26ecLayers=7;
 paused=1;{i64 h0=350000*ms;for(int n=0;n<60;n++)s26ec_hint_tick(h0+=11*ms);}CHECK(!(g_s26ecHintPacked>>31));paused=0;
 {i64 h0=360000*ms;for(int n=0;n<60;n++)s26ec_hint_tick(h0+=11*ms);}CHECK(g_s26ecHintPacked>>31);
 /* wrist label billboard: orthonormal, +Z toward the camera, origin at the anchor */
 {float M[16],pos[3]={1,1.2f,-2},cam[3]={0,1.7f,0};CHECK(s26ec_wrist_matrix(M,pos,cam));
  float x[3]={M[0],M[4],M[8]},y[3]={M[1],M[5],M[9]},z[3]={M[2],M[6],M[10]},tc[3]={cam[0]-pos[0],cam[1]-pos[1],cam[2]-pos[2]};
  float tl=sqrtf(tc[0]*tc[0]+tc[1]*tc[1]+tc[2]*tc[2]);
  CHECK(fabsf(x[0]*x[0]+x[1]*x[1]+x[2]*x[2]-1)<1e-4f&&fabsf(y[0]*y[0]+y[1]*y[1]+y[2]*y[2]-1)<1e-4f&&fabsf(x[0]*y[0]+x[1]*y[1]+x[2]*y[2])<1e-4f);
  CHECK((z[0]*tc[0]+z[1]*tc[1]+z[2]*tc[2])/tl>.999f&&y[1]>0&&M[3]==pos[0]&&M[7]==pos[1]&&M[11]==pos[2]);
  float above[3]={0,5,0};CHECK(!s26ec_wrist_matrix(M,above,(float[3]){0,0,0}));}
 printf("PASS: %d production HANDS AND HAPTICS checks (settings bridge, point/any-finger masks, pinch, closure-only, finger-open release at 72-144 Hz, pinch seating, heavy slip, tear/wheel pressure, creature haptics, button hints)\n",checks);return 0;
}
'''
helpers=''.join(fn(n) for n in ['h10_copy_f','h10_identity','h10_matmul','h14_transform_point','h14_rigid_inverse','h11_parse_float'])
helpers+='static float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}\n'
sso=fn('h5748t_sso_eq');copy=fn('h5748n_copy_tstring')
c=B/'hands_haptics_test.c'
c.write_text(types+'\n'+defines+'\n'+header+helpers+sso+copy+gesture+grip+pressure+haptics+comfort+remap+hintLogic+fn('s26ec_wrist_matrix',hint)+main)
exe=B/'hands_haptics_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-Wall','-Wno-unused-function','-Wno-unused-variable','-I',str(S),str(c),'-o',str(exe),'-lm'],check=True)
subprocess.run([str(exe)],check=True)
src=s
for wire in ['s26ec_grip_tick(i,displayTime)','s26ec_static_tick(sess,displayTime)','s26ec_hint_tick(displayTime)','s26ec_index_tick(sess,g_lastSyncResult==0)',
             'else if(s26ec_heavy_slip_step(h))h14_release(h,"grip pressure slipped")','if(!jointed)s26ec_pinch_seat(hand,handM,gripHand,bm,contact,mass)',
             'float grip=s26ec_tear_scale(hand);if(grip<=0.0f)return;','float cap=s26ec_wheel_cap(valid);','u32 mask=s26ec_poke_mask(hand,engaged);',
             '__atomic_store_n(&g_s26ecSemanticFired[h],1u,__ATOMIC_RELEASE);','set==g_s26ecWristSet','"VRWRIST"','"VRHAPT"']:
    assert wire in src,wire
assert '!(s26ec_poke_mask(h,0)&2u)' in (S/'phone_x.inc').read_text()
dist=(R/'runtime/script/modules/DistortionEffectsHandler.hps').read_text(encoding='utf-8')
assert 'cScript_RunGlobalFunc("VRHAPT",bVRLookedAt ? "L" : "S"' in dist and 'cScript_RunGlobalFunc("VRHAPT","S","0")' in dist
hh=(R/'runtime/script/modules/HintHandler.hps').read_text(encoding='utf-8')
assert 'HPL3VR_DrawWristHint();' in hh and 'cGui_GetSetFromName("VR_WristHint")' in hh
print('PASS: production wiring for grip, pressure, poke, haptics, hints and script producers')
