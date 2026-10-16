from pathlib import Path
import subprocess,sys,re,itertools
R=Path(__file__).resolve().parents[1]
s=(R/'source/s26n.c').read_text()
expr=re.search(r'i32 terminalTouch=(.*?);',s).group(1)
code='''#include <stdio.h>
typedef unsigned u32;
int g_h576boEntryHand,g_h576boPointerDown,g_h576boPointerHand,g_s26hdLaserEnabled,g_s26hdLaserHand;
u32 g_h576bsTerminalNearStep[2],g_h14PhysicsSteps=100;
int main(){int checks=0;
for(int enabled=0;enabled<2;enabled++)for(int laser=-1;laser<2;laser++)for(int entry=-1;entry<2;entry++)for(int pointer=-1;pointer<2;pointer++)for(int down=0;down<2;down++)for(int near=0;near<2;near++)for(int h=0;h<2;h++){
g_s26hdLaserEnabled=enabled;g_s26hdLaserHand=laser;g_h576boEntryHand=entry;g_h576boPointerHand=pointer;g_h576boPointerDown=down;g_h576bsTerminalNearStep[h]=near?100:0;
int actual=EXPRESSION;
int expected=(entry==h)||(down&&pointer==h&&!(enabled&&laser==h))||near;
if(actual!=expected)return 1;
if(!enabled && actual!=((entry==h)||(down&&pointer==h)||near))return 2;
checks++;
}printf("PASS %d contact ownership cases; disabled path unchanged; near contact retained\\n",checks);}
'''.replace('EXPRESSION',expr)
assert 'g_s26hdLaserHand=h;g_h576boEntryHand=-1;' in (R/'source/accessibility_hd.inc').read_text()
p=R/'build/pointer_hm.c';p.write_text(code);exe=p.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
