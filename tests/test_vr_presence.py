"""Execute the production S26ED presence/performance logic against mocked
engine, OpenGL and OpenXR state: head-tap flashlight zone and tap gating,
hand-over-hand ladder input, render scale persistence and parsing, the
texture budget menu toggle, and the depth-for-reprojection pipeline
(engine attachment discovery, per-eye depth copy, swapchain lifecycle and
xrEndFrame chaining). Contract tests only; feel, the body pose and the
runtime's use of submitted depth still need a headset.
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
def block(opener):
    """The production if-block starting at opener, braces matched."""
    a=s.index(opener);brace=s.index('{',a);depth=0
    for i in range(brace,len(s)):
        depth+=(s[i]=='{')-(s[i]=='}')
        if depth==0:return s[a:i+1]
def typedef(name):
    m=re.search(r'^typedef[^\n]*\*'+name+r'\)[^\n]*\n',s,re.M)
    if not m:raise SystemExit('typedef not found: '+name)
    return m.group(0)
types=s[s.index('typedef unsigned char'):s.index('#define XR_SUCCESS')]
defines='\n'.join(x for x in s.splitlines() if x.startswith('#define XR_'))
swap=s[s.index('#define H5754H_XR_TYPE_SWAPCHAIN_CREATE_INFO'):s.index('/* Retired Pause/OpenXR lifetime census')]
pfn=''.join(typedef(n) for n in ['PFN_H5754AQ_CheckFramebufferStatus','PFN_GIPA','PFN_H5750A_WglGetProcAddress','PFN_H5750V_BindFramebuffer',
    'PFN_H5750V_BlitFramebuffer','PFN_H5750V_ReadBuffer','PFN_H5750Y_GenFramebuffers','PFN_H5750Y_FramebufferTexture2D'])
gesture=(S/'gesture_ec.inc').read_text();gesture=gesture[:gesture.index('/* Normalised curls')]
tstring='typedef struct { u8 storage[16]; u64 size; u64 capacity; } H5730TString;\n'
renderO=block('if(h5748t_sso_eq(className,"O",1u)){')
ladderMsg=block('if(h5748t_sso_eq(objectName,"VRLADDER",8u)){')

header=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
static int checks;
'''
mocks=r'''
static void zero_bytes(void*p,u32 n){memset(p,0,n);}
static int logs;static void ext_Log(const char*f,...){(void)f;logs++;}
static i32 h20_mem_readable(const void*p,u64 n){(void)n;return p!=0;}
static i32 h20_mem_executable(const void*p){return p!=0;}
/* ---- engine options / runtime ---- */
static u8 g_s26edDepthExtension=1;
static volatile u32 g_s26edOnLadder;
static i32 g_h576mScriptRuntimePublished=1,xrOn=1,xrRunning=1;
static i32 p2_xr_on(void){return xrOn;}static i32 p2_xr_running(void){return xrRunning;}
static float upm=1.0f;static float h5755ea_world_units_per_meter(void){return upm;}
/* ---- in-memory files for render scale ---- */
typedef struct {char data[64];u32 size,pos;int used;} MemFile;
static MemFile scaleFile;static int fileWrites,fileOpens;
static i32 make_sibling_path(char* out,u32 cap,const char* leaf){snprintf(out,cap,"C:\\SOMA\\%s",leaf);return 1;}
static void* ext_fopen(const char*p,const char*m){fileOpens++;if(!strstr(p,"hpl3vr_render_scale.txt"))return 0;
 if(m[0]=='r'){if(!scaleFile.used)return 0;scaleFile.pos=0;return &scaleFile;}scaleFile.used=1;scaleFile.size=0;scaleFile.pos=0;fileWrites++;return &scaleFile;}
static u64 ext_fread(void*d,u64 sz,u64 n,void*f){MemFile*m=f;u64 want=sz*n,left=m->size-m->pos;if(want>left)want=left;memcpy(d,m->data+m->pos,want);m->pos+=(u32)want;return want/sz;}
static u64 ext_fwrite(const void*d,u64 sz,u64 n,void*f){MemFile*m=f;memcpy(m->data+m->size,d,sz*n);m->size+=(u32)(sz*n);return n;}
static i32 ext_fclose(void*f){(void)f;return 0;}
/* ---- texture budget: fake Soma.exe image ---- */
static u8* somaImage;
static void* ext_GetModuleHandleA(const char*n){return n?(void*)1:(void*)somaImage;}
/* ---- OpenGL ---- */
static i32 curRead=7,curDraw=7,curRb=3;static u8 scissor=1,depthMaskV=0;static u32 pendingErr,errAtBlit;
static i32 engType=0x8D41,engName=11,engD=24,engS=8,engComp=0x8C17,stType=0x8D41,stName=11,engLevel=0,engLayered=0;
static i32 rbW=1500,rbH=1600,texW=1500,texH=1600,texLevelAvailable=1,attachQueries;
typedef struct {u32 kind,name,point;} Att;static Att att[128];static u32 genNext=40;
static i32 blits,bx[8];static u32 bmask,bfilter,blitReadName,blitDrawName,blitPoint;static u8 blitScissor,blitMask;
static u32 lastReadBuffer=99,lastDrawBuffer=99;
static i32 bound(u32 t){return t==0x8CA8u?curRead:curDraw;}
static void __attribute__((ms_abi)) gl_Bind(u32 t,u32 f){if(t==0x8CA8u||t==0x8D40u)curRead=(i32)f;if(t==0x8CA9u||t==0x8D40u)curDraw=(i32)f;}
static void __attribute__((ms_abi)) gl_Blit(i32 a,i32 b,i32 c,i32 d,i32 e,i32 f,i32 g,i32 h,u32 m,u32 fl){
 blits++;bx[0]=a;bx[1]=b;bx[2]=c;bx[3]=d;bx[4]=e;bx[5]=f;bx[6]=g;bx[7]=h;bmask=m;bfilter=fl;
 blitReadName=att[curRead].name;blitDrawName=att[curDraw].name;blitPoint=att[curDraw].point;blitScissor=scissor;blitMask=depthMaskV;if(errAtBlit)pendingErr=errAtBlit;}
static void __attribute__((ms_abi)) gl_ReadBuffer(u32 b){lastReadBuffer=b;}
static void __attribute__((ms_abi)) gl_DrawBuffer(u32 b){lastDrawBuffer=b;}
static void __attribute__((ms_abi)) gl_Gen(i32 n,u32*ids){for(i32 i=0;i<n;i++)ids[i]=genNext++;}
static void __attribute__((ms_abi)) gl_FbTex2D(u32 t,u32 point,u32 tt,u32 tex,i32 lvl){(void)tt;(void)lvl;Att*a=&att[bound(t)];a->kind=tex?2:0;a->name=tex;a->point=point;}
static void __attribute__((ms_abi)) gl_AttachRb(u32 t,u32 point,u32 rt,u32 rb){(void)rt;Att*a=&att[bound(t)];a->kind=rb?1:0;a->name=rb;a->point=point;}
static void __attribute__((ms_abi)) gl_AttachTex(u32 t,u32 point,u32 tex,i32 lvl){(void)lvl;Att*a=&att[bound(t)];a->kind=tex?3:0;a->name=tex;a->point=point;}
static u32 __attribute__((ms_abi)) gl_Check(u32 t){return att[bound(t)].name?0x8CD5u:0x8CD6u;}
static void __attribute__((ms_abi)) gl_AttachParam(u32 t,u32 attachment,u32 pname,i32*out){
 attachQueries++;*out=0;if(bound(t)!=7)return;
 if(attachment==0x8D00u){if(pname==0x8CD0u)*out=engType;if(pname==0x8CD1u)*out=engName;if(pname==0x8216u)*out=engD;if(pname==0x8217u)*out=engS;
  if(pname==0x8211u)*out=engComp;if(pname==0x8CD2u)*out=engLevel;if(pname==0x8DA7u)*out=engLayered;}
 if(attachment==0x8D20u){if(pname==0x8CD0u)*out=stType;if(pname==0x8CD1u)*out=stName;}}
static void __attribute__((ms_abi)) gl_BindRb(u32 t,u32 rb){(void)t;curRb=(i32)rb;}
static void __attribute__((ms_abi)) gl_RbParam(u32 t,u32 p,i32*out){(void)t;*out=0;if(curRb!=engName)return;if(p==0x8D42u)*out=rbW;if(p==0x8D43u)*out=rbH;}
static void __attribute__((ms_abi)) gl_TexLevelParam(u32 tex,i32 lvl,u32 p,i32*out){*out=0;if(tex!=(u32)engName||lvl)return;if(p==0x1000u)*out=texW;if(p==0x1001u)*out=texH;}
static u32 __attribute__((ms_abi)) gl_GetError(void){u32 e=pendingErr;pendingErr=0;return e;}
static void __attribute__((ms_abi)) gl_GetBooleanv(u32 p,u8*o){if(p==0x0B72u)*o=depthMaskV;}
static void __attribute__((ms_abi)) gl_DepthMask(u8 v){depthMaskV=v;}
static void* __attribute__((ms_abi)) mock_wgl(const char*n){
 if(!strcmp(n,"glGetFramebufferAttachmentParameteriv"))return (void*)gl_AttachParam;if(!strcmp(n,"glFramebufferRenderbuffer"))return (void*)gl_AttachRb;
 if(!strcmp(n,"glFramebufferTexture"))return (void*)gl_AttachTex;if(!strcmp(n,"glBindRenderbuffer"))return (void*)gl_BindRb;
 if(!strcmp(n,"glGetRenderbufferParameteriv"))return (void*)gl_RbParam;if(!strcmp(n,"glGetTextureLevelParameteriv"))return texLevelAvailable?(void*)gl_TexLevelParam:0;return 0;}
static void* ext_GetProcAddress(void*m,const char*n){(void)m;
 if(!strcmp(n,"glDrawBuffer"))return (void*)gl_DrawBuffer;if(!strcmp(n,"glGetError"))return (void*)gl_GetError;
 if(!strcmp(n,"glGetBooleanv"))return (void*)gl_GetBooleanv;if(!strcmp(n,"glDepthMask"))return (void*)gl_DepthMask;return 0;}
static void ext_glGetIntegerv(u32 p,i32*o){*o=0;if(p==0x8CA6u)*o=curDraw;if(p==0x8CAAu)*o=curRead;if(p==0x8CA7u)*o=curRb;}
static u8 ext_glIsEnabled(u32 c){return c==0x0C11u?scissor:0;}
static void ext_glEnable(u32 c){if(c==0x0C11u)scissor=1;}static void ext_glDisable(u32 c){if(c==0x0C11u)scissor=0;}
static PFN_H5750A_WglGetProcAddress p_h5750aWglGetProcAddress;static void h5750a_resolve_swap_interval(void){p_h5750aWglGetProcAddress=mock_wgl;}
static PFN_H5750V_ReadBuffer p_h5750vReadBuffer;static void h5750v_resolve_read_buffer(void){p_h5750vReadBuffer=gl_ReadBuffer;}
static PFN_H5754AQ_CheckFramebufferStatus p_s26CheckResolveFbo;static i32 s26_resolve_validation_ready(void){p_s26CheckResolveFbo=gl_Check;return 1;}
static PFN_H5750Y_GenFramebuffers h5750y_gen_fbo(void){return gl_Gen;}
static PFN_H5750Y_FramebufferTexture2D h5750y_fbo_tex2d(void){return gl_FbTex2D;}
static PFN_H5750V_BindFramebuffer h5750v_bind_fbo(void){return gl_Bind;}
static PFN_H5750V_BlitFramebuffer h5750v_blit(void){return gl_Blit;}
static i32 geomOK=1,geomCalls,geomW,geomH;
static i32 h5750x_eye_geometry(i32 eye,i32 rw,i32 rh,i32 crop[4],i32*nw,i32*nh){(void)eye;(void)nw;(void)nh;geomCalls++;geomW=rw;geomH=rh;
 if(!geomOK)return 0;crop[0]=rw/10;crop[1]=rh/20;crop[2]=crop[0]+1000;crop[3]=crop[1]+1100;return 1;}
/* ---- OpenXR ---- */
static u8 xrobj[0x300];static void* p2_xr_obj(void){return xrobj;}
static int offerD24=1,offer32F=0,creates,destroys,acquires,waits,releases,createFail,acquireFail,waitResult;static H5754HSwapchainCreateInfo lastCi;
static u32 acqNext[16];static int heldImage[16];
static i32 __attribute__((ms_abi)) xr_formats(Handle sess,u32 cap,u32*n,i64*f){(void)sess;i64 all[3];u32 k=0;all[k++]=0x8C43;if(offerD24)all[k++]=0x88F0;if(offer32F)all[k++]=0x8CAC;
 *n=k;if(cap){if(cap<k)return -1;memcpy(f,all,k*sizeof(i64));}return 0;}
static i32 __attribute__((ms_abi)) xr_create(Handle sess,const H5754HSwapchainCreateInfo*ci,Handle*out){(void)sess;lastCi=*ci;if(createFail)return -2;*out=(Handle)(u64)(0x100+creates++);return 0;}
static i32 __attribute__((ms_abi)) xr_destroy(Handle h){(void)h;destroys++;return 0;}
static i32 __attribute__((ms_abi)) xr_images(Handle sw,u32 cap,u32*n,H5754HSwapchainImageGL*img){*n=3;if(cap){for(u32 i=0;i<3;i++){if(img[i].type!=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_KHR)return -3;img[i].image=500+10*(u32)((u64)sw-0x100)+i;}}return 0;}
static i32 __attribute__((ms_abi)) xr_acquire(Handle sw,const H5754HAcquireInfo*ai,u32*idx){if(ai->type!=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_ACQUIRE_INFO||acquireFail)return -4;u32 k=(u32)((u64)sw-0x100)&15u;*idx=acqNext[k]++%3u;heldImage[k]=1;acquires++;return 0;}
static i32 __attribute__((ms_abi)) xr_wait(Handle sw,const H5754HWaitInfo*wi){(void)sw;if(wi->type!=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_WAIT_INFO||wi->timeout<=0)return -5;waits++;return waitResult;}
static i32 __attribute__((ms_abi)) xr_release(Handle sw,const H5754HReleaseInfo*ri){if(ri->type!=H5754H_XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO)return -6;heldImage[(u32)((u64)sw-0x100)&15u]=0;releases++;return 0;}
static i32 __attribute__((ms_abi)) xr_gipa(Handle inst,const char*n,void**out){(void)inst;*out=0;
 if(!strcmp(n,"xrEnumerateSwapchainFormats"))*out=(void*)xr_formats;if(!strcmp(n,"xrCreateSwapchain"))*out=(void*)xr_create;
 if(!strcmp(n,"xrDestroySwapchain"))*out=(void*)xr_destroy;if(!strcmp(n,"xrEnumerateSwapchainImages"))*out=(void*)xr_images;
 if(!strcmp(n,"xrAcquireSwapchainImage"))*out=(void*)xr_acquire;if(!strcmp(n,"xrWaitSwapchainImage"))*out=(void*)xr_wait;
 if(!strcmp(n,"xrReleaseSwapchainImage"))*out=(void*)xr_release;return *out?0:-1;}
/* ---- haptics (ladder rungs) ---- */
'''
production=(S/'head_tap_ed.inc').read_text()+(S/'ladder_ed.inc').read_text()+(S/'render_scale_ed.inc').read_text()+\
    (S/'texture_streaming_i.inc').read_text()+(S/'depth_ed.inc').read_text()
wrappers=r'''
static i32 h5748t_sso_eq(const H5730TString* s,const char* lit,u32 n);
'''+fn('h5748t_sso_eq')+fn('h5748n_copy_tstring')+r'''
static u64 vrcomfort_O(const H5730TString* className,const H5730TString* functionName){
 '''+renderO+r'''
 return 99u;
}
static u64 vrladder(const H5730TString* objectName,const H5730TString* functionName){
 '''+ladderMsg+r'''
 return 99u;
}
'''
main=r'''
static H5730TString T(const char*z){H5730TString t;memset(&t,0,sizeof(t));t.size=strlen(z);t.capacity=15;memcpy(t.storage,z,t.size);return t;}
/* Independent oracle: rotate v by unit quaternion q (x,y,z,w). */
static void qrot(const float q[4],const float v[3],float o[3]){
 float x=q[0],y=q[1],z=q[2],w=q[3];float t[3]={2*(y*v[2]-z*v[1]),2*(z*v[0]-x*v[2]),2*(x*v[1]-y*v[0])};
 o[0]=v[0]+w*t[0]+(y*t[2]-z*t[1]);o[1]=v[1]+w*t[1]+(z*t[0]-x*t[2]);o[2]=v[2]+w*t[2]+(x*t[1]-y*t[0]);}
static void axisq(float ax,float ay,float az,float deg,float q[4]){float n=sqrtf(ax*ax+ay*ay+az*az),h=deg*3.14159265f/360.0f,s=sinf(h)/n;q[0]=ax*s;q[1]=ay*s;q[2]=az*s;q[3]=cosf(h);}
static void qmul(const float a[4],const float b[4],float o[4]){
 o[3]=a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2];o[0]=a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1];
 o[1]=a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0];o[2]=a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3];}
static void perspective(float* p,float n,float f){memset(p,0,64);p[0]=0.6f;p[5]=0.58f;p[10]=-(f+n)/(f-n);p[11]=-1.0f;p[14]=-2.0f*f*n/(f-n);}
static u8 renderer[0xc00];
static void setRenderer(i32 w,i32 h,float n,float f){*(i32*)(renderer+0x40)=w;*(i32*)(renderer+0x44)=h;perspective((float*)(renderer+0xaa4),n,f);}
static void session(u64 h){*(Handle*)(xrobj+0x20)=(Handle)h;}
static void eyeRender(i32 eye){g_s26edDepthSeen[eye]=0;s26ed_depth_observe(renderer,eye);s26ed_depth_capture(eye);}
int main(void){
 /* =========== 1. HEAD TAP: crown zone in the HMD frame =========== */
 {
  float id[4]={0,0,0,1};
  float crown[3]={0,0.15f,0.05f},front[3]={0,0.15f,-0.12f},ear[3]={0.11f,0.02f,0.05f},chin[3]={0,-0.12f,-0.05f},side[3]={0.20f,0.15f,0.05f},high[3]={0,0.40f,0.05f},back[3]={0,0.15f,0.18f};
  CHECK(s26ed_crown_zone(id,crown,0));CHECK(!s26ed_crown_zone(id,front,0));CHECK(!s26ed_crown_zone(id,ear,0));CHECK(!s26ed_crown_zone(id,chin,0));
  CHECK(!s26ed_crown_zone(id,side,0));CHECK(!s26ed_crown_zone(id,high,0));CHECK(s26ed_crown_zone(id,back,0));
  float edge[3]={0,0.15f,-0.08f};CHECK(!s26ed_crown_zone(id,edge,0));CHECK(s26ed_crown_zone(id,edge,S26ED_CROWN_EXIT_PAD));
  /* The zone follows the head: any orientation, hand placed on the rotated crown. */
  int tested=0;
  for(int yaw=-180;yaw<180;yaw+=30)for(int pitch=-70;pitch<=70;pitch+=35)for(int roll=-40;roll<=40;roll+=40){
   float qy[4],qp[4],qr[4],t[4],q[4];axisq(0,1,0,(float)yaw,qy);axisq(1,0,0,(float)pitch,qp);axisq(0,0,1,(float)roll,qr);qmul(qy,qp,t);qmul(t,qr,q);
   float d[3];qrot(q,crown,d);CHECK(s26ed_crown_zone(q,d,0));
   qrot(q,front,d);CHECK(!s26ed_crown_zone(q,d,0));qrot(q,ear,d);CHECK(!s26ed_crown_zone(q,d,0));qrot(q,chin,d);CHECK(!s26ed_crown_zone(q,d,0));
   /* World-up above the eyes is not the crown when looking far down. */
   if(pitch<=-70&&roll==0){float up[3]={0,0.15f,0};CHECK(!s26ed_crown_zone(q,up,0));}
   tested++;}
  CHECK(tested==12*5*3);
  float bad[4]={0,0,0,2};CHECK(!s26ed_crown_zone(bad,crown,0));float nanq[4]={NAN,0,0,1};CHECK(!s26ed_crown_zone(nanq,crown,0));
  float nand[3]={NAN,0.15f,0.05f};CHECK(!s26ed_crown_zone(id,nand,0));
 }
 /* =========== 2. HEAD TAP: one toggle per touch =========== */
 {
  S26EDTap t;memset(&t,0,sizeof(t));t.armed[0]=t.armed[1]=0;const i64 ms=1000000LL;
  i32 in0[2]={0,0},near0[2]={0,0},el[2]={1,1};
  /* Starts armed only after the hand is seen outside the zone. */
  i32 in1[2]={1,0},near1[2]={1,0};CHECK(s26ed_tap_step(&t,in1,near1,el,1000*ms)==-1);
  CHECK(s26ed_tap_step(&t,in0,near0,el,1010*ms)==-1);
  CHECK(s26ed_tap_step(&t,in1,near1,el,1020*ms)==0);
  for(int k=0;k<50;k++)CHECK(s26ed_tap_step(&t,in1,near1,el,(1030+k*11)*ms)==-1); /* holding does not repeat */
  i32 pad[2]={0,0},padNear[2]={1,0};CHECK(s26ed_tap_step(&t,pad,padNear,el,1700*ms)==-1); /* jitter in the exit pad does not re-arm */
  CHECK(s26ed_tap_step(&t,in1,near1,el,1710*ms)==-1);
  CHECK(s26ed_tap_step(&t,in0,near0,el,1800*ms)==-1);CHECK(s26ed_tap_step(&t,in1,near1,el,1810*ms)==0);
  /* Cooldown: a quick second touch inside 0.6 s is ignored and must leave again. */
  CHECK(s26ed_tap_step(&t,in0,near0,el,1900*ms)==-1);CHECK(s26ed_tap_step(&t,in1,near1,el,2000*ms)==-1);
  CHECK(s26ed_tap_step(&t,in1,near1,el,2500*ms)==-1);
  CHECK(s26ed_tap_step(&t,in0,near0,el,2510*ms)==-1);CHECK(s26ed_tap_step(&t,in1,near1,el,2520*ms)==0);
  /* A hand holding something never fires and must leave before it can. */
  CHECK(s26ed_tap_step(&t,in0,near0,el,4000*ms)==-1);i32 busy[2]={0,1};
  CHECK(s26ed_tap_step(&t,in1,near1,busy,4100*ms)==-1);CHECK(s26ed_tap_step(&t,in1,near1,el,4200*ms)==-1);
  CHECK(s26ed_tap_step(&t,in0,near0,el,4300*ms)==-1);CHECK(s26ed_tap_step(&t,in1,near1,el,4400*ms)==0);
  /* Both hands arrive together: exactly one toggle. */
  i32 both[2]={1,1};CHECK(s26ed_tap_step(&t,in0,near0,el,6000*ms)==-1);CHECK(s26ed_tap_step(&t,both,both,el,6100*ms)==0);
  CHECK(s26ed_tap_step(&t,both,both,el,7000*ms)==-1);
  i32 rightOnly[2]={0,1};CHECK(s26ed_tap_step(&t,in0,near0,el,8000*ms)==-1);CHECK(s26ed_tap_step(&t,rightOnly,rightOnly,el,8100*ms)==1);
 }
 /* =========== 3. LADDER: hand pulls become climb input =========== */
 {
  S26EDLadder L;s26ed_ladder_reset(&L);i32 grip[2]={1,0};float y[2]={1.2f,1.0f};i32 rung=-1,rungs=0;i64 t=1000000000LL;const i64 dt=11111111LL;
  CHECK(s26ed_ladder_step(&L,grip,y,t,&rung)==0.0f&&rung==-1); /* first sample only anchors */
  float c=0;for(int k=0;k<90;k++){t+=dt;y[0]-=0.9f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);if(rung>=0){CHECK(rung==0);rungs++;}}
  CHECK(c>0.95f&&c<=1.0f);CHECK(rungs==2||rungs==3);
  /* Half speed is roughly half input. */
  for(int k=0;k<60;k++){t+=dt;y[0]-=0.45f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(fabsf(c-0.5f)<0.03f);
  /* Pushing up climbs down. */
  for(int k=0;k<60;k++){t+=dt;y[0]+=0.9f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c<-0.95f);
  /* Holding still decays to exactly 0 quickly. */
  for(int k=0;k<40;k++){t+=dt;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c==0.0f);
  /* Deadzone: tracking drift never climbs. */
  for(int k=0;k<60;k++){t+=dt;y[0]-=0.03f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c==0.0f);
  /* Releasing grip ends the pull. */
  for(int k=0;k<20;k++){t+=dt;y[0]-=0.9f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c>0.5f);
  grip[0]=0;for(int k=0;k<40;k++){t+=dt;y[0]-=0.9f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c==0.0f);
  /* Re-grabbing never jumps: the new hand height is only an anchor. */
  grip[0]=1;y[0]=0.2f;t+=dt;c=s26ed_ladder_step(&L,grip,y,t,&rung);CHECK(c==0.0f);
  /* A frame hitch re-anchors instead of producing a huge pull. */
  t+=200000000LL;y[0]-=0.5f;c=s26ed_ladder_step(&L,grip,y,t,&rung);CHECK(c==0.0f);
  /* Two hands: the larger pull wins (hand over hand). */
  grip[0]=grip[1]=1;y[0]=1.0f;y[1]=1.0f;t+=dt;s26ed_ladder_step(&L,grip,y,t,&rung);
  for(int k=0;k<60;k++){t+=dt;y[0]+=0.2f/90.0f;y[1]-=0.9f/90.0f;c=s26ed_ladder_step(&L,grip,y,t,&rung);}CHECK(c>0.95f);
  float bad[2]={NAN,1.0f};i32 g2[2]={1,0};t+=dt;s26ed_ladder_step(&L,g2,bad,t,&rung);CHECK(L.holding[0]==0&&L.holding[1]==0); /* untracked height drops the hold */
 }
 /* =========== 4. VRLADDER messages =========== */
 {
  H5730TString on=T("1"),off=T("0"),q=T("Q"),bad=T("X"),obj=T("VRLADDER"),other=T("VRSCENE");
  g_s26ecSettings=S26EC_SET_LADDER;CHECK(vrladder(&obj,&on)==1u&&g_s26edOnLadder==1u);CHECK(vrladder(&obj,&q)==1u);
  CHECK(vrladder(&obj,&off)==1u&&g_s26edOnLadder==0u);CHECK(vrladder(&obj,&bad)==0u);CHECK(vrladder(&other,&on)==99u);
  g_s26ecSettings=0;CHECK(vrladder(&obj,&q)==0u);
 }
 /* =========== 5. RENDER SCALE =========== */
 {
  CHECK(S26ED_SCALE_INDEX_MAX==18u);CHECK(s26ed_scale_from_index(0)==60u&&s26ed_scale_from_index(8)==100u&&s26ed_scale_from_index(18)==150u&&s26ed_scale_from_index(99)==150u);
  u32 v=0;CHECK(s26ed_parse_scale("100\n",4,&v)&&v==100u);CHECK(s26ed_parse_scale(" 125\r\n",6,&v)&&v==125u);CHECK(s26ed_parse_scale("60",2,&v)&&v==60u);
  v=7;CHECK(!s26ed_parse_scale("101",3,&v)&&v==7u);CHECK(!s26ed_parse_scale("55",2,&v));CHECK(!s26ed_parse_scale("155",3,&v));CHECK(!s26ed_parse_scale("abc",3,&v));
  CHECK(!s26ed_parse_scale("",0,&v));CHECK(!s26ed_parse_scale("100x",4,&v));CHECK(!s26ed_parse_scale("01000",5,&v));
  CHECK(s26ed_scaled_dim(2016,100)==2016&&s26ed_scaled_dim(2017,100)==2017); /* 1:1 at 100% keeps the runtime size exactly */
  CHECK(s26ed_scaled_dim(2016,125)==2520&&s26ed_scaled_dim(1000,60)==600&&s26ed_scaled_dim(1001,110)==1102&&s26ed_scaled_dim(1001,105)==1052);
  for(i32 w=400;w<=4000;w+=37)for(u32 pct=60;pct<=150;pct+=5){i32 o=s26ed_scaled_dim(w,pct);CHECK((o&1)==0||pct==100u);CHECK(o>=w*(i32)pct/100);CHECK(o<=w*(i32)pct/100+3);}
  CHECK(s26ed_scaled_dim(7000,150)==8192);CHECK(s26ed_scaled_dim(0,150)==0);CHECK(s26ed_scaled_dim(2000,99)==2000);
  /* Persistence: missing file keeps 100; requests write once; this session keeps its scale. */
  s26ed_load_render_scale();CHECK(g_s26edScaleActive==100u&&g_s26edScaleRequested==100u);
  H5730TString O=T("O"),i13=T("13"),a13=T("A13"),a8=T("A8"),i8=T("8"),bad=T("19"),bad2=T("A"),bad3=T("1a"),bad4=T("123");
  CHECK(vrcomfort_O(&O,&a8)==1u&&vrcomfort_O(&O,&a13)==0u);
  int w0=fileWrites;CHECK(vrcomfort_O(&O,&i13)==1u&&fileWrites==w0+1);CHECK(scaleFile.size==4&&!memcmp(scaleFile.data,"125\n",4));
  CHECK(vrcomfort_O(&O,&i13)==1u&&fileWrites==w0+1);CHECK(g_s26edScaleActive==100u&&vrcomfort_O(&O,&a8)==1u);
  CHECK(vrcomfort_O(&O,&bad)==0u&&vrcomfort_O(&O,&bad2)==0u&&vrcomfort_O(&O,&bad3)==0u&&vrcomfort_O(&O,&bad4)==0u&&fileWrites==w0+1);
  H5730TString i0=T("0");CHECK(vrcomfort_O(&O,&i0)==1u&&scaleFile.size==3&&!memcmp(scaleFile.data,"60\n",3));
  CHECK(vrcomfort_O(&O,&i8)==1u&&!memcmp(scaleFile.data,"100\n",4));
  /* Next launch reads it back. */
  memcpy(scaleFile.data,"135\n",4);scaleFile.size=4;g_s26edScaleLoaded=0;g_s26edScaleActive=g_s26edScaleRequested=100;s26ed_load_render_scale();
  CHECK(g_s26edScaleActive==135u&&g_s26edScaleRequested==135u);H5730TString a15=T("A15");CHECK(vrcomfort_O(&O,&a15)==1u);
  s26ed_load_render_scale();CHECK(g_s26edScaleActive==135u); /* loaded once */
  memcpy(scaleFile.data,"999\n",4);g_s26edScaleLoaded=0;g_s26edScaleActive=g_s26edScaleRequested=100;s26ed_load_render_scale();CHECK(g_s26edScaleActive==100u);
 }
 /* =========== 6. TEXTURE BUDGET menu toggle =========== */
 {
  somaImage=calloc(0x80cd00,1);
  const u8 sig[29]={0x48,0x89,0x74,0x24,0x20,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x83,0xec,0x60,0x48,0x8b,0x05,0xda,0xe2,0x52,0x00,0x0f,0x29,0x74,0x24,0x50,0x66,0x0f};
  memcpy(somaImage+0x2de9c0,sig,29);u64* budget=(u64*)(somaImage+0x80cca8);*budget=0x40000000ull;
  g_s26ecSettings=0;s26_texture_streaming_step();CHECK(*budget==0x40000000ull&&!g_s26TextureVerified);
  s26ec_set_option(S26EC_SET_TEXTURE,1);s26_texture_streaming_step();CHECK(*budget==0x60000000ull&&g_s26TextureOwned);
  s26_texture_streaming_step();CHECK(*budget==0x60000000ull);
  s26ec_set_option(S26EC_SET_TEXTURE,0);s26_texture_streaming_step();CHECK(*budget==0x40000000ull&&!g_s26TextureOwned);
  s26ec_set_option(S26EC_SET_TEXTURE,1);s26_texture_streaming_step();CHECK(*budget==0x60000000ull);
  xrRunning=0;s26_texture_streaming_step();CHECK(*budget==0x40000000ull);xrRunning=1;s26_texture_streaming_step();CHECK(*budget==0x60000000ull);
  *budget=0x50000000ull;s26ec_set_option(S26EC_SET_TEXTURE,0);s26_texture_streaming_step();CHECK(*budget==0x50000000ull&&!g_s26TextureOwned); /* never clobbers an engine-changed value */
  free(somaImage);somaImage=0;
 }
 /* =========== 7. DEPTH: pure helpers =========== */
 {
  CHECK(s26ed_depth_format(24,8,0x8C17u)==0x88F0u&&s26ed_depth_format(32,8,0x1406u)==0x8CADu&&s26ed_depth_format(32,0,0x1406u)==0x8CACu);
  CHECK(s26ed_depth_format(24,0,0x8C17u)==0x81A6u&&s26ed_depth_format(16,0,0x8C17u)==0x81A5u&&s26ed_depth_format(32,0,0x8C17u)==0x81A7u);
  CHECK(!s26ed_depth_format(24,8,0x1406u)&&!s26ed_depth_format(16,8,0x8C17u)&&!s26ed_depth_format(24,4,0x8C17u)&&!s26ed_depth_format(24,0,0x1405u)&&!s26ed_depth_format(0,0,0x8C17u));
  float p[16],n=0,f=0;perspective(p,0.05f,400.0f);CHECK(s26ed_depth_planes(p,1.0f,&n,&f));CHECK(fabsf(n-0.05f)<0.0005f&&fabsf(f-400.0f)<4.0f);
  CHECK(s26ed_depth_planes(p,1.25f,&n,&f)&&fabsf(n-0.04f)<0.0005f&&fabsf(f-320.0f)<3.2f);
  perspective(p,0.01f,100.0f);CHECK(s26ed_depth_planes(p,1.0f,&n,&f)&&fabsf(n-0.01f)<0.0002f&&fabsf(f-100.0f)<1.0f); /* SOMA's logged eye projection */
  float q[16];memcpy(q,p,64);q[11]=1.0f;CHECK(!s26ed_depth_planes(q,1,&n,&f));memcpy(q,p,64);q[10]=-1.0f;CHECK(!s26ed_depth_planes(q,1,&n,&f)); /* infinite far */
  memcpy(q,p,64);q[14]=0.02f;CHECK(!s26ed_depth_planes(q,1,&n,&f));memcpy(q,p,64);q[10]=NAN;CHECK(!s26ed_depth_planes(q,1,&n,&f));
  memcpy(q,p,64);q[15]=1.0f;CHECK(!s26ed_depth_planes(q,1,&n,&f));CHECK(!s26ed_depth_planes(p,0.0f,&n,&f));
  /* Chain: copies the projection layer, never edits the caller's frame. */
  XrCompositionLayerProjectionView v[2];memset(v,0,sizeof(v));
  for(int e=0;e<2;e++){v[e].type=48;v[e].subImage.swapchain=(Handle)(u64)(0x10+e);v[e].subImage.imageRect.extent.width=1000;v[e].subImage.imageRect.extent.height=1100;}
  XrCompositionLayerProjection pl;memset(&pl,0,sizeof(pl));pl.type=35;pl.viewCount=2;pl.views=v;pl.layerFlags=3;
  XrCompositionLayerQuad quad;memset(&quad,0,sizeof(quad));quad.type=36;
  const void* layers[2]={&pl,&quad};XrFrameEndInfo in;memset(&in,0,sizeof(in));in.type=12;in.layerCount=2;in.layers=layers;in.displayTime=77;
  XrFrameEndInfo out;S26EDDepthFrame fr;Handle sw[2]={(Handle)0x200,(Handle)0x201};float nn[2]={0.05f,0.06f},ff[2]={400,410};
  CHECK(s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));
  CHECK(out.displayTime==77&&out.layerCount==2&&out.layers==fr.layers&&fr.layers[0]==&fr.proj&&fr.layers[1]==&quad&&in.layers==layers&&layers[0]==&pl);
  CHECK(fr.proj.views==fr.views&&fr.proj.layerFlags==3&&pl.views==v&&v[0].next==0&&v[1].next==0);
  for(int e=0;e<2;e++){S26EDDepthInfo* d=(S26EDDepthInfo*)fr.views[e].next;CHECK(d==&fr.depth[e]&&d->type==1000010000&&d->next==0);
   CHECK(d->subImage.swapchain==sw[e]&&d->subImage.imageRect.extent.width==1000&&d->subImage.imageRect.extent.height==1100&&d->subImage.imageArrayIndex==0);
   CHECK(d->minDepth==0.0f&&d->maxDepth==1.0f&&d->nearZ==nn[e]&&d->farZ==ff[e]);CHECK(fr.views[e].subImage.swapchain==v[e].subImage.swapchain);}
  /* Rejections leave the frame alone. */
  Handle none[2]={(Handle)0x200,0};CHECK(!s26ed_depth_chain(&in,&out,&fr,none,1000,1100,nn,ff));
  CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,999,1100,nn,ff));
  v[1].subImage.imageRect.offset.x=1;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));v[1].subImage.imageRect.offset.x=0;
  int chained=7;v[0].next=&chained;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));v[0].next=0;
  v[0].type=36;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));v[0].type=48;
  pl.viewCount=1;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));pl.viewCount=2;
  const void* two[2]={&pl,&pl};in.layers=two;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));
  const void* noProj[1]={&quad};in.layers=noProj;in.layerCount=1;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));
  const void* withNull[2]={&pl,0};in.layers=withNull;in.layerCount=2;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));
  in.layers=layers;in.layerCount=17;CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));in.layerCount=2;
  float badN[2]={0.05f,0};CHECK(!s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,badN,ff));
  CHECK(s26ed_depth_chain(&in,&out,&fr,sw,1000,1100,nn,ff));
 }
 /* =========== 8. DEPTH: live pipeline with mocked GL/XR =========== */
 {
  *(Handle*)(xrobj+0x10)=(Handle)0x1111;session(0x2222);*(i32*)(xrobj+0x40)=1000;*(i32*)(xrobj+0x44)=1100;*(i32*)(xrobj+0x60)=1000;*(i32*)(xrobj+0x64)=1100;
  *(PFN_GIPA*)(xrobj+0x1C8)=xr_gipa;setRenderer(1500,1600,0.05f,400.0f);
  XrCompositionLayerProjectionView v[2];memset(v,0,sizeof(v));
  for(int e=0;e<2;e++){v[e].type=48;v[e].subImage.imageRect.extent.width=1000;v[e].subImage.imageRect.extent.height=1100;}
  XrCompositionLayerProjection pl;memset(&pl,0,sizeof(pl));pl.type=35;pl.viewCount=2;pl.views=v;
  const void* layers[1]={&pl};XrFrameEndInfo in;memset(&in,0,sizeof(in));in.layerCount=1;in.layers=layers;
  /* Option off: no GL queries, no swapchains, frames untouched. */
  g_s26ecSettings=0;eyeRender(0);eyeRender(1);CHECK(attachQueries==0&&creates==0&&acquires==0);CHECK(s26ed_depth_end_frame(&in,1)==&in);
  /* Extension missing: same. */
  g_s26ecSettings=S26EC_SET_DEPTH;g_s26edDepthExtension=0;eyeRender(0);CHECK(attachQueries==0&&creates==0);g_s26edDepthExtension=1;
  /* Normal frame. */
  eyeRender(0);CHECK(creates==2&&lastCi.format==0x88F0&&lastCi.usageFlags==0x02u&&lastCi.width==1000&&lastCi.height==1100&&lastCi.sampleCount==1&&lastCi.arraySize==1&&lastCi.mipCount==1&&lastCi.faceCount==1);
  CHECK(acquires==1&&waits==1&&releases==1&&!heldImage[0]);
  CHECK(geomW==1500&&geomH==1600&&blits==1&&bx[0]==150&&bx[1]==80&&bx[2]==1150&&bx[3]==1180&&bx[4]==0&&bx[5]==0&&bx[6]==1000&&bx[7]==1100);
  CHECK(bmask==0x0100u&&bfilter==0x2600u&&blitReadName==11u&&blitDrawName==500u&&blitPoint==0x821Au&&blitScissor==0&&blitMask==1);
  CHECK(lastReadBuffer==0&&lastDrawBuffer==0);
  CHECK(curRead==7&&curDraw==7&&curRb==3&&scissor==1&&depthMaskV==0); /* engine state restored */
  CHECK(att[40].name==0&&att[41].name==0); /* private FBOs hold no engine/runtime image */
  CHECK(g_s26edDepthReady==1u);
  XrFrameEndInfo* got=(XrFrameEndInfo*)s26ed_depth_end_frame(&in,1);CHECK(got==&in&&g_s26edDepthReady==0u); /* one eye is not enough */
  eyeRender(0);eyeRender(1);CHECK(creates==2&&acquires==3&&blits==3&&blitDrawName==510u);CHECK(g_s26edDepthReady==3u);
  got=(XrFrameEndInfo*)s26ed_depth_end_frame(&in,1);CHECK(got==&g_s26edDepthEnd&&g_s26edDepthReady==0u&&v[0].next==0);
  {const XrCompositionLayerProjection* cp=got->layers[0];for(int e=0;e<2;e++){const S26EDDepthInfo* d=cp->views[e].next;
   CHECK(d&&d->type==1000010000&&d->subImage.swapchain==g_s26edDepthSwap[e]&&fabsf(d->nearZ-0.05f)<0.0005f&&fabsf(d->farZ-400.0f)<4.0f);}}
  s26ed_depth_end_result(got,0);CHECK(!g_s26edDepthSessionFailed);
  CHECK(s26ed_depth_end_frame(&in,1)==&in); /* readiness is consumed per EndFrame */
  /* Menu/quad frames consume readiness without depth. */
  eyeRender(0);eyeRender(1);CHECK(s26ed_depth_end_frame(&in,0)==&in&&g_s26edDepthReady==0u);
  /* World scale converts to metres. */
  upm=1.25f;eyeRender(0);eyeRender(1);got=(XrFrameEndInfo*)s26ed_depth_end_frame(&in,1);
  {const XrCompositionLayerProjection* cp=got->layers[0];const S26EDDepthInfo* d=cp->views[0].next;CHECK(fabsf(d->nearZ-0.04f)<0.0005f&&fabsf(d->farZ-320.0f)<3.2f);}upm=1.0f;
  /* Engine scene in the default framebuffer, a shadow-map-sized target, or an unknown format: skipped, nothing acquired. */
  int a0=acquires;curDraw=0;eyeRender(0);CHECK(acquires==a0&&g_s26edDepthReady==0u);curDraw=7;
  rbW=2048;rbH=2048;eyeRender(0);CHECK(acquires==a0);rbW=1500;rbH=1600;
  engS=4;eyeRender(0);CHECK(acquires==a0);engS=8;
  stName=12;eyeRender(0);CHECK(acquires==a0);stName=11;
  setRenderer(1500,1600,0.05f,400.0f);((float*)(renderer+0xaa4))[10]=-1.0f;eyeRender(0);CHECK(acquires==a0);setRenderer(1500,1600,0.05f,400.0f);
  geomOK=0;eyeRender(0);CHECK(acquires==a0);geomOK=1;
  CHECK(!g_s26edDepthSessionFailed);
  /* GL error during the copy: image still released, eye not ready, session continues. */
  errAtBlit=0x0502;eyeRender(0);CHECK(acquires==a0+1&&releases==acquires&&g_s26edDepthReady==0u&&!g_s26edDepthSessionFailed);errAtBlit=0;
  eyeRender(0);CHECK(g_s26edDepthReady==1u);
  /* Texture depth attachment: needs GL 4.5 size query, level 0, not layered. */
  engType=0x1702;stType=0x1702;texLevelAvailable=0;g_s26edDepthGlReady=0;g_s26edDepthGlTried=0;a0=acquires;eyeRender(0);CHECK(acquires==a0);
  texLevelAvailable=1;g_s26edDepthGlReady=0;g_s26edDepthGlTried=0;eyeRender(0);CHECK(acquires==a0+1&&g_s26edDepthReady==1u&&blitReadName==11u);
  engLayered=1;eyeRender(0);CHECK(acquires==a0+1);engLayered=0;engLevel=1;eyeRender(0);CHECK(acquires==a0+1);engLevel=0;engType=0x8D41;stType=0x8D41;
  /* Format change in the same session recreates both swapchains. */
  int c0=creates,d0=destroys;engD=32;engS=0;engComp=0x1406;stType=0;offer32F=1;eyeRender(0);
  CHECK(creates==c0+2&&destroys==d0+2&&lastCi.format==0x8CAC&&blitPoint==0x8D00u);
  /* Runtime without that format: off for this session only. */
  engD=24;engS=8;engComp=0x8C17;stType=0x8D41;offerD24=0;c0=creates;eyeRender(0);CHECK(g_s26edDepthSessionFailed&&creates==c0);
  int q0=attachQueries;a0=acquires;eyeRender(0);eyeRender(1);CHECK(attachQueries==q0&&acquires==a0&&s26ed_depth_end_frame(&in,1)==&in);
  /* A new session tries again (old swapchains ended with the old session). */
  offerD24=1;session(0x3333);d0=destroys;eyeRender(0);eyeRender(1);CHECK(!g_s26edDepthSessionFailed&&creates==c0+2&&destroys==d0&&g_s26edDepthReady==3u);
  /* Runtime rejects a frame carrying depth: color-only for the rest of the session. */
  got=(XrFrameEndInfo*)s26ed_depth_end_frame(&in,1);CHECK(got==&g_s26edDepthEnd);s26ed_depth_end_result(got,-1);CHECK(g_s26edDepthSessionFailed);
  eyeRender(0);eyeRender(1);CHECK(s26ed_depth_end_frame(&in,1)==&in);
  s26ed_depth_end_result(&in,-1);session(0x4444);CHECK(s26ed_depth_active());
  /* Acquire failure and wait failure disable the session; an acquired image is always released. */
  acquireFail=1;eyeRender(0);CHECK(g_s26edDepthSessionFailed);acquireFail=0;session(0x5555);
  waitResult=1;a0=acquires;eyeRender(0);CHECK(g_s26edDepthSessionFailed&&acquires==a0+1&&releases==acquires);waitResult=0;session(0x6666);
  /* Eye swapchain sizes differ: off for this session. */
  *(i32*)(xrobj+0x60)=1002;eyeRender(0);CHECK(g_s26edDepthSessionFailed);*(i32*)(xrobj+0x60)=1000;session(0x7777);
  createFail=1;eyeRender(0);CHECK(g_s26edDepthSessionFailed);createFail=0;
  /* Observation must come from the same eye render: a stale one is never copied. */
  session(0x8888);eyeRender(0);int b0=blits;s26ed_depth_capture(0);CHECK(blits==b0);
 }
 printf("PASS: %d S26ED checks (head-tap crown zone over %d head poses and tap gating; ladder hand climb; VRLADDER; render scale parse/persist/VRCOMFORT O; texture budget toggle; depth format/planes/chain and mocked GL/XR depth pipeline)\n",checks,12*5*3);
 return 0;
}
'''
c=B/'vr_presence_test.c'
c.write_text(header+types+defines+'\n'+swap+pfn+tstring+gesture+mocks+production+wrappers+main)
exe=B/'vr_presence_test.exe'
subprocess.run([sys.argv[1],'cc','-std=gnu11','-O1','-Wall','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-but-set-variable',str(c),'-o',str(exe),'-lm'],check=True)
subprocess.run([str(exe)],check=True)
