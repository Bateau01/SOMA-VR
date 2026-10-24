"""Compiled production-script recurrence, not a native gameplay test. Validate gap timeout and unchanged legacy recurrence."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1]
def piece(s):
 a=s.index('  float fSlowDownSpeed',s.index('// The DLL'))
 b=s.index('  // H57.55EO: physical SwingDoor',a)
 return s[a:b].replace('cVector2f(0)','0')
cur=(R/'runtime/script/player/PlayerState_Interact_RotateBase.hps').read_text();old=(R/'tests/fixtures/iq_baseline/PlayerState_Interact_RotateBase.hps').read_text()
head=r"""#include <cmath>
#include <cstdio>
#include <cstring>
static float mfRotSpeed,mfMoveSlowDownFactor=3,mvMoveAdd,mfHPL3VRLeverSpeedAdd,mfMoveSpeedFactor=1,mfIQLeverSampleAge;
static bool mbResetSpeedWhenNoMouseMovement=true,mbHPL3VRLeverInputThisStep,mbHPL3VRSwingDirect,mbIQLeverSampleGaps;
static void* pCam;static float GetSpeedAdd(void*){return 0;}static float cMath_Abs(float x){return std::fabs(x);}
"""
main=r"""int main(){int n=0;
#define C(x) do{n++;if(!(x)){printf("FAIL %d\n",__LINE__);return 1;}}while(0)
for(int hz=60;hz<=120;hz+=60)for(int i=0;i<10000;i++){
 float start=(i%201-100)*.1f;mfHPL3VRLeverSpeedAdd=(i%33-16)*.001f;mbHPL3VRLeverInputThisStep=i%3!=0;mbIQLeverSampleGaps=false;
 mfRotSpeed=start;baseline(1.f/hz);float expected=mfRotSpeed;mfRotSpeed=start;candidate(1.f/hz);C(memcmp(&expected,&mfRotSpeed,4)==0);
}
mbIQLeverSampleGaps=true;mfIQLeverSampleAge=0;mfRotSpeed=2;mbHPL3VRLeverInputThisStep=false;
candidate(1.f/120);C(mfRotSpeed>1.9f);C(mfIQLeverSampleAge>0);
mbHPL3VRLeverInputThisStep=true;mfHPL3VRLeverSpeedAdd=0;candidate(1.f/120);C(mfRotSpeed==0);C(mfIQLeverSampleAge==0);
mfRotSpeed=2;mbHPL3VRLeverInputThisStep=false;for(int j=0;j<7;j++)candidate(1.f/120);C(mfRotSpeed==0); // no fresh input cannot drive indefinitely
mbHPL3VRLeverInputThisStep=true;mfHPL3VRLeverSpeedAdd=-.01f;candidate(1.f/120);C(mfRotSpeed<0);C(mfIQLeverSampleAge==0);
printf("PASS %d recurrence assertions: legacy bit-equivalence, gap, immediate stop, stale timeout and restart\n",n);}
"""
p=R/'build/lever_motor_gaps_iq.cpp';p.write_text(head+'static void baseline(float afTimeStep){'+piece(old)+'}\nstatic void candidate(float afTimeStep){'+piece(cur)+'}\n'+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
v=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);print(v.stdout);assert v.returncode==0
(R/'docs/v109-evidence/lever_motor_gaps_iq.json').write_text(json.dumps({'scope':__doc__,'output':v.stdout}))
