"""Read-only PE/RTTI evidence for the known Steam character-body layout."""
from pathlib import Path
import struct, hashlib, json
R=Path(__file__).resolve().parents[1]
p=Path(r'D:\SteamLibrary\steamapps\common\SOMA\Soma.exe');b=p.read_bytes()
assert hashlib.sha256(b).hexdigest()=='7c424e6055dda5b3aa41d4b3a9d6ffdebb8f4b50fa8a38769dee82d080b79113'
pe=struct.unpack_from('<I',b,0x3c)[0];n=struct.unpack_from('<H',b,pe+6)[0]
opt=pe+24;size=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<Q',b,opt+24)[0]
sections=[]
for i in range(n):
 o=opt+size+i*40;vs,va,rs,raw=struct.unpack_from('<IIII',b,o+8)
 sections.append((va,rs,raw))
def rva(off):
 for va,rs,raw in sections:
  if raw<=off<raw+rs:return va+off-raw
 raise ValueError(off)
def off(va):
 for start,rs,raw in sections:
  if start<=va<start+rs:return raw+va-start
 raise ValueError(va)
name=b'.?AVcCharacterBodyNewton@hpl@@\0';td=rva(b.index(name)-16)
cols=[]
for va,rs,raw in sections:
 for o in range(raw,raw+rs-24,4):
  sig,offset,cd,typ,hierarchy,selfrva=struct.unpack_from('<IIIIII',b,o)
  if sig==1 and typ==td and selfrva==rva(o):cols.append((rva(o),offset))
tables=[]
for col,offset in cols:
 needle=struct.pack('<Q',base+col);pos=0
 while (pos:=b.find(needle,pos))!=-1:
  vr=rva(pos)+8
  entries=struct.unpack_from('<'+'Q'*12,b,off(vr))
  tables.append({'vtable':hex(base+vr),'subobject_offset':offset,'methods':[hex(x) for x in entries]});pos+=8
result={'executable_sha256':hashlib.sha256(b).hexdigest(),'type_descriptor':hex(base+td),'tables':tables,'scope':'Static PE RTTI only; no runtime validation or store mapping inferred.'}
(R/'docs/v109-evidence/character_rtti.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
