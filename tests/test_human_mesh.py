from pathlib import Path
import numpy as np,struct,json,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];N={'c':'http://www.collada.org/2005/11/COLLADASchema'};checks=0
for side in ['left','right']:
 b=(R/'runtime'/f'hand_{side}.skin').read_bytes();_,nv,nj,*pivot=struct.unpack_from('<3I3f',b)
 v=np.frombuffer(b,offset=24,count=nv*16,dtype='<f4').reshape(-1,16);ids=v[:,8:12].copy().view('<i4');dense=np.zeros((nv,nj))
 for k in range(4):np.add.at(dense,(np.arange(nv),ids[:,k]),v[:,12+k])
 assert np.isfinite(dense).all() and np.min(dense)>=0 and np.max(abs(dense.sum(1)-1))<1e-5
 root=E.parse(R/'runtime/entities/soma_vr/s26f'/f'hand_human_{side}.dae').getroot()
 pos=np.array(root.find('.//c:source[@id="Handpositions"]/c:float_array',N).text.split(),float).reshape(-1,3);ww=np.array(root.find('.//c:source[@id="Handweights"]/c:float_array',N).text.split(),float);pairs=np.array(root.find('.//c:vertex_weights/c:v',N).text.split(),int).reshape(-1,4,2);nd=np.zeros((len(pos),nj))
 for k in range(4):np.add.at(nd,(np.arange(len(pos)),pairs[:,k,0]),ww[pairs[:,k,1]])
 for i,p in enumerate(pos):
  hits=np.flatnonzero(np.linalg.norm((v[:,:3]-pivot)*.01-p,axis=1)<1e-7)
  if len(hits):assert np.min(np.max(abs(dense[hits]-nd[i]),axis=1))<1e-5;checks+=1
 if side=='left':
  target=np.unique(v[:,:3],axis=0)[362];hits=np.flatnonzero(np.linalg.norm(v[:,:3]-target,axis=1)<1e-5)
  assert len(hits)==6 and np.max(dense[hits,22:26])==0
  assert np.max(abs(dense[hits,18:22].sum(1)-1))<1e-6
print('PASS',checks,'native/fallback human vertex weight equivalence checks; repaired side vertex has only middle-finger influences')
