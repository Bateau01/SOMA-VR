
from pathlib import Path
import subprocess,sys,re
R=Path(__file__).resolve().parents[1];A=R/'audit/hb';A.mkdir(parents=True,exist_ok=True)
src=(R/'source/timing_gx.inc').read_text().split('static void s26gx_install')[0]
head=r"""
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef uint64_t u64;typedef uint32_t u32;typedef int32_t i32;typedef uint8_t u8;
#define H5755BH_GAMEPLAY_VR 1
static int calls,on,running,g_h5755bhPresentationState;
static int p2_xr_on(void){return on;}static int p2_xr_running(void){return running;}
"""
body=r"""
static int wanted;static void* seen;
static u64 __attribute__((ms_abi)) wantfn(void*p,i32 m){calls++;wanted=m;seen=p;return 0x12340001;}
int main(void){o_s26gxWant=wantfn;int count=0;int rates[]={60,120,90,144};
 for(on=0;on<2;on++)for(running=0;running<2;running++)for(g_h5755bhPresentationState=0;g_h5755bhPresentationState<4;g_h5755bhPresentationState++)
 for(int r=0;r<4;r++)for(int m=-1;m<=4;m++)for(int nil=0;nil<2;nil++){
  union {u64 a;u8 b[80];} obj,expected;memset(&obj,0,sizeof(obj));*(u32*)(obj.b+0x30)=rates[r];expected=obj;
  calls=0;void*p=nil?0:obj.b;
  int active=p&&m>1&&rates[r]==120&&on&&running&&g_h5755bhPresentationState==1;
  u64 got=s26gx_want(p,m);assert(got==0x12340001&&calls==1&&wanted==(active?1:m)&&seen==p);
  assert(!memcmp(&obj,&expected,sizeof(obj)));count++;
 }
 printf("PASS %d timing cases; 60Hz/VR guards, original return, zero timer writes\n",count);
}
"""
p=A/'timer.c';p.write_text(head+src+body)
subprocess.run([sys.argv[1],'cc','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
subprocess.run([str(p.with_suffix('.exe'))],check=True)
for name in ['capture_ha.inc','ghost_gz.inc','hand_timing_gs.inc','stutter_ej.inc']:
 assert not (R/'source'/name).exists()
for file in ['build/hpl3vr.dll','build/store/hpl3vr-store.dll']:
 b=(R/file).read_bytes()
 for token in [b'LOSSLESS HAND CAPTURE',b'hpl3vr_stutter.bin',b'STUTTER RECORDER',b'hpl3vr_capture_hands.flag',b'engine getter returned']:
  assert token not in b,(file,token)
m=(R/'runtime/script/modules/MenuHandler.hps').read_text()
assert 'STUTTER RECORDING' not in m and '"STUTTER"' not in m
assert 'if(mlVRComfortCategory<0) return 5;' in m
assert re.search(r'void HPL3VR_BackSettings\(\)\s*\{\s*if',m)
# Structural balance excluding comments and strings; engine gameplay assets identical except menu removal.
strip=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"','',m,flags=re.S)
for left,right in [('{','}'),('(',')'),('[',']')]:
 n=0
 for c in strip:
  n+=(c==left)-(c==right);assert n>=0
 assert n==0
old=R.parents[1]/'SOMA_VR_S26HA_LOSSLESS_EYE_CAPTURE/repo'
allowed={'script/modules/MenuHandler.hps','SOMA-VR-Settings.ps1','Launch-SOMA-VR.ps1','Stop-SOMA-VR.cmd'}
for p in (R/'runtime').rglob('*'):
 if p.is_file() and p.relative_to(R/'runtime').as_posix() not in allowed:
  assert p.read_bytes()==(old/'runtime'/p.relative_to(R/'runtime')).read_bytes(),p
print('PASS recorder/capture absent from both DLLs; menu structure; all other runtime assets unchanged before packaging')
