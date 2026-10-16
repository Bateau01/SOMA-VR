from pathlib import Path
import ast,subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
t=ast.parse((R/'tests/test_shoulder_gestures.py').read_text())
head=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='head' for x in n.targets))
body=r'''
static char item,other;
static void tick(void){xr[0xE8/8]+=10000000;g_h14PhysicsSteps++;s26fw_begin_step();}
static void local(int h,int slot,float x,float y,float z){
 float c=cosf(yaw),s=sinf(yaw);
 wrist[h][0]=anchors[slot][0]+metric*(c*x+s*z);
 wrist[h][1]=anchors[slot][1]+metric*y;
 wrist[h][2]=anchors[slot][2]+metric*(-s*x+c*z);
}
int main(){int grid=0,added=0,poses=0;float r=.125f;xr[0xE8/8]=1000000000;
 for(int ix=-22;ix<=22;ix++)for(int iy=-30;iy<=20;iy++)for(int iz=-20;iz<=30;iz++){
  float x=ix*.01f,y=iy*.01f,z=iz*.01f;
  float core=s26fy_slot_score(x,y,z,r),deposit=s26fz_deposit_score(x,y,z,r);
  assert(deposit<=core+.00001f);
  if(z<=0)assert(deposit==core);
  if(deposit<=1&&core>1){assert(z>0);added++;}
  if(fabsf(x)>r*1.5f||y>r||y<-.231f||z>.243f)assert(deposit>1);
  assert(!(s26fz_deposit_score(x+.215f,y,z,r)<=1&&s26fz_deposit_score(x-.215f,y,z,r)<=1));
  grid++;
 }
 assert(added>0);
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++)for(int rot=0;rot<24;rot++)for(int sc=0;sc<3;sc++){
  s26fw_reset();yaw=rot*.2617993878f;metric=sc==0?.7f:sc==1?1:1.4f;
  local(h,slot,0,-.18f,.12f);g_h14GripBody[h]=&item;tick();
  assert(!s26fw_near(h,slot,0,0,0)); /* cannot retrieve from new deposit-only lobe */
  assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  /* Same-step wrist update cannot disagree with readiness until next snapshot. */
  local(h,slot,0,0,-.4f);assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  tick();assert(!s26fu_shoulder_stow_ready(h,&item,slot,1));
  g_h14GripBody[h]=0;poses++;
 }
 yaw=0;metric=1;
 /* Every cancellation is checked while in the NEW area, both hands and slots. */
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++)for(int mode=0;mode<12;mode++){
  s26fw_reset();local(h,slot,0,-.18f,.12f);g_h14GripBody[h]=&item;tick();assert(s26fu_shoulder_stow_ready(h,&item,slot,1));
  if(mode==0)g_h14GripBody[h]=0;
  if(mode==1)g_h14GripBody[1-h]=&item;
  if(mode==2)g_h15GripJointed[h]=1;
  if(mode==3)g_h484ClusterGrip[h]=1;
  if(mode==4)rawValid=0;
  if(mode==5)g_h5755asUiIslandActive=1;
  if(mode==6)g_h576bfMapTransitionActive=1;
  if(mode==7)g_h14GripBody[h]=&other;
  if(mode==9)g_s26CutsceneHandsHidden=1;
  if(mode==10)g_s26ManualHeal=1;
  if(mode==11)g_lastActive[h]=0;
  tick();assert(!s26fu_shoulder_stow_ready(h,&item,slot,mode!=8));
  g_h14GripBody[0]=g_h14GripBody[1]=0;g_h15GripJointed[h]=g_h484ClusterGrip[h]=0;rawValid=1;
  g_h5755asUiIslandActive=g_h576bfMapTransitionActive=g_s26CutsceneHandsHidden=g_s26ManualHeal=0;g_lastActive[h]=1;
 }
 /* Releasing elsewhere cannot arm a deposit merely because the dropped item is behind us. */
 s26fw_reset();g_h14GripBody[0]=0;local(0,0,0,-.18f,.12f);tick();assert(!s26fu_shoulder_stow_ready(0,&item,0,1));
 printf("PASS: %d sampled geometry checks, %d new rear/lower points, %d hand/slot/yaw/scale cases; unchanged front/lateral/retrieval bounds; no default slot overlap; new-region ownership/lifecycle gates and shared snapshots.\n",grid,added,poses);
}
'''
source=head+(R/'source/shoulder_geometry_fy.inc').read_text()+(R/'source/shoulder_gestures_fw.inc').read_text()+(R/'source/shoulder_stow_fu.inc').read_text()+body
p=B/'shoulder_deposit_test.c';p.write_text(source)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout);(B/'shoulder_deposit_results.json').write_text(json.dumps({'passed':True,'result':r.stdout,'scope':'Production geometry/gesture functions, synthetic tracking/ownership. Hardware validation pending.'},indent=2))
