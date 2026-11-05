from pathlib import Path
import subprocess
r=Path('.').resolve();s=(r/'source/s26n.c').read_text(encoding='cp1252');a=s.index('static i32 g_s26jeTerminalUseQuery');b=s.index('/* BW: synchronous',a);code=s[a:b]
head=r'''
#include <cstdio>
#include <cstring>
using i32=int;
struct H576AAInvItem{int stowed;const void*raw;};
int g_h576mScriptRuntimePublished=1,g_h576bfMapTransitionActive,g_s26ManualHeal,g_s26CutsceneHandsHidden;
const char*g_h5729LastClassName="cScrPlayerState_Normal";const void*g_h14GripBody[2]={(void*)1,0};
int on=1,running=1,pause=0,grab=0,terminal=0,policy=0,valid[2]={1,1},queryCalls;
int p2_xr_on(){return on;}int p2_xr_running(){return running;}int h5754h_pause_active(){return pause;}
int h5720_streq(const char*a,const char*b){return !strcmp(a,b);}int h5755fm_grab_gameplay_actions_allowed(){return grab;}
int h5730_exact_terminal_state(int,int,int,int){return terminal;}int visual_pose_valid(int h){return valid[h];}
void h576aa_run_global(const char*,const char*,const char*);
#define C(x) do{if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}++checks;}while(0)
'''
main=r'''
void h576aa_run_global(const char*,const char*,const char*){++queryCalls;if(g_s26jeTerminalUseQuery)g_s26jeTerminalUseAllowed=policy;}
int main(){int checks=0;H576AAInvItem it{0,(void*)1};C(s26_tool_hand_authorized(&it));
g_h5729LastClassName="terminal";terminal=1;policy=1;C(!s26_tool_hand_authorized(&it));C(s26_tool_hand_authorized_impl(&it,1));
policy=0;C(!s26_tool_hand_authorized_impl(&it,1));policy=1;
for(int* gate:{&pause,&g_h576bfMapTransitionActive,&g_s26ManualHeal,&g_s26CutsceneHandsHidden}){*gate=1;C(!s26_tool_hand_authorized_impl(&it,1));*gate=0;}
it.stowed=1;C(!s26_tool_hand_authorized_impl(&it,1));it.stowed=0;
it.raw=(void*)2;C(!s26_tool_hand_authorized_impl(&it,1));it.raw=(void*)1;
valid[0]=0;C(!s26_tool_hand_authorized_impl(&it,1));valid[0]=1;
terminal=0;C(!s26_tool_hand_authorized_impl(&it,1));grab=1;C(s26_tool_hand_authorized(&it));
C(!g_s26jeTerminalUseQuery);printf("PASS %d authorization checks; extracted implementation with mocked native state\n",checks);}
'''
head='#include <initializer_list>\n'+head
p=r/'build/je-permission.cpp';p.write_text(head+code+main)
zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout);assert v.returncode==0
(r/'audit/je-terminal-latch/helper.txt').write_text(v.stdout)


assert "return s26_tool_hand_authorized_impl(h576aa_inv_find_logical(name),1);" in (r/"source/s26n.c").read_text(encoding="cp1252")
