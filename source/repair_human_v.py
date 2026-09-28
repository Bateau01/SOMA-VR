"""Export reviewed same-finger knuckle blends into staged assets only."""
from pathlib import Path
import json,struct,hashlib,shutil,subprocess,time
import xml.etree.ElementTree as E
import numpy as np
R=Path(__file__).resolve().parents[1]; W=R.parent; C=W/'SOMA_VR_HUMAN_CURL_CANDIDATE'
N={'c':'http://www.collada.org/2005/11/COLLADASchema'}; E.register_namespace('',N['c'])
reports=[]
for side in ['left','right']:
 rel=Path(f'entities/soma_vr/s26f/hand_human_{side}.dae')
 src=R/'rollback'/rel; tree=E.parse(src); root=tree.getroot()
 pos=np.array(root.find('.//c:source[@id="Handpositions"]/c:float_array',N).text.split(),float).reshape(-1,3)
 wn=root.find('.//c:source[@id="Handweights"]/c:float_array',N); weights=np.array(wn.text.split(),float)
 vn=root.find('.//c:controller[@id="HandSkin"]/c:skin/c:vertex_weights/c:v',N); pairs=np.array(vn.text.split(),int).reshape(-1,2)
 raw=(R/'rollback'/f'hand_{side}.skin').read_bytes(); b=bytearray(raw); _,nv,nj,*pivot=struct.unpack_from('<3I3f',b)
 allowed=set()
 for correction in json.loads((C/f'{side}_corrections.json').read_text()):
  target=np.array(correction['position']); dense=np.array(correction['after']); ids=np.flatnonzero(dense>0).tolist(); ws=dense[ids].tolist()
  while len(ids)<4:ids.append(0);ws.append(0.)
  assert len(ids)==4 and abs(sum(ws)-1)<1e-7
  hits=[]
  for i in range(nv):
   o=24+i*64
   if np.linalg.norm(np.array(struct.unpack_from('<3f',b,o))-target)>1e-5:continue
   old=np.zeros(nj)
   for j,w in zip(struct.unpack_from('<4i',b,o+32),struct.unpack_from('<4f',b,o+48)):old[j]+=w
   assert np.allclose(old,correction['before'],atol=1e-6)
   struct.pack_into('<4i4f',b,o+32,*ids,*ws);allowed.update(range(o+32,o+64));hits.append(i)
  dh=np.flatnonzero(np.linalg.norm(pos-(target-np.array(pivot))*.01,axis=1)<1e-7)
  assert len(dh)==len(hits)>0
  for i in dh:
   old=np.zeros(nj)
   for j,k in pairs[i*4:i*4+4]:old[j]+=weights[k]
   assert np.allclose(old,correction['before'],atol=1e-6)
   for n,(j,w) in enumerate(zip(ids,ws)):
    k=pairs[i*4+n,1];assert np.count_nonzero(pairs[:,1]==k)==1
    pairs[i*4+n,0]=j;weights[k]=w
  reports.append({**correction,'side':side,'skin_corners':hits,'native_corners':dh.tolist()})
 assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(raw,b)))
 wn.text=' '.join(format(x,'.9g') for x in weights);vn.text=' '.join(str(x) for x in pairs.flatten())
 tree.write(R/'runtime'/rel,encoding='utf-8',xml_declaration=True)
 check=E.parse(R/'runtime'/rel);original=E.parse(src)
 for query in ['.//c:source[@id="Handweights"]/c:float_array','.//c:controller[@id="HandSkin"]/c:skin/c:vertex_weights/c:v']:
  check.find(query,N).text=original.find(query,N).text
 assert E.tostring(check.getroot())==E.tostring(original.getroot())
 (R/'runtime'/f'hand_{side}.skin').write_bytes(b)
 # Use the previously established private native importer, outside the game.
 conv=W/'SOMA_VR_S26T_HAND_FIX/build/converter'; out=conv/rel;shutil.copy2(R/'runtime'/rel,out)
 cache=out.with_suffix('.msh');assert cache.resolve().is_relative_to(conv.resolve())
 if cache.exists():cache.unlink()
 si=subprocess.STARTUPINFO();si.dwFlags=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 proc=subprocess.Popen([str(conv/'ModelViewer.exe'),str(out)],cwd=conv,startupinfo=si)
 try:
  for _ in range(150):
   time.sleep(.2)
   if cache.exists() and cache.stat().st_size>1000:time.sleep(2);break
   if proc.poll() is not None:raise RuntimeError('Native importer exited')
  else:raise RuntimeError('Native importer timed out')
 finally:
  if proc.poll() is None:proc.terminate()
  proc.wait(timeout=10)
 log=(conv/'HPL3/modelview.log').read_text(errors='replace');assert 'not connected to a bone' not in log and "Couldn't create material" not in log
 (R/'audit'/f'hand_native_import_v_{side}.txt').write_text(log)
 shutil.copy2(cache,R/'runtime'/rel.with_suffix('.msh'))
 print(side,'staged human hand import PASS',flush=True)
(R/'audit/hand_repairs_v.json').write_text(json.dumps({'repairs':reports,'geometry_materials_bind_matrices_unchanged':True,'native_import':'PASS','headset_test':'NOT RUN'},indent=2))
