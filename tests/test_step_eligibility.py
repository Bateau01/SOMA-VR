"""Execute the patched x64 comparison, not a Python reimplementation of it."""
from pathlib import Path
import ctypes as c, subprocess,sys,json
R=Path(__file__).resolve().parents[1];A=R/'audit/step-machine';A.mkdir(parents=True,exist_ok=True)
head='''#include <windows.h>
typedef unsigned char u8;typedef unsigned u32;typedef unsigned long long u64;typedef long long i64;typedef int i32;
static void* ext_GetModuleHandleA(const char*n){return GetModuleHandleA(n);}
static void* ext_GetProcAddress(void*m,const char*n){return (void*)GetProcAddress(m,n);}
static void ext_Log(const char*s,...){}
'''
code=(R/'source/simulation_rate_gd.inc').read_text().split('/* The step routine')[0]
tail='''__declspec(dllexport) int prepare(void*p){return s26gh_prepare_step_threshold(p);}
__declspec(dllexport) void activate(void){*g_s26ghStepThreshold=0.000025f;}
'''
src=A/'step.c';src.write_text(head+code+tail);dll=A/'step.dll'
subprocess.run([sys.argv[1],'cc','-shared','-O2',str(src),'-o',str(dll)],check=True)
k=c.WinDLL('kernel32');k.VirtualAlloc.argtypes=[c.c_void_p,c.c_size_t,c.c_ulong,c.c_ulong];k.VirtualAlloc.restype=c.c_void_p
k.VirtualFree.argtypes=[c.c_void_p,c.c_size_t,c.c_ulong]
b=k.VirtualAlloc(None,0x700000,0x3000,0x40);assert b
try:
 ins=b+0x57c8ff;c.memmove(ins-4,bytes.fromhex('f30f1011'),4)
 c.memmove(ins,bytes.fromhex('0f2f153a211100'),7);c.memmove(ins+7,bytes.fromhex('0f93c00fb6c0c3'),7)
 c.memmove(b+0x57c959,bytes.fromhex('83e804'),3);c.c_float.from_address(b+0x68ea40).value=.0001
 test=c.WINFUNCTYPE(c.c_int,c.POINTER(c.c_float))(ins-4)
 def passes(speed,hz):return bool(test(c.byref(c.c_float((speed/hz)**2))))
 assert passes(1.03125,60) and not passes(1.03125,120)
 lib=c.WinDLL(str(dll));lib.prepare.argtypes=[c.c_void_p];lib.prepare.restype=c.c_int
 assert not lib.prepare(b+8);assert lib.prepare(b);assert not lib.prepare(b)
 speeds=[.1,.59,.61,1.03125,2.5,5.25]
 before=[passes(v,60) for v in speeds];assert before==[v>.6 for v in speeds]
 lib.activate();after=[passes(v,120) for v in speeds];assert before==after
 assert c.c_float.from_address(b+0x68ea40).value==c.c_float(.0001).value
 result={'pass':True,'speeds':speeds,'eligibility60':before,'eligibility120':after,'shared_constant_unchanged':True,'scope':'production patch + executed x64 comparison; native obstacle test is separate'}
 (A/'result.json').write_text(json.dumps(result,indent=2));print('PASS: executed native comparison; original failure, signature guards, unchanged 60 Hz and matched 120 Hz eligibility')
finally:k.VirtualFree(b,0,0x8000)
