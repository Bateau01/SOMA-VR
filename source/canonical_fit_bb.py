from pathlib import Path
import re
p=Path(__file__).resolve().with_name('s26n.c');s=p.read_text()
def span(name):
 m=re.search(r'^static [^\n;]*\b'+name+r'\([^;\n]*\)\s*\{',s,re.M);assert m,name
 a=s.index('{',m.start());b=a+1;d=1
 while d:d+=(s[b]=='{')-(s[b]=='}');b+=1
 return m.start(),b
def edit(name,f):
 global s
 a,b=span(name);s=s[:a]+f(s[a:b])+s[b:]
for name,args,call in [
 ('h20_skin_vertex_local','i32 hand,const H10Vert* v,const float* bones,float* out','hand,v,bones,out'),
 ('s26q_finger_points_pose','i32 hand,i32 finger,const float inCurl[4],const float* handM,float out[5][3],i32* outLen,u64 root','hand,finger,inCurl,handM,out,outLen,root'),
 ('s26q_link_frame_pose','i32 hand,i32 finger,i32 depth,const float cv[4],const float* handM,float* outSegM,float* outLen,u64 root','hand,finger,depth,cv,handM,outSegM,outLen,root')]:
 typ='void' if name.startswith('h20') else 'i32'
 def transform(x):
  x=x.replace(name+'('+args+')',name+'_metric('+args+',float metric)',1).replace('h5755ea_world_units_per_meter()','metric')
  if name=='s26q_link_frame_pose':x=x.replace('s26q_finger_points_pose(hand,finger,cv,handM,p,&len,root)','s26q_finger_points_pose_metric(hand,finger,cv,handM,p,&len,root,metric)')
  return x+'\nstatic '+typ+' '+name+'('+args+'){'+('return ' if typ!='void' else '')+name+'_metric('+call+',h5755ea_world_units_per_meter());}\n'
 edit(name,transform)
# Forward declaration required by the frame helper (points definition is later).
pos=s.index('static i32 s26q_link_frame_pose_metric')
s=s[:pos]+'static i32 s26q_finger_points_pose_metric(i32 hand,i32 finger,const float inCurl[4],const float* handM,float out[5][3],i32* outLen,u64 root,float metric);\n'+s[pos:]
def canonical(x):
 x=x.replace('*h5755ea_world_units_per_meter()','*1.0f')
 x=x.replace('h20_skin_vertex_local(hand,&vv[i],bones,hp)','h20_skin_vertex_local_metric(hand,&vv[i],bones,hp,1.0f)')
 return x
edit('h519_nearest_link',canonical)
def finger(x):
 x=canonical(x).replace('h18_finger_points_world(hand,f,zeroCv,ident,pts[f],&lens[f])','s26q_finger_points_pose_metric(hand,f,zeroCv,ident,pts[f],&lens[f],s26q_root_applied(hand,f),1.0f)').replace('h519_link_frame(hand,f,d,zeroCv,ident,frame[sl],&linkL[sl])','s26q_link_frame_pose_metric(hand,f,d,zeroCv,ident,frame[sl],&linkL[sl],s26q_root_applied(hand,f),1.0f)')
 x=x.replace('g_h519ExactLinks[hand]=(u32)made;','float metric=h5755ea_world_units_per_meter();for(i32 sl=0;sl<H519_LINK_COUNT;++sl)if(g_h519FingerValid[hand][sl]){g_h519FingerRadius[hand][sl]*=metric;g_h519FingerHeight[hand][sl]*=metric;for(i32 k=0;k<3;++k)g_h519FingerOffset[hand][sl][k]*=metric;}\n    g_h519ExactLinks[hand]=(u32)made;')
 return x
edit('h519_fit_finger_shell',finger)
# Palm body-to-hand translation is a world length: normalize before fitting.
def palm(x):
 x=canonical(x).replace('h10_build_rig(hand);float bones','float canonicalM[16];h10_copy_f(canonicalM,bodyToHand,16);float metric=h5755ea_world_units_per_meter();for(i32 k=0;k<3;++k)canonicalM[12+k]/=metric;bodyToHand=canonicalM;\n    h10_build_rig(hand);float bones')
 x=x.replace('if(outN<3)return 0;','if(outN<3)return 0;for(i32 q=0;q<outN;++q)for(i32 k=0;k<3;++k){outDims[q][k]*=metric;outM[q][12+k]*=metric;}')
 return x
edit('h504_fit_palm_boxes',palm)
s=s.replace('H504_NEAR_HALF+','(H504_NEAR_HALF*h5755ea_world_units_per_meter())+')
s=s.replace('ext_OrigDrawHandMesh(hand,pos,authoredScale)','ext_OrigDrawHandMesh(hand,pos,authoredScale*h5755ea_world_units_per_meter())')
s=s.replace('Simon hand mesh/collision authored 1.0000','Simon hand mesh/collision compensate to preserve apparent size').replace('Simon visual + physical hands LOCKED authored scale 1.0000','Simon visual + physical hands preserve apparent size')
s=s.replace('every active Simon hand family draws at authoredScale 1.0000; palm/finger collision is fitted from that exact mesh; world-scale setting NEVER rescales the hand mesh, bones, palm slabs, phalanx capsules, or grab anchors','every active Simon hand family uses one compensated visual/physical scale; canonical mesh fit is scaled uniformly; rigid tracking frames remain unit length')
p.write_text(s)
