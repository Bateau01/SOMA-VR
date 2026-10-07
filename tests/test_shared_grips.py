from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
head=r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
typedef int i32;typedef unsigned int u32;
typedef struct {const char* text;} H5730TString;
static float g_s26ejHolsterJoint[2][5][4],g_s26efHolsterCurl[2][5];static int g_s26ejHolsterJointValid[2];static char g_s26elGripScope[96];
static int h576c_ci_streq(const char*a,const char*b){return _stricmp(a,b)==0;}
static int h5748t_sso_eq(const H5730TString*a,const char*b,u32 n){return !strcmp(a->text,b);}
static int h5748n_copy_tstring(void*p,char*out,u32 n){snprintf(out,n,"%s",((H5730TString*)p)->text);return 1;}
static void h5748n_copyz(char*out,u32 n,const char*s){snprintf(out,n,"%s",s);}
#include "item_grips_ej.inc"
int main(){int checks=0;float r[9],f[3];
 for(int i=0;i<52;i++){const S26EJGrip*e=&g_s26elDefaultGrips[i];
  if(!s26ej_grip_override(e->hand,e->kind,e->name,r,f))return 1;
  if(memcmp(r,e->rotation,sizeof(r))||memcmp(f,e->fraction,sizeof(f)))return 2;
  if(memcmp(g_s26ejHolsterJoint[e->hand],e->joint,sizeof(e->joint))||!g_s26ejHolsterJointValid[e->hand])return 3;
  H5730TString n={e->name};if(!s26el_grip_model_command(&n)||strcmp(g_s26elGripScope,e->name))return 4;
  checks++;
 }
 if(s26ej_grip_override(0,0,"missing",r,f)||g_s26ejHolsterJointValid[0])return 5;
 if(s26ej_grip_override(-1,0,"ARK",r,f)||s26ej_grip_override(2,0,"ARK",r,f))return 6;
 H5730TString end={"END"};if(!s26el_grip_model_command(&end)||g_s26elGripScope[0])return 7;
 printf("PASS %d shared poses, exact transforms and joint curls\n",checks);return 0;
}
'''
p=B/'shared_grips_test.c';p.write_text(head);exe=B/'shared_grips_test.exe'
subprocess.run([sys.argv[1],'cc','-O2','-I',str(R/'source'),str(p),'-o',str(exe)],check=True)
# A conflicting legacy file is deliberately present beside the test executable.
(B/'hpl3vr_item_grips.dat').write_bytes(b'legacy override must not be opened')
subprocess.run([str(exe)],cwd=B,check=True)
source=(R/'source/item_grips_ej.inc').read_text();main=(R/'source/s26n.c').read_text(encoding='utf-8');menu=(R/'runtime/script/modules/MenuHandler.hps').read_text()
assert all(x not in source for x in ['fopen','fread','grips_load','grip_capture','grip_save','item_grips.dat'])
assert all(x not in main for x in ['s26ej_trace','s26ej_grip_step','"GRIPPOSE"','"STUTTER"','stutter_ej.inc'])
assert all(x not in menu for x in ['TEST TOOLS','GRIPPOSE','START STUTTER','SAVE LEFT ITEM GRIP'])
assert 'if(mlVRComfortCategory<0) return 5;' in menu
result={'passed':True,'shared_poses':52,'legacy_override_file_ignored':True,'capture_and_recorder_paths_removed':True,'menu_back_row_corrected':True}
(B/'shared_grips_results.json').write_text(json.dumps(result,indent=2));print(result)
