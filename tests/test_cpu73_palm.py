"""Real shipped vertices, synthetic bone/classification/transform inputs; not a game test."""
from pathlib import Path
import subprocess,json
r=Path(__file__).resolve().parents[1];b=r/'build/cpu73';b.mkdir(exist_ok=True)
import re
def function(text,name):
 a=text.index('static i32 '+name+'('); start=text.index('{',a);depth=0
 for i in range(start,len(text)):
  if text[i]=='{':depth+=1
  elif text[i]=='}':
   depth-=1
   if depth==0:return text[a:i+1]
 raise AssertionError('Unclosed function')
actual=function((r/'source/s26n.c').read_text(encoding='utf-8'),'h504_fit_palm_boxes').replace('h504_fit_palm_boxes','candidate',1)
expected=function((r/'tests/cpu73_palm_equivalence.c').read_text(encoding='utf-8'),'candidate')
assert re.sub(r'\s+','',actual)==re.sub(r'\s+','',expected),'Standalone candidate diverged from production helper'
zig=r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe'
subprocess.run([str(zig),'cc','-O2',str(r/'tests/cpu73_palm_equivalence.c'),'-o',str(b/'palm_equivalence.exe')],check=True)
p=subprocess.run([str(b/'palm_equivalence.exe'),*[str(p) for p in sorted((r/'runtime').rglob('*.skin'))]],capture_output=True,text=True,check=True)
(b/'palm-equivalence.txt').write_text(p.stdout,encoding='utf-8');print(p.stdout)
