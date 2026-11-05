"""Create both-eye animation samples for manual inspection, not a visual pass oracle."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw

p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
cases=json.loads((a.capture/'animation-cases.json').read_text())['cases']
for i,case in enumerate(cases):
    sheet=Image.new('RGB',(1536,560));draw=ImageDraw.Draw(sheet)
    draw.text((4,2),case['entity'],fill='white')
    for row,phase in enumerate((i*2,i*2+1)):
        for col,(sample,eye) in enumerate((s,e) for s in (0,12,23) for e in (0,1)):
            f=a.capture/f'iu_eye_trace_{phase}_{sample:02}_{eye}.rgba'
            draw.text((col*256,row*276+20),f'phase {phase} sample {sample} eye {eye}',fill='white')
            if f.exists():
                raw=f.read_bytes();assert len(raw)==256*256*4
                im=Image.frombytes('RGBA',(256,256),raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                sheet.paste(im.convert('RGB'),(col*256,row*276+36))
    sheet.save(a.capture/f'animation-case-{i}.png')
