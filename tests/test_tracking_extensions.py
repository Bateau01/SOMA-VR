from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];B=R/'build';src=(R/'source/tracking_q.inc').read_text()
def function(name):
 a=src.index('static i32 '+name) if name=='s26q_name_eq' else src.index('static i32 __attribute__((ms_abi)) '+name)
 start=src.index('{',a);depth=0
 for i in range(start,len(src)):
  depth+=(src[i]=='{')-(src[i]=='}')
  if depth==0:return src[a:i+1]
header='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int i32;typedef unsigned u32;typedef unsigned char u8;typedef unsigned long long u64;typedef long long i64;typedef void* Handle;
static void zero_bytes(void*p,u64 n){memset(p,0,n);}static void ext_Log(const char*s,...){(void)s;}
static void* ext_malloc(u64 n){return malloc(n);}static void ext_free(void*p){free(p);}
'''
types=src[:src.index('static u8 g_s26qTrackerEnabled;')]
mock=r'''
static u8 g_s26qTrackerEnabled,g_s26qHandExtension,g_s26sEyeExtension,g_s26dgFrameExtension,g_s26dnMotionRangeEnabled;
static const char* options[]={"XR_HTCX_vive_tracker_interaction","XR_EXT_hand_tracking","XR_EXT_eye_gaze_interaction","XR_VALVE_frame_controller_interaction","XR_EXT_hand_joints_motion_range","XR_KHR_composition_layer_depth"};
static u32 mask;static int failRange,failFrame,failOptional,failDepth,calls;static u32 lastCount;
static i32 __attribute__((ms_abi)) enumerate(const char*s,u32 cap,u32*n,S26QExtension*p){
 *n=0;for(int i=0;i<6;i++)if(mask&(1<<i)){if(cap)strcpy(p[*n].extensionName,options[i]);++*n;}return 0;}
static i32 __attribute__((ms_abi)) create(const S26QInstanceInfo*i,Handle*out){
 ++calls;lastCount=i->enabledExtensionCount;*out=0;
 for(u32 j=0;j<i->enabledExtensionCount;j++){
  for(u32 k=j+1;k<i->enabledExtensionCount;k++)if(!strcmp(i->enabledExtensionNames[j],i->enabledExtensionNames[k]))return -99;
  if(failRange&&!strcmp(i->enabledExtensionNames[j],options[4]))return -9;
  if(failFrame&&!strcmp(i->enabledExtensionNames[j],options[3]))return -9;
  if(failDepth&&!strcmp(i->enabledExtensionNames[j],options[5]))return -9;
  if(failOptional&&j>0)return -9;
 }*out=(Handle)1;return 0;
}
'''
main=r'''
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
int main(void){int checks=0;const char* names[]={"XR_KHR_opengl_enable",options[3]};S26QInstanceInfo in={0};in.type=3;in.enabledExtensionCount=1;in.enabledExtensionNames=names;
 g_s26qCreateInstance=create;g_s26qEnumExtensions=enumerate;Handle h=0;
 for(mask=0;mask<64;mask++){calls=0;CHECK(s26q_create_instance(&in,&h)==0&&h);CHECK(g_s26edDepthExtension==!!(mask&32));CHECK(g_s26qTrackerEnabled==!!(mask&1));CHECK(g_s26qHandExtension==!!(mask&2));CHECK(g_s26sEyeExtension==!!(mask&4));CHECK(g_s26dgFrameExtension==!!(mask&8));CHECK(g_s26dnMotionRangeEnabled==!!((mask&16)&&(mask&2)));CHECK(calls==1);}
 mask=63;failDepth=1;calls=0;CHECK(s26q_create_instance(&in,&h)==0);CHECK(calls==2&&!g_s26edDepthExtension&&g_s26dnMotionRangeEnabled&&g_s26dgFrameExtension&&g_s26qHandExtension&&g_s26sEyeExtension&&g_s26qTrackerEnabled);failDepth=0;
 mask=63;failRange=1;calls=0;CHECK(s26q_create_instance(&in,&h)==0);CHECK(calls==3&&!g_s26dnMotionRangeEnabled&&!g_s26edDepthExtension&&g_s26dgFrameExtension&&g_s26qHandExtension);failRange=0;
 mask=31;failRange=1;calls=0;CHECK(s26q_create_instance(&in,&h)==0);CHECK(calls==2&&!g_s26dnMotionRangeEnabled&&g_s26dgFrameExtension&&g_s26qHandExtension);failRange=0;
 mask=15;failFrame=1;calls=0;CHECK(s26q_create_instance(&in,&h)==0);CHECK(calls==2&&!g_s26dgFrameExtension&&g_s26sEyeExtension&&g_s26qHandExtension);
 failFrame=0;failOptional=1;calls=0;CHECK(s26q_create_instance(&in,&h)==0);CHECK(calls==3&&!g_s26sEyeExtension&&!g_s26qHandExtension&&!g_s26dgFrameExtension);
 failOptional=0;in.enabledExtensionCount=2;CHECK(s26q_create_instance(&in,&h)==0&&g_s26dgFrameExtension&&lastCount==5);
 printf("PASS: %d extension negotiation checks (64 capability combinations incl. depth layer, depth/range dependency and rejection, duplicates, Frame rejection, full fallback)\n",checks);return 0;
}
'''
c=B/'tracking_extensions_test.c';c.write_text(header+types+mock+function('s26q_name_eq')+function('s26q_create_instance')+main)
exe=B/'tracking_extensions_test.exe';subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
