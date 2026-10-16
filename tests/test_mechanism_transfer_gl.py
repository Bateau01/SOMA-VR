from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8');B=R/'build';B.mkdir(exist_ok=True)
a=s.index('        // Called by the exact prop script BEFORE native mechanism Setup.');b=s.index('\n    }',a)
fn='static int transfer(void){\n'+s[a:b]+'\n}\n'
head=r'''
#include <stdio.h>
typedef int i32;
static int g_h576avActiveInteractHand,g_h576mScriptRuntimePublished,g_h5755chGrabExpected,g_h5755chGrabPrimaryHand,g_h5755chGrabStateActive,g_h5755cjGrabExpectedStep,g_s26glMechanismTransferHand;
static const void *g_h576avActiveInteractBody,*g_h14GripBody[2],*g_h5755chGrabStateBody,*g_h5755chGrabStateWrapper,*g_h5755chGrabStateOwner;
static int releases,checks;
static void h14_release(int h,const char*why){releases++;g_h14GripBody[h]=0;}
static void reset(void){g_h576avActiveInteractHand=0;g_h576mScriptRuntimePublished=1;g_h5755chGrabExpected=1;g_h5755chGrabPrimaryHand=0;g_h576avActiveInteractBody=g_h14GripBody[0]=(void*)1;g_h14GripBody[1]=(void*)2;g_s26glMechanismTransferHand=-1;releases=0;}
#define C(x) do{checks++;if(!(x)){printf("FAIL %d %s\n",__LINE__,#x);return 1;}}while(0)
'''
main=r'''
int main(void){
 reset();C(transfer());C(releases==1&&!g_h14GripBody[0]&&g_h14GripBody[1]==(void*)2);C(g_s26glMechanismTransferHand==0&&!g_h5755chGrabExpected);C(!transfer()&&releases==1);
 reset();g_h576mScriptRuntimePublished=0;C(!transfer()&&!releases);
 reset();g_h576avActiveInteractHand=-1;C(!transfer()&&!releases);
 reset();g_h576avActiveInteractHand=2;C(!transfer()&&!releases);
 reset();g_h576avActiveInteractBody=0;C(!transfer()&&!releases);
 reset();g_h576avActiveInteractBody=(void*)2;C(!transfer()&&!releases);
 reset();g_h5755chGrabExpected=0;C(!transfer()&&!releases);
 reset();g_h5755chGrabPrimaryHand=1;C(!transfer()&&!releases);
 printf("PASS %d mechanism-transfer scope checks\n",checks);return 0;
}
'''
c=B/'mechanism_transfer_gl.c';c.write_text(head+fn+main);exe=c.with_suffix('.exe')
subprocess.run([sys.argv[1],'cc','-O2',str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
