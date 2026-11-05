from pathlib import Path
from PIL import Image,ImageDraw
import sys
p=Path(sys.argv[1])
for phase in (6,7,8):
 sheet=Image.new('RGB',(1024,900),(25,25,25));d=ImageDraw.Draw(sheet)
 for k in range(24):
  x=(k%4)*256;y=(k//4)*150;d.text((x+3,y+2),f'phase {phase} sample {k} L / R',fill='white')
  for eye in range(2):
   f=p/f'iu_eye_trace_{phase}_{k:02}_{eye}.rgba'
   if not f.exists():continue
   im=Image.frombytes('RGBA',(256,256),f.read_bytes()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB').resize((128,128));sheet.paste(im,(x+eye*128,y+20))
 sheet.save(p/f'cpu24-motion-{phase}.png')
