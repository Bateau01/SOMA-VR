from pathlib import Path
import struct,json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];G=Path('/PATH/TO/SOMA')
R.mkdir(exist_ok=True,parents=True)
cal={}
for line in (G/'hpl3vr_hand_calibration.ini').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);cal[k]=float(v)
def unit(x):
 n=np.linalg.norm(x);return x/n if n>1e-9 else np.array([0.,0.,1.])
def rotate(axis,angle):
 x,y,z=unit(axis);K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);a=np.deg2rad(angle);m=np.eye(4);m[:3,:3]=np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K);return m
results=[]
for side in ['left','right']:
 p=G/f'hand_{side}.skin';b=p.read_bytes();_,nv,nj,*pivot=struct.unpack_from('<3I3f',b)
 v=np.frombuffer(b,offset=24,count=nv*16,dtype='<f4').reshape(-1,16);ids=v[:,8:12].copy().view('<i4');weights=v[:,12:16]
 joints=[struct.unpack_from('<2i35f',b,24+nv*64+i*148) for i in range(nj)]
 local=[np.array(j[5:21]).reshape(4,4) for j in joints];inv=[np.array(j[21:37]).reshape(4,4) for j in joints];world=[];depth=[];label=[]
 for j,m in zip(joints,local):
  par,flags=j[:2];world.append(m if par<0 else world[par]@m)
  depth.append((depth[par]+1 if par>=0 and joints[par][1]&1 else 0) if flags&1 else -1)
  label.append((flags>>4)&15 if flags&1 else -1)
 roots={label[i]:world[i][:3,3] for i in range(nj) if depth[i]==0};normal=unit(np.cross(roots[4]-roots[1],roots[2]-pivot));axes=[]
 for i,j in enumerate(joints):
  if label[i]<0:axes.append(np.array([0.,0.,1.]));continue
  child=next((q for q in range(nj) if joints[q][0]==i and label[q]==label[i]),None)
  direction=world[child][:3,3]-world[i][:3,3] if child is not None else world[i][:3,3]-world[j[0]][:3,3]
  axis=unit(np.cross(direction,normal))
  if np.dot(axis,unit(np.array(j[2:5])))<0:axis=-axis
  axes.append(unit(world[i][:3,:3].T@axis))
 pos,ix,rev=np.unique(v[:,:3],axis=0,return_index=True,return_inverse=True);dense=np.zeros((nv,nj))
 for k in range(4):np.add.at(dense,(np.arange(nv),ids[:,k]),weights[:,k])
 dw=dense[ix];tris=rev.reshape(-1,3);neighbors=[set() for _ in pos]
 for tri in tris:
  for a in tri:neighbors[a].update(int(c) for c in tri if c!=a)
 selected=[353,537,709,725] if side=='left' else [576,210,224]
 original_dw=dw.copy();corrections=[]
 for index in selected:
  finger=int(label[int(np.argmax(dw[index]))]);adj=sorted(neighbors[index])
  distance=np.linalg.norm(pos[adj]-pos[index],axis=1);factors=1/np.maximum(distance,.01);factors/=sum(factors)
  blend=np.sum(original_dw[adj]*factors[:,None],axis=0)
  blend[np.array(label)!=finger]=0;blend/=sum(blend)
  assert np.count_nonzero(blend)>0 and np.count_nonzero(blend)<=4
  dw[index]=blend
  corrections.append({'unique_vertex':index,'position':pos[index].tolist(),'finger':finger,'before':original_dw[index].tolist(),'after':blend.tolist()})
 (R/(side+'_corrections.json')).write_text(json.dumps(corrections,indent=2))
 p4=np.c_[pos,np.ones(len(pos))]
 def pose(grip,trigger):
  ww=[]
  for i,(j,m) in enumerate(zip(joints,local)):
   f=label[i];d=depth[i];loc=m
   if f>=0:
    key=f'{side}.{["thumb","index","middle","ring","pinky"][f]}.{min(d,3)}.'
    default=([10,28,24,12] if f==0 else [4,50,72,46])[min(d,3)]
    angle=np.clip(default+cal.get(key+'bend_delta_deg',0),-150,150)
    axis=axes[i]+np.array([cal.get(key+'axis_d'+a,0) for a in 'xyz'])
    loc=m@rotate(axis,-angle*(trigger if f==1 else grip))
   ww.append(loc if j[0]<0 else ww[j[0]]@loc)
  out=np.zeros_like(pos,dtype=float)
  for i in range(nj):out+=dw[:,i,None]*(p4@(ww[i]@inv[i]).T)[:,:3]
  return out
 rest=pose(0,0);assert np.max(abs(rest-pos))<.002
 posed=pose(1,0);both=pose(1,1)
 # Rank local deformation changes. These are review candidates, not automatic repairs.
 ranked=[]
 for i in range(len(pos)):
  fw=[sum(dw[i,j] for j in range(nj) if label[j]==f) for f in range(5)];f=int(np.argmax(fw))
  if f not in [2,3] or fw[f]<.65:continue
  adj=sorted(neighbors[i]);before=np.linalg.norm(pos[adj]-pos[i],axis=1);after=np.linalg.norm(posed[adj]-posed[i],axis=1)
  stretch=float(np.max(after/np.maximum(before,.01)))
  residual=float(np.linalg.norm((posed[i]-posed[adj].mean(axis=0))-(pos[i]-pos[adj].mean(axis=0))))
  ranked.append({'unique_vertex':i,'skin_corner':int(ix[i]),'finger':f,'max_edge_ratio':stretch,'neighborhood_deformation_mm':residual*10,'weights':{str(j):round(float(w),5) for j,w in enumerate(dw[i]) if w>.00001},'neighbors':adj})
 ranked.sort(key=lambda x:x['max_edge_ratio'],reverse=True)
 np.savez(R/f'{side}_poses.npz',rest=rest,grip=posed,both=both,tris=tris,weights=dw,labels=label)
 results.append({'side':side,'skin_sha256':hashlib.sha256(b).hexdigest(),'computed_axes':[a.tolist() for a in axes],'candidates':ranked})
 print(side,json.dumps(ranked[:8]),flush=True)
(R/'audit.json').write_text(json.dumps({'calibration_sha256':hashlib.sha256((G/'hpl3vr_hand_calibration.ini').read_bytes()).hexdigest(),'method':'Runtime hierarchy-derived axes, stored local bind matrices and current bend/axis calibration; free-space grip and trigger poses, no contact-limited articulation. Candidate ranking is not proof of incorrect weights.','hands':results},indent=2))
