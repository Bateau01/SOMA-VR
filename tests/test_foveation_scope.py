"""Execute the production GBuffer VRS wrapper against an actual GL context."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build'
s=(R/'source/foveation_ef.inc').read_text();s=s[:s.index('static void s26ef_install_foveation')]
for name in ['foveation_tuning_ei.inc','foveation_timing_ei.inc']:s=s.replace('#include "'+name+'"',(R/'source'/name).read_text(encoding='utf-8-sig'))
a=s.index('static i32 s26ei_read_foveation_gaze(');b=s.index('/* The light fix',a)
s=s[:a]+'static float testGaze[3];static int testValid=1;static i32 s26ef_foveation_gaze(float* g){for(int i=0;i<3;++i)g[i]=testGaze[i];return testValid;}\n'+s[b:]
light=(R/'source/light_projection_do.inc').read_text();light=light[:light.index('typedef void')]
head=r'''
#include <windows.h>
#include <GL/gl.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#undef far
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef int i32;typedef long long i64;
#define ext_Sqrtf sqrtf
#define ext_Sinf sinf
#define ext_Cosf cosf
#define ext_GetModuleHandleA GetModuleHandleA
#define ext_GetProcAddress GetProcAddress
#define ext_glGetIntegerv glGetIntegerv
#define ext_glBindTexture glBindTexture
#define ext_glEnable glEnable
#define ext_glDisable glDisable
#define ext_glIsEnabled glIsEnabled
#define ext_Log(...) ((void)0)
typedef void* (__attribute__((ms_abi)) *PFN_H5750A_WglGetProcAddress)(const char*);
static void* s26_gl_proc(void* m,PFN_H5750A_WglGetProcAddress wg,const char* n){void*p=wg(n);if((u64)p<=3||(u64)p==~(u64)0)p=(void*)GetProcAddress(m,n);return p;}
static int h20_mem_readable(const void*p,u32 n){return p&&n;}
static void*g_s26doLightRenderer,*g_s26doLightFrustum;
'''
tail=r'''
__declspec(dllexport) void configure(const char* text,int timing){s26ei_dfr_config((const u8*)text,6);g_s26eiDFRTiming=timing;}
__declspec(dllexport) unsigned timer_samples(void){unsigned n=0;for(int i=0;i<3;i++)n+=g_s26eiGPUStats[i].count;return n;}
__declspec(dllexport) unsigned owned_texture(void){return g_s26efRateTexture;}
__declspec(dllexport) unsigned counter(int i){return g_s26egDFRStats[i];}
static void (__attribute__((ms_abi)) *realUpload)(u32,i32,i32,i32,i32,i32,u32,u32,const void*);
static void __attribute__((ms_abi)) failUpload(u32 a,i32 b,i32 c,i32 d,i32 e,i32 f,u32 g,u32 h,const void*i){
 p_s26efUpload=realUpload;realUpload(a,b,c,d,e,f,g,h,i);glEnable(0xffffffffu);
}
__declspec(dllexport) void fail_next_upload(void){realUpload=p_s26efUpload;p_s26efUpload=failUpload;}
__declspec(dllexport) void run_scope(void* callback,float* projection,float* gaze,int width,int height,int enabled,int valid){
 unsigned char renderer[0xc20]={0};g_s26doLightRenderer=renderer;g_s26doLightFrustum=renderer;
 *(void**)(renderer+0x20)=renderer;*(int*)(renderer+0x40)=width;*(int*)(renderer+0x44)=height;
 memcpy(renderer+0xaa4,projection,64);*(float*)(renderer+0xbe4)=1;
 float*old=(float*)(renderer+0xbf4);old[0]=2.0f/width;old[1]=2.0f/height;old[2]=projection[8]-1;old[3]=projection[9]-1;
 for(int i=0;i<3;++i)testGaze[i]=gaze[i];testValid=valid;g_s26efFoveation=enabled;
 o_s26efGbuffer=(S26EFPass)callback;s26ef_gbuffer(renderer);
}
'''
p=B/'foveation_scope_test.c';p.write_text(head+light+s+tail);dll=B/'foveation_scope_test.dll'
subprocess.run([sys.argv[1],'cc','-shared','-O2',str(p),'-lopengl32','-o',str(dll)],check=True)
# Reuse real-driver setup; no fixture code mutates the SOMA process.
setup=(R/'tests/probe_foveation_pipeline.py').read_text();exec(setup[:setup.index('results={}')].replace('64,64','256,256'))
lib=c.CDLL(str(dll));run=lib.run_scope;run.argtypes=[P,c.POINTER(F),c.POINTER(F),I,I,I,I]
@c.WINFUNCTYPE(None,P)
def draw(_):
 begin(4)
 for x,y in [(-1,-1),(3,-1),(-1,3)]:vertex(x,y)
 end()
projection=(F*16)(1,0,0,0,0,1,0,0,0,0,-1,-1,0,0,-.2,0);gaze=(F*3)(0,0,-1)
get=fn('glGetIntegerv',None,U,c.POINTER(I));getpal=fn('glGetShadingRateImagePaletteNV',None,U,U,c.POINTER(U));isenabled=fn('glIsEnabled',c.c_ubyte,U)
# Deliberately unusual state; wrapper must restore it exactly.
palette(0,0,3,(U*3)(0x9566,0x9567,0x9565));ratebind(rt);disable(0x9563)
fn('glPixelStorei',None,U,I)(0xcf5,8)
fn('glPixelStorei',None,U,I)(0xcf2,7)
fn('glPixelStorei',None,U,I)(0xcf3,3)
fn('glPixelStorei',None,U,I)(0xcf4,2)
pbo=U();bgen(1,c.byref(pbo));bbind(0x88ec,pbo);bdata(0x88ec,128,None,0x88e8)
keys=[0x8069,0x88ef,0xcf5,0xcf2,0xcf3,0xcf4,0x955b,0x8ca6]
def state():
 out=[]
 for key in keys:
  value=I();get(key,c.byref(value));out.append(value.value)
 for index in range(3):
  value=U();getpal(0,index,c.byref(value));out.append(value.value)
 out.append(isenabled(0x9563));return out
lib.configure.argtypes=[c.c_char_p,I]
results={}
for name,on,valid in [('off',0,1),('on',1,1),('invalid_gaze',1,0),('off_again',0,1),('asymmetric_eye',1,1)]:
 if name=='asymmetric_eye':projection[8]=.18;projection[9]=-.13
 zero=U();bbind(0x90d2,buf);bdata(0x90d2,4,c.byref(zero),0x88e8)
 prior=state();run(draw,projection,gaze,256,256,on,valid);after=state();assert prior==after,(name,prior,after)
 barrier(0x2000|0x200);finish();n=U();getdata(0x90d2,0,4,c.byref(n));results[name]=n.value;assert error()==0,name
assert results['off']==results['invalid_gaze']==results['off_again']==65536,results
# The wide full-quality region still permits a measurable peripheral reduction.
assert 0<results['on']<65536 and 0<results['asymmetric_eye']<65536,results
# Three presets must reduce work in order, and restore all three palette entries.
for label,config in [('quality',b'254501'),('balanced',b'204011'),('performance',b'153511')]:
 lib.configure(config,0);zero=U();bbind(0x90d2,buf);bdata(0x90d2,4,c.byref(zero),0x88e8)
 prior=state();run(draw,projection,gaze,256,256,1,1);assert state()==prior
 barrier(0x2000|0x200);finish();n=U();getdata(0x90d2,0,4,c.byref(n));results[label]=n.value
assert results['performance']<results['balanced']<results['quality']<results['off'],results
lib.configure(b'254501',0)
# A foreign shading-rate owner must remain untouched, even when DFR is enabled.
enable(0x9563);prior=state();run(draw,projection,gaze,256,256,1,1);assert state()==prior;disable(0x9563)
assert error()==0
# Prior engine errors must not be attributed to DFR or delete its healthy texture.
lib.owned_texture.restype=U
lib.counter.argtypes=[I];lib.counter.restype=U
old_texture=lib.owned_texture();old_applied=lib.counter(1)
enable(0xffffffff);prior=state();run(draw,projection,gaze,256,256,1,1)
assert state()==prior and lib.owned_texture()==old_texture and error()==0
assert lib.counter(8)==1 and lib.counter(7)==0 and lib.counter(1)==old_applied+1
# A failure inside the DFR setup must still fail closed and recover next time.
lib.fail_next_upload();old_applied=lib.counter(1)
run(draw,projection,gaze,256,256,1,1)
assert state()==prior and lib.owned_texture()==0 and error()==0
assert lib.counter(7)==1 and lib.counter(1)==old_applied
run(draw,projection,gaze,256,256,1,1)
assert state()==prior and lib.owned_texture()!=0 and error()==0
assert lib.counter(1)==old_applied+1
# A resize forces texture recreation, then the original extent must recover.
viewport(0,0,128,128);prior=state();run(draw,projection,gaze,128,128,1,1);assert state()==prior;assert error()==0
viewport(0,0,256,256);prior=state();run(draw,projection,gaze,256,256,1,1);assert state()==prior;assert error()==0
# Multisampled FBOs must remain valid; previous MSAA menu/stereo fixes stay
# independent of this opaque-pass scope.
rb=U();fn('glGenRenderbuffers',None,I,c.POINTER(U))(1,c.byref(rb))
fn('glBindRenderbuffer',None,U,U)(0x8d41,rb)
fn('glRenderbufferStorageMultisample',None,U,I,U,I,I)(0x8d41,4,0x8058,256,256)
ms=U();fgen(1,c.byref(ms));fbind(0x8d40,ms)
fn('glFramebufferRenderbuffer',None,U,U,U,U)(0x8d40,0x8ce0,0x8d41,rb)
assert status(0x8d40)==0x8cd5 and error()==0
for config in [b'254501',b'204011',b'153511']:
 lib.configure(config,0)
 for on in [0,1,0]:
  prior=state();run(draw,projection,gaze,256,256,on,1);assert prior==state();assert error()==0
fbind(0x8d40,fbo)
# Timestamp collection must coexist with a query-buffer binding and both DFR states.
qbuffer=U();bgen(1,c.byref(qbuffer));bbind(0x9192,qbuffer);bdata(0x9192,256,None,0x88e8)
keys.append(0x9193)
for on in [0,1]:
 lib.configure(b'254501',1)
 for i in range(160):
  prior=state();run(draw,projection,gaze,256,256,on,1);assert state()==prior
  if i%31==0:finish() # Harness only: production must never wait.
assert lib.timer_samples()>0 and error()==0
lib.configure(b'254501',0)
(B/'foveation_scope_results.json').write_text(json.dumps({'passed':True,'counts':results,'restored_state':keys,'prior_error_separated':True,'injected_setup_error_recovered':True,'msaa_state_restored':True,'timestamp_samples_collected':lib.timer_samples(),'query_buffer_restored':True},indent=2));print(json.dumps(results));s.SDL_Quit()


