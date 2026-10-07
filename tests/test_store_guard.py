"""Execute the generated store DLL's pre-hook guard against mapped EXE fixtures."""
from pathlib import Path
import json,subprocess,struct,ctypes,argparse
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--steam',required=True);p.add_argument('--store',required=True);a=p.parse_args()
B=R/'build/store';s=(B/'source/s26n.c').read_text();start=s.index('static i32 s26ef_store_matches');end=s.index('\nu32 __attribute__((ms_abi)) s6_h5748n_load_thread_wrapper',start)
c='typedef unsigned char u8;typedef unsigned int u32;typedef int i32;static void* image;static void* ext_GetModuleHandleA(int x){return image;}\n'+s[start:end]+'\n__declspec(dllexport) int check(void* p){image=p;return s26ef_store_matches();}\n'
f=B/'guard_test.c';f.write_text(c);dll=B/'guard_test.dll'
subprocess.run([a.zig,'cc','-shared','-O2',str(f),'-o',str(dll)],check=True)
check=ctypes.CDLL(str(dll)).check;check.argtypes=[ctypes.c_void_p];check.restype=ctypes.c_int
def image(path):
    raw=Path(path).read_bytes();nt=struct.unpack_from('<I',raw,60)[0];size=struct.unpack_from('<I',raw,nt+24+56)[0];out=ctypes.create_string_buffer(size)
    ctypes.memmove(out,raw,struct.unpack_from('<I',raw,nt+24+60)[0]);table=nt+24+struct.unpack_from('<H',raw,nt+20)[0]
    for k in range(struct.unpack_from('<H',raw,nt+6)[0]):
        _,rva,n,off=struct.unpack_from('<IIII',raw,table+40*k+8);ctypes.memmove(ctypes.addressof(out)+rva,raw[off:off+n],n)
    return out
store=image(a.store);steam=image(a.steam);assert check(store)==1 and check(steam)==0 and check(None)==0
n=3
for at,v in json.loads((R/'reference/store-profile.json').read_text())['guard']['samples']:
    old=store[at];store[at]=bytes([v^1]);assert check(store)==0,(at,v);store[at]=old;n+=1
assert check(store)==1
(B/'guard_results.json').write_text(json.dumps({'checks':n,'passed':True,'scope':'Exact mapped EXE guard, wrong-edition and individual guarded-byte mutations. No game launched.'},indent=2))
print('PASS',n,'store guard checks')
