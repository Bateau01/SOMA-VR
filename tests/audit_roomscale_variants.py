from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'build/audit-deps'))
import pefile,capstone
paths={'steam':Path('D:/SteamLibrary/steamapps/common/SOMA/Soma.exe'),'epic':Path('C:/Program Files/Epic Games/SOMA/Soma.exe'),'gog':Path('C:/Program Files/GOG Galaxy/Games/SOMA/Soma.exe')}
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
def load(p):
 pe=pefile.PE(str(p));return pe,pe.get_memory_mapped_image()
def function(pe,data,rva):
 if rva in (0x260ab0,0x25a250):
  return list(md.disasm(data[rva:rva+0x4b1],rva))
 f=next(x.struct for x in pe.DIRECTORY_ENTRY_EXCEPTION if x.struct.BeginAddress==rva)
 return list(md.disasm(data[rva:f.EndAddress],rva))
def norm(ins):
 start=ins[0].address;end=ins[-1].address+ins[-1].size;out=[]
 for i in ins:
  b=bytearray(i.bytes)
  if i.disp_size and any(o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP for o in i.operands):b[i.disp_offset:i.disp_offset+i.disp_size]=b'\0'*i.disp_size
  if i.mnemonic in ('call','jmp') and i.operands[0].type==capstone.x86.X86_OP_IMM and not start<=i.operands[0].imm<end:b[i.imm_offset:i.imm_offset+i.imm_size]=b'\0'*i.imm_size
  out.append(b.hex())
 return out
loaded={k:load(p) for k,p in paths.items()};result={'identities':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},'functions':{}}
assert result['identities']['epic']==result['identities']['gog']=='395cd54830c8e66e22166e71ac6fe95fd3bb5433b898737836744a6d178a0a6a'
for name,rva in [('fit',0x23f1d0),('filter',0x260ab0)]:
 a=function(*loaded['steam'],rva);signature=norm(a);matches=[]
 pe,data=loaded['epic']
 for x in pe.DIRECTORY_ENTRY_EXCEPTION:
  f=x.struct
  if name=='filter':
   if f.BeginAddress!=0x25a250:continue
  elif f.EndAddress-f.BeginAddress!=a[-1].address+a[-1].size-rva:continue
  ins=function(pe,data,f.BeginAddress)
  if norm(ins)==signature:matches.append(f.BeginAddress)
 assert len(matches)==1,(name,matches)
 store=matches[0];result['functions'][name]={'steam':hex(rva),'epic':hex(store),'gog':hex(store),'normalized_instructions_equal':True,'instructions':len(a)}
 for version,addr in [('steam',rva),('epic',store),('gog',store)]:
  ins=function(*loaded[version],addr)
  (R/f'audit/roomscale-sweep/{version}_{name}.asm').write_text('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins))
(R/'audit/roomscale-sweep/variants.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
