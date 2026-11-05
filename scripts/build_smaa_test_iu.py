"""Build only into ./build; never writes to a SOMA installation."""
from pathlib import Path
import argparse,subprocess,sys,hashlib,os,json
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--test',action='store_true');p.add_argument('--production',action='store_true');p.add_argument('--icon-capture',action='store_true')
for name in ('cpu-gui-prewarm','cpu-texture-release','cpu-render-jobs','cpu-work-profile','cpu-string-spans','cpu-near-types','cpu-texture-storage','cpu-texture-latc','cpu-string-oracle','cpu-streaming-optimisations','cpu-hand-mesh','cpu-leaf-filter','cpu-held-query'):p.add_argument('--'+name,action='store_true')
p.add_argument('--cpu-texture-min-bytes',type=int,choices=(0,65536,2097152),default=2097152)
args=p.parse_args()
subprocess.run([sys.executable,str(R/'scripts/build_logging_ji.py'),'--zig',args.zig],check=True)
if args.production and args.icon_capture:p.error('icon capture is private-only')
if args.cpu_leaf_filter and not args.cpu_hand_mesh:p.error('leaf filter requires verified native job ownership')
if args.production and (args.cpu_work_profile or args.cpu_string_oracle):p.error('observation is isolated-only')
B=R/('build/native-runtime' if args.production else 'build/smaa-test');B.mkdir(parents=True,exist_ok=True)
receipt=B/'build-receipt.json';receipt.unlink(missing_ok=True)
base=R/'third_party/hpl3vr_S5-P2_base.dll'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='f17f2048c7625705e3867c7ca9e106c3c343053deefc716e67f210ca647f74ed','Unexpected base DLL'
env=os.environ.copy();env['PYTHONUTF8']='1'
subprocess.run([args.zig,'cc',f'-DCPU_HELD_QUERY={int(args.cpu_held_query)}',f'-DCPU_LEAF_FILTER={int(args.cpu_leaf_filter)}',f'-DCPU_HAND_MESH={int(args.cpu_hand_mesh)}',f'-DCPU_STREAMING_OPTIMISATIONS={int(args.cpu_streaming_optimisations)}','-target','x86_64-windows-gnu',f'-DCPU_GUI_PREWARM={int(args.cpu_gui_prewarm)}',f'-DCPU_TEXTURE_RELEASE={int(args.cpu_texture_release)}',f'-DCPU_TEXTURE_MIN_BYTES={args.cpu_texture_min_bytes}',f'-DCPU_RENDER_JOBS={int(args.cpu_render_jobs)}',f'-DCPU_WORK_PROFILE={int(args.cpu_work_profile)}',f'-DCPU_STRING_SPANS={int(args.cpu_string_spans)}',f'-DCPU_NEAR_TYPES={int(args.cpu_near_types)}',f'-DCPU_TEXTURE_STORAGE={int(args.cpu_texture_storage)}',f'-DCPU_TEXTURE_LATC={int(args.cpu_texture_latc)}',f'-DCPU_STRING_ORACLE={int(args.cpu_string_oracle)}',* ([] if args.production else ['-DS26IU_TEST=1',*(['-DNI_ICON_CAPTURE=1'] if args.icon_capture else [])]),'-O2','-g0','-ffreestanding','-fno-asynchronous-unwind-tables','-fno-ident','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-parameter','-c',str(R/'source/s26n.c'),'-o',str(B/'hpl3vr.obj')],check=True,env=env)
subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/apply_payload.py'),str(base),str(B/'hpl3vr.obj'),str(B/'hpl3vr.dll')],check=True,env=env)
receipt.write_text(json.dumps({'dll_sha256':hashlib.sha256((B/'hpl3vr.dll').read_bytes()).hexdigest(),'arguments':vars(args),'source_hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted([p for p in (R/'source').rglob('*') if p.is_file()]+[R/'tests/smaa_observer_iu.inc',R/'scripts/build_smaa_test_iu.py'])}},indent=2))
print('Built:',B/'hpl3vr.dll');print('SHA256:',hashlib.sha256((B/'hpl3vr.dll').read_bytes()).hexdigest())
if args.test:subprocess.run([sys.executable,'-X','utf8',str(R/'tests/test_native_hand_scale.py'),args.zig],check=True,env=env)
