
#include <cstdio>
#include <cstring>
#undef NDEBUG
#include <cassert>
#include <cstdint>
using u8=unsigned char;using u32=unsigned;using u64=uint64_t;using i64=int64_t;using i32=int;
#define H5755BH_GAMEPLAY_VR 3
u32 g_h576bfMapTransitionActive,g_h5755bhPresentationState=3,g_h5755asUiIslandActive,g_h5755asResumeClassifyActive,g_h5755azExitPending,g_s26CutsceneHandsHidden;
u32 g_frameCounter=7,g_h14PhysicsSteps=4,g_h532Dormant[2],g_h532ArmState[2]={2,2},g_h531TrackedTargetValid[2]={1,1};
u32 g_h545ContactThisStep[2],g_h5755efHandIdleParked[2],g_h5755deContactVisualActive[2],g_h567BlockedHold[2],g_h15GripJointed[2];
void* g_h34HandNewton[2]={(void*)1,(void*)2};void*g_h14GripBody[2];
float g_h14LastPhysicsDt=1.f/120,cam[16],origin[3],g_h531TrackedTarget[2][16],g_h526Target[2][16],g_h528TargetVel[2][3];
struct V{float x,y,z;};struct Pose{V position;};Pose g_lastPose[2];
int reads=0,writes=0;bool flag=false,frameFlag=false;
void zero_bytes(void*p,size_t n){memset(p,0,n);}void ext_Log(const char*,...){}
int make_sibling_path(char*p,u32 n,const char*s){snprintf(p,n,"%s",s);return 1;}
void* ext_fopen(const char*p,const char*m){if(strstr(p,"frame_timing.flag"))return frameFlag?(void*)3:nullptr;if(strstr(p,".flag"))return flag?(void*)3:nullptr;writes++;return fopen("capture_if_test.bin",m);}
int ext_fclose(void*p){return p==(void*)3?0:fclose((FILE*)p);}
u64 ext_fwrite(const void*p,u64 n,u64 c,void*f){return fwrite(p,n,c,(FILE*)f);}
void*p2_camera_obj(){return cam;}int p2_xr_origin_set(){return 1;}float*p2_xr_origin(){return origin;}void*p2_xr_obj(){return nullptr;}
void getMatrix(void*,float*m){reads++;memset(m,0,64);m[0]=m[5]=m[10]=m[15]=1;m[12]=.5f;}
void getVelocity(void*,float*v){reads++;v[0]=1;}
auto p_h14GetMatrix=getMatrix;auto p_h14GetVelocity=getVelocity;
#include "../source/hand_timing_audit_if.inc"
int main(){
 s26if_hand_capture(0);assert(reads==0&&g_s26ifCount==0);flag=true;
 s26if_hand_capture(0);assert(reads==0); // missing flag remains disabled this launch
 g_s26ifInit=0;frameFlag=true;s26if_hand_capture(0);assert(reads==0&&g_s26ifCount==0);
 g_s26ifInit=0;frameFlag=false;g_h576bfMapTransitionActive=1;s26if_hand_capture(0);assert(reads==0);
 g_h576bfMapTransitionActive=0;g_h5755asUiIslandActive=1;s26if_hand_capture(1);assert(reads==0);
 g_h5755asUiIslandActive=0;g_s26CutsceneHandsHidden=1;s26if_hand_capture(0);assert(reads==0);
 g_s26CutsceneHandsHidden=0;g_h34HandNewton[1]=nullptr;
 s26if_hand_capture(0);assert(g_s26ifCount==1&&reads==2);s26if_hand_flush();assert(writes==0);
 g_h34HandNewton[1]=(void*)2;g_h14GripBody[0]=(void*)0x1234;
 for(int k=0;k<5000;k++)s26if_hand_capture(k%2);
 assert(g_s26ifCount==S26IF_HAND_ROWS);int n=reads;s26if_hand_capture(0);assert(reads==n);
 assert(g_s26ifRows[1].held==0x1234&&g_s26ifRows[1].physical[0]==.5f);
 s26if_hand_flush();assert(writes==1);s26if_hand_flush();assert(writes==1);
 FILE*f=fopen("capture_if_test.bin","rb");assert(f);u32 h[4];assert(fread(h,16,1,f)==1);assert(h[0]==0x46494853&&h[2]==sizeof(S26IFHandSample)&&h[3]==8192);fseek(f,0,SEEK_END);assert(ftell(f)==16+8192*sizeof(S26IFHandSample));fclose(f);
 printf("PASS capture OFF, map/UI/script quarantine, absent hand, bounded memory, one save, file integrity; row=%zu\n",sizeof(S26IFHandSample));
}
