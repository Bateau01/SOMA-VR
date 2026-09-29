"""Exercise extracted production bob bridge with mock native engine boundaries."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text()
a=s.index('static float g_s26chBobLocal');b=s.index('static void s26ch_bob_install',a)
header=r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
using i32=int;using u32=unsigned;using u8=unsigned char;
alignas(16) u8 player[0x180],character[0x200],camera[0x30];
int g_h576mScriptRuntimePublished=1,xr=1,originalCalls=0,checks=0;
int p2_xr_on(){return xr;}void* h5755ax_current_player(){return player;}
int h20_mem_readable(const void* p,unsigned){return p!=nullptr;}
int h5748n_copy_tstring(void* p,char* out,unsigned size){if(!p||strlen((char*)p)>=size)return 0;strcpy(out,(char*)p);return 1;}
int h11_parse_float(const char* s,float* out){char* end;*out=strtof(s,&end);return end!=s&&*end==0;}
int h9_good(float x,float bound){return std::isfinite(x)&&fabsf(x)<=bound;}
void __attribute__((ms_abi)) original(void*,const float*){originalCalls++;}
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %d\n",__LINE__);exit(1);}}while(0)
"""
main=r"""
int main(){
 *(void**)(player+0x170)=character;*(void**)(character+0x1b0)=camera;character[0x1e8]=1;
 o_s26chCameraOffset=original;
 const float bob[3]={.03f,-.06f,.01f},offset[3]={0,1.5f,0};
 for(int mode=0;mode<4;mode++)for(int yaw=0;yaw<8;yaw++){
  s26ch_bob_reset();float a=yaw*3.14159265f/4,c=cosf(a),sn=sinf(a);
  float right[3]={c,0,-sn},forward[3]={sn,0,c};
  memcpy(character+0x18c,right,12);memcpy(character+0x180,forward,12);
  bool head=mode&1,hands=mode&2;float factor=(head?1.f:0.f)-(hands?1.f:0.f);
  char packet[100];snprintf(packet,sizeof(packet),"%.6f|%.6f|%.6f",factor*bob[0],factor*bob[1],factor*bob[2]);
  CHECK(s26ch_bob_packet(packet));s26ch_camera_offset(character,offset);CHECK(g_s26chBobCamera==camera);
  float world[3];s26ch_bob_to_world(bob,right,forward,world);
  float pos[3]={10,20,30};for(int i=0;i<3;i++)if(!head)pos[i]+=world[i];
  s26ch_bob_apply(camera,pos);
  for(int i=0;i<3;i++)CHECK(fabsf(pos[i]-((i+1)*10.f+(hands?0.f:world[i])))<.00001f);
  for(int gate=0;gate<3;gate++){
   float p[3]={1,2,3};g_h576mScriptRuntimePublished=gate==0?0:1;xr=gate==1?0:1;
   s26ch_bob_apply(gate==2?(void*)1:camera,p);CHECK(p[0]==1&&p[1]==2&&p[2]==3);
  }
  xr=g_h576mScriptRuntimePublished=1;
 }
 CHECK(originalCalls==32);
 const char* bad[]={"", "1|2", "0|0|0|0", "nan|0|0", "0|inf|0", "2|0|0"};
 for(auto text:bad)CHECK(!s26ch_bob_packet(text));
 s26ch_bob_reset();CHECK(!g_s26chBobCamera&&!g_s26chBobCharacter);
 float p[3]={1,2,3};s26ch_bob_apply(camera,p);CHECK(p[0]==1&&p[1]==2&&p[2]==3);
 printf("PASS %d bob transform, toggle, lifecycle and gate checks\n",checks);
}
"""
B=R/'build';B.mkdir(exist_ok=True);(R/'audit').mkdir(exist_ok=True)
p=B/'bob.cpp';exe=B/'bob.exe';p.write_text(header+s[a:b]+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
v=subprocess.run([str(exe)],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/bob_tests.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production native bridge with mock character/camera, XR and hook boundaries.'},indent=2));raise SystemExit(v.returncode)
