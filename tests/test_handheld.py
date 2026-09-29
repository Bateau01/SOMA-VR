"""Production tablet contact latch and state gate with mocked engine boundaries."""
from pathlib import Path
import ast,re,subprocess,sys,json
R=Path(__file__).resolve().parents[1];s=(R/'source/s26n.c').read_text(encoding='utf-8-sig')
def fn(name):
 a=re.search(r'static i32 '+name+r'\([^;{}]*\)\s*\{',s).start();b=s.index('{',a);n=1;i=b+1
 while n:n+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
tree=ast.parse((R/'tests/test_apartment.py').read_text())
header=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='header' for t in n.targets))
header+='''
const void* g_s26ckPadBody;
int stateValid=1;
void h5720_strcpy(char* out,u32 n,const char* s){snprintf(out,n,"%s",s);}
void* h5720_player_state(char* m,u32 mn,char* c,u32 cn){h5720_strcpy(m,mn,g_h5729LastModuleName);h5720_strcpy(c,cn,g_h5729LastClassName);return stateValid?(void*)1:nullptr;}
'''
main=r'''
int main(){
 for(int hand=0;hand<2;hand++)for(int bad=0;bad<9;bad++){
  g_h14GripBody[0]=g_h14GripBody[1]=nullptr;g_h30NativeMouseDown=0;
  g_s26ckPadBody=(void*)7;g_lastSqueezeActive[hand]=1;g_lastSqueeze[hand]=1;
  externalJoint=0;mass=.35f;poseOK=latchOK=1;begins=latches=0;
  H25PendingInteract p={0,10,(void*)7,{0,0,0}};
  if(bad==1)p.jointed=1;if(bad==2)g_s26ckPadBody=(void*)8;if(bad==3)p.physicsStep=9;
  if(bad==4)g_lastSqueeze[hand]=0;if(bad==5)externalJoint=1;
  if(bad==6)mass=0;if(bad==7)poseOK=0;if(bad==8)latchOK=0;
  CHECK(s26ck_latch_tablet(hand,&p,owner,(void*)3)==(bad==0));
  CHECK(begins==0); // Must never synthesize another native Grab input.
  if(bad==0)CHECK(g_h14GripBody[hand]==p.newtonBody);
 }
 g_h5729LastModuleName="player/PlayerState_Interact_Terminal.hps";g_h5729LastClassName="cScrPlayerState_Interact_Terminal";
 g_s26ckPadBody=nullptr;CHECK(h5730_exact_terminal_state(nullptr,0,nullptr,0));
 g_h5729LastModuleName="player/PlayerState_Interact_HandheldTerminal.hps";g_h5729LastClassName="cScrPlayerState_Interact_HandheldTerminal";
 CHECK(!h5730_exact_terminal_state(nullptr,0,nullptr,0));
 g_s26ckPadBody=(void*)7;CHECK(h5730_exact_terminal_state(nullptr,0,nullptr,0));
 g_h5729LastClassName="cScrPlayerState_Normal";CHECK(!h5730_exact_terminal_state(nullptr,0,nullptr,0));
 stateValid=0;CHECK(!h5730_exact_terminal_state(nullptr,0,nullptr,0));
 printf("PASS %d handheld pickup and input-state gate checks\n",checks);
}
'''
p=R/'build/handheld.cpp';exe=R/'build/handheld.exe';p.write_text(header+fn('s26ck_latch_tablet')+fn('h5730_exact_terminal_state')+main)
subprocess.run([sys.argv[1],'c++','-O2',str(p),'-o',str(exe)],check=True)
v=subprocess.run([str(exe)],capture_output=True,text=True);print(v.stdout+v.stderr)
(R/'audit/handheld_tests.json').write_text(json.dumps({'exit':v.returncode,'output':v.stdout,'scope':'Production functions with engine mocks. Real GUI callbacks tested separately inside SOMA.'},indent=2));raise SystemExit(v.returncode)
