"""Private input-queue fixture build; never use for packaging."""
import argparse,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);p.add_argument('--icon-capture',action='store_true');a=p.parse_args()
opts=json.loads((root/'scripts/cpu-runtime-options.json').read_text());opts.pop('production',None)
cmd=[sys.executable,str(root/'scripts/build_smaa_test_iu.py'),'--zig',a.zig]
if a.icon_capture:cmd.append('--icon-capture')
for k,v in opts.items():
 if isinstance(v,bool):
  if v:cmd.append('--'+k.replace('_','-'))
 elif v is not None:cmd.extend(['--'+k.replace('_','-'),str(v)])
subprocess.run(cmd,cwd=root,check=True)
