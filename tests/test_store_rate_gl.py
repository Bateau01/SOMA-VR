"""Run the timer and menu contracts against generated Epic/GOG production code."""
from pathlib import Path
import re,json,sys
R=Path(__file__).resolve().parents[1]
profile=json.loads((R/'reference/store-profile.json').read_text())
mapping={int(k,16):int(v,16) for k,v in profile['addresses'].items()}
def sig(m):
 vals=[int(x.strip(),0) for x in m.group()[1:-1].split(',') if x.strip()]
 if len(vals)<8 or any(x>255 for x in vals):return m.group()
 replacement=profile['signature_changes'].get(bytes(vals).hex())
 return '{'+','.join(hex(x) for x in bytes.fromhex(replacement))+'}' if replacement else m.group()
for name in ['test_simulation_rate.py','test_simulation_menu.py']:
 p=R/'tests'/name;s=p.read_text()
 s=s.replace("R/'source/","R/'build/store/source/").replace("R/'audit/","R/'audit/store-")
 s=re.sub(r'0x[0-9a-fA-F]+',lambda m:hex(mapping.get(int(m.group(),16),int(m.group(),16))),s)
 s=re.sub(r'\{\s*(?:(?:0x[0-9a-fA-F]+|[0-9]+)\s*,\s*)*(?:0x[0-9a-fA-F]+|[0-9]+)\s*,?\s*\}',sig,s)
 if name=='test_simulation_rate.py':
  old='memcpy(exe+0x57416f,ss,7);';assert old in s
  s=s.replace(old,old+'*(i32*)(exe+0x574172)=0x65c620-0x574176;')
 print('Generated Epic/GOG:',name,flush=True)
 exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
