from pathlib import Path
import re,xml.etree.ElementTree as E,json
import numpy as np
R=Path(__file__).resolve().parents[1];G=Path('D:/SteamLibrary/steamapps/common/SOMA')
def rotation(s):
 x,y,z=map(float,s.split());cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def vec(p):return 'cVector3f('+','.join(f'{x:.6f}f' for x in p)+')'
inventory=[]
for file in sorted((G/'maps').glob('chapter*/*/*.hpm_Area')):
 areas={a.get('Name'):a for a in E.parse(file).iter('Area')};points=[]
 for name,a in areas.items():
  if a.get('AreaType')!='Climb':continue
  vs={v.get('Name'):v.get('Value') for v in a.findall('./UserVariables/Var')}
  feet=areas.get(vs.get('FeetPosition'));assert feet is not None
  pos=np.fromstring(a.get('WorldPos'),sep=' ');fp=np.fromstring(feet.get('WorldPos'),sep=' ')
  rot=rotation(a.get('Rotation'));scale=np.fromstring(a.get('Scale'),sep=' ')
  local=np.array([.20,(rot.T@(fp-pos))[1],scale[2]*.5])
  points.append((name,local,np.array([0,0,-1]),np.array([0,1,0])))
  inventory.append({'map':file.stem,'target':name,'kind':'native Climb','local_contact':local.tolist(),'feet':vs['FeetPosition'],'status':'candidate; surface alignment requires rendered inspection'})
 if not points:continue
 p=R/'runtime'/file.relative_to(G);p=p.with_suffix('.hps')
 text=p.read_text(encoding='utf-8-sig') if p.exists() else file.with_suffix('.hps').read_text(encoding='utf-8-sig')
 text='#include "helpers/helper_vr_traversal_hy.hps"\n'+text
 idx=text.index('{',text.index('class cScrMap'))+1
 text=text[:idx]+'\n    [nosave] cVRTraversalGuidesHY mVRTraversalHY;\n'+text[idx:]
 init='\n        mVRTraversalHY.Dispose();\n'+''.join('        mVRTraversalHY.Add("'+n+'",'+vec(at)+','+vec(f)+','+vec(norm)+');\n' for n,at,f,norm in points)
 m=re.search(r'void OnEnter\(\)\s*\{',text);assert m;text=text[:m.end()]+init+text[m.end():]
 m=re.search(r'void OnLeave\(\)\s*\{',text)
 if m:text=text[:m.end()]+'\n        mVRTraversalHY.Dispose();'+text[m.end():]
 else:
  idx=text.index('{',text.index('class cScrMap'))+1;text=text[:idx]+'\n void OnLeave(){mVRTraversalHY.Dispose();}\n'+text[idx:]
 # Ignore commented-out declarations when locating the real callback.
 clean=re.sub(r'/\*.*?\*/',lambda m:' '*len(m[0]),text,flags=re.S)
 m=re.search(r'void Update\(float (\w+)\)\s*\{',clean)
 if m:text=text[:m.end()]+'\n        mVRTraversalHY.Update('+m[1]+');'+text[m.end():]
 else:
  idx=text.index('{',text.index('class cScrMap'))+1;text=text[:idx]+'\n void Update(float dt){mVRTraversalHY.Update(dt);}\n'+text[idx:]
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
(R/'docs/v109-evidence/climb_candidates_hy.json').write_text(json.dumps(inventory,indent=2))
print('Prepared',len(inventory),'climb/vent candidates; not visually validated')
