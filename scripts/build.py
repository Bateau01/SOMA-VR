"""Build only into ./build; never writes to a SOMA installation."""
from pathlib import Path
import argparse,subprocess,sys,hashlib,os
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True,help='Path to zig.exe (validated with 0.13.0)');p.add_argument('--test',action='store_true');args=p.parse_args()
B=R/'build';B.mkdir(exist_ok=True)
base=R/'third_party/hpl3vr_S5-P2_base.dll'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='f17f2048c7625705e3867c7ca9e106c3c343053deefc716e67f210ca647f74ed','Unexpected base DLL'
env=os.environ.copy();env['PYTHONUTF8']='1'
subprocess.run([args.zig,'cc','-target','x86_64-windows-gnu','-O2','-g0','-ffreestanding','-fno-asynchronous-unwind-tables','-fno-ident','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-parameter','-c',str(R/'source/s26n.c'),'-o',str(B/'hpl3vr.obj')],check=True,env=env)
subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/apply_payload.py'),str(base),str(B/'hpl3vr.obj'),str(B/'hpl3vr.dll')],check=True,env=env)
print('Built:',B/'hpl3vr.dll');print('SHA256:',hashlib.sha256((B/'hpl3vr.dll').read_bytes()).hexdigest())
if args.test:subprocess.run([sys.executable,'-X','utf8',str(R/'tests/test_native_hand_scale.py'),args.zig],check=True,env=env)
