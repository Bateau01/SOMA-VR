"""Production roomscale bridge with synthetic tracking and accepted collision motion."""
from pathlib import Path
import sys,subprocess,json
R=Path(__file__).resolve().parents[1]
c=r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
using i32=int;using u32=unsigned;struct H5730TString{const char*s;};
unsigned g_frameCounter=1,g_s26nHeadValidFrame=1,g_h5735RecenterRequests;
int g_h5755bhPresentationState=1,g_h576bfMapTransitionActive,g_s26CutsceneHandsHidden,g_s26nHeadHeightFresh=1;
#define H5755BH_GAMEPLAY_VR 1
float origin[3],head[3],published[3],scale=1,yaw;
int s26s_vr_active(){return 1;}int p2_xr_origin_set(){return 1;}int p2_head_mode(){return 0;}int h5754h_pause_active(){return 0;}
float*p2_xr_origin(){return origin;}float*p2_eye_mid(){return head;}
int h5748t_sso_eq(const H5730TString*s,const char*t,unsigned){return !strcmp(s->s,t);}
float h10_len3(float x,float y,float z){return sqrtf(x*x+y*y+z*z);}
float h10_dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
float h9_abs(float x){return fabsf(x);}int h9_good(float x,float n){return std::isfinite(x)&&fabsf(x)<n;}
float h5755ea_world_units_per_meter(){return scale;}
void tracking_delta_to_game(float x,float y,float z,float*a,float*b,float*c){*a=scale*(cosf(yaw)*x+sinf(yaw)*z);*b=scale*y;*c=scale*(-sinf(yaw)*x+cosf(yaw)*z);}
int s26s_set_vector(const float*v){memcpy(published,v,12);return 1;}
int h5748n_copy_tstring(void*p,char*out,unsigned n){snprintf(out,n,"%s",((H5730TString*)p)->s);return 1;}
int h11_parse_float(char*s,float*out){char*end;*out=strtof(s,&end);return end!=s&&!*end;}
int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);exit(1);}}while(0)
'''+(R/'source/roomscale_hr.inc').read_text()+r'''
int token(const char*fn,const char*arg=""){H5730TString f{fn},a{arg};return s26hr_room_token(&a,&f);}
void frame(){g_frameCounter++;g_s26nHeadValidFrame=g_frameCounter;}
int main(){
 for(float metric:{.5f,1.f,2.f})for(float angle:{0.f,.7f,2.f})for(float fraction:{0.f,.5f,1.f}){
  scale=metric;yaw=angle;memset(origin,0,sizeof(origin));head[0]=.3f;head[1]=1.7f;head[2]=.1f;frame();
  C(token("QUERY"));C(!token("QUERY"));float old[3];tracking_delta_to_game(head[0],0,head[2],old,old+1,old+2);
  char ack[100];snprintf(ack,sizeof(ack),"%.9g,0,%.9g",published[0]*fraction,published[2]*fraction);
  C(token("ACK",ack));C(!token("ACK",ack));float now[3];tracking_delta_to_game(head[0]-origin[0],0,head[2]-origin[2],now,now+1,now+2);
  C(fabsf(now[0]+published[0]*fraction-old[0])<.00001f);C(fabsf(now[2]+published[2]*fraction-old[2])<.00001f);C(origin[1]==0);
 }
 frame();head[0]=origin[0]+.3f;head[2]=origin[2];C(token("QUERY"));g_h5735RecenterRequests++;C(!token("ACK",".01,0,0"));
 frame();C(token("QUERY"));C(!token("ACK","nan,0,0"));
 frame();C(token("QUERY"));C(!token("ACK","0,1,0"));
 frame();C(token("QUERY"));g_h576bfMapTransitionActive=1;C(!token("ACK",".01,0,0"));g_h576bfMapTransitionActive=0;
 frame();head[0]=origin[0]+.05f;head[2]=origin[2];C(!token("QUERY"));
 printf("PASS %d tracking-origin assertions\n",checks);
}
'''
c=c.replace('#include <cmath>','#include <cmath>\n#include <initializer_list>')
p=R/'build/roomscale_bridge_hr.cpp';p.write_text(c)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True)
(R/'docs/v109-evidence/roomscale_bridge_hr.json').write_text(json.dumps({'scope':__doc__,'exit':r.returncode,'output':r.stdout+r.stderr},indent=2));print(r.stdout+r.stderr);raise SystemExit(r.returncode)
