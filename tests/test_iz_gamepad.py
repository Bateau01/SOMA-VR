"""Production final-Look routing test; not hardware input validation."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'audit/ja-gamepad';out.mkdir(parents=True,exist_ok=True)
s=(r/'source/s26n.c').read_text();a=s.index('static void __attribute__((ms_abi)) h37a_global_player_analog_guard(');b=s.index('static void* h34_player_input_interface',a)
code=r"""
#include <assert.h>
#include <stdio.h>
typedef int i32;typedef unsigned u32;
#define H34_ANALOG_LOOK 1
static int g_h37aSyntheticAnalogDepth,g_h37aSyntheticAnalogHand,g_h37aSyntheticFellThrough,g_niInputMode,gameplay,g_s26nPhiRemote;
static unsigned g_h37aGlobalLookSuppressed[2];static int calls,id;static float received[3];
static int h5755dg_gameplay_vr(void){return gameplay;}
static void __attribute__((ms_abi)) original(void*p,int analog,const float*a){calls++;id=analog;if(a)for(int i=0;i<3;i++)received[i]=a[i];}
static void (__attribute__((ms_abi)) *o_h37aGlobalPlayerAnalog)(void*,int,const float*)=original;
"""+s[a:b]+r"""
int main(void){int cases=0;float input[3]={.25f,-.75f,.125f};
for(int mode=0;mode<3;mode++)for(int active=0;active<2;active++)for(int analog=0;analog<8;analog++){
 g_niInputMode=mode;gameplay=active;calls=0;
 h37a_global_player_analog_guard(0,analog,input);
 assert(calls==1&&id==analog);assert(received[0]==input[0]&&received[2]==input[2]);
 assert(received[1]==((mode==2&&active&&analog==H34_ANALOG_LOOK)?0:input[1]));
 assert(input[1]==-.75f);cases++;
}
g_niInputMode=2;gameplay=1;g_s26nPhiRemote=1;calls=0;h37a_global_player_analog_guard(0,H34_ANALOG_LOOK,input);assert(calls==1&&received[1]==input[1]);g_s26nPhiRemote=0;
g_h37aSyntheticAnalogDepth=1;g_h37aSyntheticAnalogHand=1;calls=0;
h37a_global_player_analog_guard(0,H34_ANALOG_LOOK,input);assert(calls==0&&g_h37aSyntheticFellThrough&&g_h37aGlobalLookSuppressed[1]==1);
g_h37aSyntheticAnalogDepth=0;calls=0;h37a_global_player_analog_guard(0,H34_ANALOG_LOOK,0);assert(calls==1);
printf("PASS %d mode/presentation/analog combinations; existing synthetic guard and null forwarding retained\n",cases);
}
"""
(out/'routing.c').write_text(code)
subprocess.run([sys.argv[1],'cc','-O2',str(out/'routing.c'),'-o',str(out/'routing.exe')],check=True)
a=subprocess.run([str(out/'routing.exe')],check=True,capture_output=True,text=True);(out/'result.txt').write_text(a.stdout);print(a.stdout)
