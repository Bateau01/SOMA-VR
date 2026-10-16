from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8');B=R/'build';B.mkdir(exist_ok=True)
a=s.index('static i32 h576av_theta_logical_name(');b=s.index('static i32 h576bo_parse_surface_csv',a);fn=s[a:b]
head=r'''
#include <stdio.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;
typedef struct {const char* text;unsigned size;} H5730TString;
static int g_h576avThetaPendingHand=-1,g_h576avActiveInteractHand,g_h30NativeMouseDown,g_h30NativeUseHand;
static char g_h576avThetaPendingLogical[96];static u32 g_h576avThetaPendingStartStep,g_h576avThetaPendingLastStep,g_h14PhysicsSteps=100,g_h576avThetaCancels,g_h576avThetaTokenRejects,g_h576avThetaArms;
static const void *g_s26gkThetaSourceBody,*g_h14GripBody[2],*g_h576avActiveInteractBody,*g_h31NativeUseBody;
static int g_lastSqueezeActive[2]={1,1};static float g_lastSqueeze[2]={1,1};
static unsigned char wrappers[2][1024];static void* user(const void*b){return b==(void*)1?wrappers[0]:b==(void*)2?wrappers[1]:0;}
static void*(*p_h14GetUserData)(const void*)=user;
static int h20_mem_readable(const void*p,unsigned n){return p!=0;}
static int h5720_streq(const char*a,const char*b){return !strcmp(a,b);}
static int h576c_ci_streq(const char*a,const char*b){return !strcmp(a,b);}
static int h5748t_sso_eq(const H5730TString*a,const char*b,unsigned n){return a&&a->size==n&&!strncmp(a->text,b,n);}
static int h5748n_copy_tstring(void*p,char*out,unsigned n){H5730TString*t=p;if(t->size>=n)return 0;strcpy(out,t->text);return 1;}
static void h5748n_copyz(char*out,unsigned n,const char*in){snprintf(out,n,"%s",in);}
static void ext_Log(const char*f,...){ }
static int checks;
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 H5730TString o={"VROMNITHETA",11},c={"door_panel_chip_formatted",25},f={"R",1};c.size=strlen(c.text);
 g_h576avActiveInteractBody=(void*)1;g_h14GripBody[0]=(void*)1;
 C(h576av_decode_theta_token(&o,&c,&f)==1);C(g_h576avThetaPendingHand==0&&g_s26gkThetaSourceBody==(void*)1);
 h576av_theta_clear_pending("test");C(!g_s26gkThetaSourceBody&&g_h576avThetaPendingHand==-1);
 g_h14GripBody[0]=(void*)2;C(h576av_decode_theta_token(&o,&c,&f)==1);C(!g_s26gkThetaSourceBody);C(g_h14GripBody[0]==(void*)2);
 g_h576avActiveInteractHand=-1;h576av_theta_clear_pending("test");C(h576av_decode_theta_token(&o,&c,&f)==1);C(g_h576avThetaPendingHand==-1);
 g_h576avActiveInteractHand=0;g_lastSqueeze[0]=0;C(h576av_decode_theta_token(&o,&c,&f)==1);C(g_h576avThetaPendingHand==-1);g_lastSqueeze[0]=1;
 c.text="not_a_tool";c.size=strlen(c.text);C(h576av_decode_theta_token(&o,&c,&f)==-1);
 c.text="chip_unformatted";c.size=strlen(c.text);f.text="B42";f.size=3;g_h14GripBody[0]=(void*)1;
 *(u32*)(wrappers[0]+0x3c)=42;*(const void**)(wrappers[0]+0x2e8)=(void*)1;
 C(h576av_decode_theta_token(&o,&c,&f)==1);C(g_s26gkThetaSourceBody==(void*)1);
 h576av_theta_clear_pending("test");f.text="B43";C(h576av_decode_theta_token(&o,&c,&f)==1);C(g_h576avThetaPendingHand==-1);
 printf("PASS %d exact source handoff authorization checks\n",checks);return 0;
}
'''
c=B/'source_handoff_gl.c';c.write_text(head+fn+main);exe=c.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
