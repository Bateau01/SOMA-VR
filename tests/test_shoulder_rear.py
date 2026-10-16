from pathlib import Path
import ast,subprocess,sys,json
R=Path(__file__).resolve().parents[1];B=R/'build';B.mkdir(exist_ok=True)
tree=ast.parse((R/'tests/test_shoulder_gestures.py').read_text())
head=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='head' for t in n.targets))
s=(R/'source/s26n.c').read_text()
def function(name):
 a=s.index('static ',s.index(name+'(')-12);b=s.index('{',a)+1;d=1
 while d:d+=(s[b]=='{')-(s[b]=='}');b+=1
 return s[a:b]
body=r"""
static void local(S26FWFrame*f,int slot,float x,float y,float z){
 float c=cosf(f->yaw),s=sinf(f->yaw),k=f->metric;
 f->wrist[0]=f->anchor[slot][0]+k*(c*x+s*z);
 f->wrist[1]=f->anchor[slot][1]+k*y;
 f->wrist[2]=f->anchor[slot][2]+k*(-s*x+c*z);
}
int main(){int grid=0,pose=0,added=0;float r=.125f;
 // Exhaustive sampled comparison: old core retained, no new front acceptance.
 for(int ix=-22;ix<=22;ix++)for(int iy=-16;iy<=16;iy++)for(int iz=-18;iz<=18;iz++){
  float x=ix*.01f,y=iy*.01f,z=iz*.01f;
  float old=(x/(r*1.5f))*(x/(r*1.5f))+(y/r)*(y/r)+(z/(r*.65f))*(z/(r*.65f));
  float now=s26fy_slot_score(x,y,z,r);
  if(z<=0)assert(fabsf(old-now)<.0001f);
  if(old<=1)assert(now<=1.00001f);
  if(now<=1&&old>1){assert(z>0);added++;}
  if(fabsf(x)>r*1.5f||fabsf(y)>r)assert(now>1);
  grid++;
 }
 assert(added>0);
 // Both slots; movement/lean/crouch translations, full yaw, three world scales.
 for(int side=0;side<2;side++)for(int rot=0;rot<24;rot++)for(int sc=0;sc<3;sc++)for(int shift=0;shift<3;shift++){
  S26FWFrame f={0};f.valid=1;f.yaw=rot*.2617993878f;f.metric=sc==0?.7f:sc==1?1:1.4f;
  f.anchor[side][0]=shift*.2f;f.anchor[side][1]=2-shift*.3f;f.anchor[side][2]=-4+shift*.1f;
  local(&f,side,0,0,.14f);assert(s26fw_frame_inside(&f,side,r,0));
  local(&f,side,0,0,-.09f);assert(!s26fw_frame_inside(&f,side,r,0));
  local(&f,side,0,0,.17f);assert(!s26fw_frame_inside(&f,side,r,0));
  local(&f,side,.19f,0,.08f);assert(!s26fw_frame_inside(&f,side,r,0));
  // Front/rear debug surface agrees with admission surface.
  yaw=f.yaw;metric=f.metric;
  for(int rear=0;rear<2;rear++)for(int a=1;a<12;a++){
   float m[16];h576ap_make_slot_model(f.anchor[side],r,rear,m);
   float angle=a*.2617993878f,x=cosf(angle),z=(rear?1:-1)*sinf(angle);
   for(int k=0;k<3;k++)f.wrist[k]=m[12+k]+m[k]*x+m[8+k]*z;
   float q=0;h576an_point_in_body_slot(f.wrist,f.anchor[side],r,0,&q);assert(fabsf(q-1)<.00002f);
  }
  pose++;
 }
 // No overlap between default left/right initial admission regions.
 for(int ix=-45;ix<=45;ix++)for(int iy=-20;iy<=20;iy++)for(int iz=-20;iz<=25;iz++){
  float x=ix*.01f,y=iy*.01f,z=iz*.01f;
  assert(!(s26fy_slot_score(x+.215f,y,z,r)<=1&&s26fy_slot_score(x-.215f,y,z,r)<=1));
 }
 // Rear-only readiness still requires same owned body and script eligibility.
 static char item;metric=1;yaw=0;xr[0xE8/8]=1000000000;s26fw_begin_step();
 for(int h=0;h<2;h++)for(int slot=0;slot<2;slot++){
  s26fw_reset();s26fw_begin_step();h10_copy_f(wrist[h],anchors[slot],3);wrist[h][2]+=.14f;
  g_h14GripBody[h]=&item;assert(!s26fu_shoulder_stow_ready(h,&item,slot,0));
  assert(s26fu_shoulder_stow_ready(h,&item,slot,1));g_h14GripBody[h]=0;
  assert(!s26fu_shoulder_stow_ready(h,&item,slot,1));
 }
 printf("PASS: %d sampled geometry comparisons; %d newly accepted rear points; %d translated/rotated/scaled poses; debug boundaries; default shoulder separation; rear ownership and eligibility.\n",grid,added,pose);
}
"""
source=head+'\n#define ext_Sqrtf sqrtf\n'+(R/'source/shoulder_geometry_fy.inc').read_text()+function('h576an_point_in_body_slot')+function('h576ap_make_slot_model')+(R/'source/shoulder_gestures_fw.inc').read_text()+(R/'source/shoulder_stow_fu.inc').read_text()+body
p=B/'shoulder_rear_test.c';p.write_text(source)
subprocess.run([sys.argv[1],'cc',str(p),'-o',str(p.with_suffix('.exe'))],check=True)
r=subprocess.run([str(p.with_suffix('.exe'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
print(r.stdout);(B/'shoulder_rear_results.json').write_text(json.dumps({'passed':True,'result':r.stdout,'scope':'Production geometry and gesture functions, synthetic state. Not headset feel validation.'},indent=2))

