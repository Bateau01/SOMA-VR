from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1]; B=R/"build"; B.mkdir(exist_ok=True)
s=(R/"source/s26n.c").read_text(); a=s.index('    if(h5748t_sso_eq(objectName,"VRGUIDE",7u)){'); e=s.index('        if(h5748t_sso_eq(functionName,"HELD"',a)
block=s[a:e]+"return 0; } return 0; }"
head=r"""
#include <math.h>
#include <string.h>
#include <assert.h>
typedef int i32; typedef unsigned u32;
#define ext_Sqrtf sqrtf
#define h576c_ci_streq(a,b) (!strcmp(a,b))
typedef struct {char name[96];i32 hand,kind;float rotation[9],fraction[3],joint[5][4];} S26EJGrip;
static int g_h576mScriptRuntimePublished=1,g_h5755bhPresentationState=1,g_h576bfMapTransitionActive,g_s26CutsceneHandsHidden;
#define H5755BH_GAMEPLAY_VR 1
static int g_s26xPhoneActive=1,g_s26xPhonePending=1,g_h14GripBody[2],valid=1,paused=0;
static float basisIn[9]={1,0,0,0,1,0,0,0,1},centerIn[3]={4,5,6},returned[3];
static int p2_xr_on(void){return 1;} static int p2_xr_running(void){return 1;}
static int h5754h_pause_active(void){return paused;} static int visual_pose_valid(int h){return valid;}
static float h5755ea_world_units_per_meter(void){return 1;}
static int h5748t_sso_eq(const char*a,const char*b,unsigned n){return strlen(a)==n&&!strcmp(a,b);}
static int h14_hand_pose_raw(int h,float*p,float*m){return valid;}
static int h15_grip_center_world(int h,float*m,float*c){memcpy(c,centerIn,12);return 1;}
static void quat_to_game_basis(int h,float*b){memcpy(b,basisIn,36);}
static int s26s_set_vector(const float*v){memcpy(returned,v,12);return 1;}
"""
tail=r"""
int main(void){
 const S26EJGrip* g=s26el_default_grip(1,2,"Phone");assert(g);
 for(int turn=0;turn<40;turn++){
  float a=turn*.157f,c=cosf(a),s=sinf(a);float v[9]={c,0,-s,0,1,0,s,0,c};memcpy(basisIn,v,36);
  assert(query("VRGUIDE","PHONE"));for(int i=0;i<3;i++)assert(returned[i]==centerIn[i]);
  /* Synthetic head turns cannot enter this query: only controller basis does. */
  for(int row=0;row<3;row++){
   const char* token=row==0?"PHONE_ROW0":row==1?"PHONE_ROW1":"PHONE_ROW2";
   assert(query("VRGUIDE",token));
   for(int col=0;col<3;col++){float expected=0;for(int k=0;k<3;k++)expected+=v[k*3+row]*g->rotation[col*3+k];assert(fabsf(returned[col]-expected)<.00001f);}
   assert(!query("VRGUIDE",token));
  }
 }
 assert(query("VRGUIDE","PHONE"));paused=1;assert(!query("VRGUIDE","PHONE_ROW0"));paused=0;assert(!query("VRGUIDE","PHONE_ROW0"));
 assert(query("VRGUIDE","PHONE"));valid=0;assert(!query("VRGUIDE","PHONE_ROW0"));valid=1;assert(!query("VRGUIDE","PHONE_ROW0"));
 assert(query("VRGUIDE","PHONE"));g_h14GripBody[1]=1;assert(!query("VRGUIDE","PHONE"));g_h14GripBody[1]=0;assert(!query("VRGUIDE","PHONE_ROW0"));
 assert(query("VRGUIDE","PHONE"));g_h576bfMapTransitionActive=1;assert(!query("VRGUIDE","PHONE_ROW0"));g_h576bfMapTransitionActive=0;assert(!query("VRGUIDE","PHONE_ROW0"));
 assert(query("VRGUIDE","PHONE"));g_s26xPhonePending=0;assert(!query("VRGUIDE","PHONE_ROW0"));g_s26xPhonePending=1;
 assert(query("VRGUIDE","PHONE"));assert(query("VRGUIDE","PHONE_ROW0"));
 return 0;
}
"""
p=B/"phone_guide_test.c";p.write_text(head+(R/"source/authored_grips_el.inc").read_text()+(R/"source/holster_grip_ef.inc").read_text()+(R/"source/phone_guide_frame.inc").read_text()+"\nstatic int query(const char*objectName,const char*functionName){\n"+block+tail)
exe=B/"phone_guide_test.exe";subprocess.run([sys.argv[1],"cc","-O2",str(p),"-o",str(exe)],check=True);subprocess.run([str(exe)],check=True)
script=(R/"runtime/script/helpers/helper_vr_phone_q.hps").read_text();section=script[script.index('if(pocket &&'):script.index("}else if(!pocket)")]
assert "GetYaw" not in section and "GetCamera" not in section
assert all(x in section for x in ["PHONE_ROW0","PHONE_ROW1","PHONE_ROW2","if(valid) mVRPhoneGuide.Show"])
assert "s26ef_prepare_holster" not in block and "s26ej_grip_override" not in block
result={"passed":True,"scope":"Extracted production bridge with synthetic tracking; real authored rotation and matrix helper; not native rendered or headset validation","rotations":40,"cases":["row conversion","single consumption","pause","tracking loss","held phone","map transition","pending call end","recovery","script no camera yaw","no retrieval mutations"]}
(B/"phone_guide_results.json").write_text(json.dumps(result,indent=2));print(json.dumps(result))
