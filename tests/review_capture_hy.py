from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,sys,json
R=Path(__file__).resolve().parents[1]/'docs/v109-evidence'
folders=[Path(x) for x in sys.argv[1:]]
for folder in folders:
 best=None;score=-1
 for p in folder.glob('*.ppm'):
  im=Image.open(p);a=np.asarray(im).astype('int16');s=((a[:,:,1]>a[:,:,0]*1.3+30)&(a[:,:,2]>a[:,:,0]*1.3+30)&(a[:,:,1]>100)).sum()
  if s>score:best=im.copy();score=s
 if best is not None:best.save(folder/'guide.png');print(str(folder/'guide.png'),int(score))
