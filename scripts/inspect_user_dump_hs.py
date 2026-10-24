from pathlib import Path
import struct,json
p=Path(r'C:/Users/BateauPC/AppData/Local/CrashDumps/Soma.exe.42088.dmp');b=p.read_bytes();n,d=struct.unpack_from('<II',b,8);streams={}
for i in range(n):t,sz,o=struct.unpack_from('<III',b,d+12*i);streams[t]=(o,sz)
mods=[]
if 4 in streams:
 o,_=streams[4];n=struct.unpack_from('<I',b,o)[0]
 for i in range(n):
  q=o+4+108*i;base,size=struct.unpack_from('<QI',b,q);name=struct.unpack_from('<I',b,q+20)[0];ln=struct.unpack_from('<I',b,name)[0];name=b[name+4:name+4+ln].decode('utf-16le');mods.append((base,size,name))
  if any(x in name.lower() for x in ['newton','hpl3vr','soma.exe']):print(hex(base),hex(size),name)
ranges=[]
if 5 in streams:
 o,_=streams[5];n=struct.unpack_from('<I',b,o)[0]
 for i in range(n):addr,size,off=struct.unpack_from('<QII',b,o+4+16*i);ranges.append((addr,size,off))
if 9 in streams:
 o,_=streams[9];n,off=struct.unpack_from('<QQ',b,o)
 for i in range(n):addr,size=struct.unpack_from('<QQ',b,o+16+16*i);ranges.append((addr,size,off));off+=size
print('ranges',len(ranges))
def read(addr,n):
 for a,s,o in ranges:
  if a<=addr and addr+n<=a+s:return b[o+addr-a:o+addr-a+n]
 return b''
base=next(a for a,s,n in mods if n.lower().endswith('hpl3vr.dll'))
print('getmatrix ptr',read(base+0x1dd538,8).hex())
o,_=streams[6];code=struct.unpack_from('<I',b,o+8)[0];addr=struct.unpack_from('<Q',b,o+24)[0];print('exception',hex(code),hex(addr),[(hex(a),name) for a,s,name in mods if a<=addr<a+s]);print('exception params',b[o+32:o+152].hex(' '))
Path('docs/v109-evidence/user-20261022/dump_streams.json').write_text(json.dumps({'modules':mods,'ranges':ranges,'exception':hex(addr),'code':hex(code)},indent=2))
