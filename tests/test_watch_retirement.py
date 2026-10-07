"""Require that EK differs from EJ only at the four retired watch paths and PE checksum."""
from pathlib import Path
import sys,struct,json
R=Path(__file__).resolve().parents[1];old=Path(sys.argv[1]);results=[]
def offset(d,rva):
 nt=struct.unpack_from('<I',d,60)[0];table=nt+24+struct.unpack_from('<H',d,nt+20)[0]
 for i in range(struct.unpack_from('<H',d,nt+6)[0]):
  _,s,n,o=struct.unpack_from('<IIII',d,table+40*i+8)
  if s<=rva<s+n:return o+rva-s
 raise AssertionError(hex(rva))
for name in ['hpl3vr.dll','store/hpl3vr-store.dll']:
 a=(old/'build'/name).read_bytes();b=(R/'build'/name).read_bytes();assert len(a)==len(b)
 nt=struct.unpack_from('<I',a,60)[0];allowed=set(range(nt+24+64,nt+24+68))
 for rva,expected in [(0x1990,bytes.fromhex('31c0c390')),(0xa386,b'\x90\x90'),(0xb6f8,b'\xe9'+struct.pack('<i',0xb722-0xb6fd)+b'\x90\x90'),(0xbed0,b'\xe9'+struct.pack('<i',0xb063-0xbed5)+b'\x90\x90')]:
  at=offset(b,rva);assert b[at:at+len(expected)]==expected;allowed.update(range(at,at+len(expected)))
 changes={i for i in range(len(a)) if a[i]!=b[i]};assert changes<=allowed,sorted(changes-allowed)
 results.append(dict(binary=name,changed_bytes=len(changes),only_watch_paths_and_checksum=True,all_resolution_render_input_payload_bytes_unchanged=True))
(R/'build/watch_retirement_results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
