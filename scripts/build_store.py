"""Build the exact-hash Epic/GOG port from the same source as Steam.

Generated source and DLL stay under build/store. Never patches a game EXE.
"""
from pathlib import Path
import argparse,json,re,struct,subprocess,sys,shutil,hashlib
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);args=p.parse_args()
B=R/'build/store';B.mkdir(parents=True,exist_ok=True)
profile=json.loads((R/'reference/store-profile.json').read_text())
mapping={int(k,16):int(v,16) for k,v in profile['addresses'].items()}
tokens=re.compile(r'''/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|0x[0-9a-fA-F]+''',re.S)
source=B/'source';shutil.copytree(R/'source',source,dirs_exist_ok=True)
changes=[]
for f in source.glob('*'):
    if f.suffix not in ('.c','.inc'):continue
    s=f.read_text()
    def literal(m):
        token=m.group()
        if not token.startswith('0x') or int(token,16) not in mapping:return token
        v=int(token,16);changes.append([f.name,s.count('\n',0,m.start())+1,hex(v),hex(mapping[v])]);return hex(mapping[v])
    s=tokens.sub(literal,s)
    def signature(m):
        vals=[int(x.strip(),0) for x in m.group()[1:-1].split(',') if x.strip()]
        if len(vals)<8 or any(x>255 for x in vals):return m.group()
        replacement=profile['signature_changes'].get(bytes(vals).hex())
        return '{'+','.join(hex(x) for x in bytes.fromhex(replacement))+'}' if replacement else m.group()
    s=re.sub(r'\{\s*(?:(?:0x[0-9a-fA-F]+|[0-9]+)\s*,\s*)*(?:0x[0-9a-fA-F]+|[0-9]+)\s*,?\s*\}',signature,s)
    f.write_text(s)
g=profile['guard']
guard='''static i32 s26ef_store_matches(void){
 const u8* b=(const u8*)ext_GetModuleHandleA(0);
 if(!b||*(const unsigned short*)b!=0x5a4d)return 0;
 u32 n=*(const u32*)(b+0x3c);if(n<0x40||n>0x1000)return 0;
 if(*(const u32*)(b+n)!=0x4550||*(const unsigned short*)(b+n+4)!=0x8664)return 0;
'''+f' if(*(const u32*)(b+n+8)!={g["timestamp"]}u||*(const u32*)(b+n+24+56)!={g["image_size"]}u)return 0;\n'
guard+=' static const struct{u32 rva;u8 byte;} checks[]={'+','.join('{'+hex(r)+'u,'+hex(v)+'}' for r,v in g['samples'])+'};\n'
guard+=' for(u32 i=0;i<sizeof(checks)/sizeof(checks[0]);++i)if(b[checks[i].rva]!=checks[i].byte)return 0;return 1;\n}\n'
f=source/'s26n.c';s=f.read_text();marker='u32 __attribute__((ms_abi)) s6_h5748n_load_thread_wrapper(void* param){'
assert s.count(marker)==1
s=s.replace(marker,guard+marker+'\n    if(!s26ef_store_matches())return 1;');f.write_text(s)
obj=B/'hpl3vr.obj';out=B/'hpl3vr-store.dll'
subprocess.run([args.zig,'cc','-target','x86_64-windows-gnu','-O2','-g0','-ffreestanding','-fno-asynchronous-unwind-tables','-fno-ident','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-parameter','-c',str(f),'-o',str(obj)],check=True)
base=R/'third_party/hpl3vr_S5-P2_base.dll'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='f17f2048c7625705e3867c7ca9e106c3c343053deefc716e67f210ca647f74ed'
subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/apply_payload.py'),str(base),str(obj),str(out)],check=True)
data=bytearray(out.read_bytes());nt=struct.unpack_from('<I',data,60)[0];table=nt+24+struct.unpack_from('<H',data,nt+20)[0]
def offset(rva):
    for i in range(struct.unpack_from('<H',data,nt+6)[0]):
        at=table+40*i;_,s,n,o=struct.unpack_from('<IIII',data,at+8)
        if s<=rva< s+n:return o+rva-s
    raise ValueError(hex(rva))
for patch in profile['base_operands']:
    at=offset(int(patch['operand_rva'],16));assert struct.unpack_from('<I',data,at)[0]==int(patch['old'],16)
    struct.pack_into('<I',data,at,int(patch['new'],16))
struct.pack_into('<I',data,nt+24+64,0);out.write_bytes(data)
result={'sha256':hashlib.sha256(data).hexdigest(),'executable_sha256':profile['sha256'],'literal_changes':changes,'status':'built-not-gameplay-validated'}
(B/'result.json').write_text(json.dumps(result,indent=2));print('Store DLL:',out,result['sha256'])
