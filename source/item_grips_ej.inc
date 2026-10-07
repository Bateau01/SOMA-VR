/* Shared authored retrieval poses. No disk overrides or capture path. */
typedef struct {char name[96];i32 hand,kind;float rotation[9],fraction[3],joint[5][4];} S26EJGrip;
#include "authored_grips_el.inc"
static i32 s26ej_grip_override(i32 hand,i32 kind,const char* name,float* rotation,float* fraction){
    if(hand<0||hand>1)return 0;g_s26ejHolsterJointValid[hand]=0;
    const S26EJGrip* e=s26el_default_grip(hand,kind,name);if(!e)return 0;
    for(i32 i=0;i<9;++i)rotation[i]=e->rotation[i];for(i32 i=0;i<3;++i)fraction[i]=e->fraction[i];
    for(i32 f=0;f<5;++f){float sum=0;for(i32 d=0;d<4;++d){g_s26ejHolsterJoint[hand][f][d]=e->joint[f][d];sum+=e->joint[f][d];}g_s26efHolsterCurl[hand][f]=sum*.25f;}
    g_s26ejHolsterJointValid[hand]=1;return 1;
}
static i32 s26el_grip_model_command(const H5730TString* command){
 g_s26elGripScope[0]=0;
 if(h5748t_sso_eq(command,"END",3u))return 1;
 char key[96];if(!h5748n_copy_tstring((void*)command,key,sizeof(key)))return 0;
 for(i32 kind=0;kind<3;++kind)if(s26el_default_grip(0,kind,key)){h5748n_copyz(g_s26elGripScope,sizeof(g_s26elGripScope),key);return 1;}
 return 0;
}
