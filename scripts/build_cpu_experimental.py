"""Build the native-only CPU experiment."""
import argparse,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);a=p.parse_args()
options=json.loads((root/'scripts/cpu-runtime-options.json').read_text())
assert options['production'] and options['cpu_string_spans']
assert not options.get('cpu_work_profile') and not options.get('cpu_string_oracle')
cmd=[sys.executable,str(root/'scripts/build_smaa_test_iu.py'),'--zig',a.zig]
for key,value in options.items():
    if isinstance(value,bool):
        if value:cmd.append('--'+key.replace('_','-'))
    elif value is not None:cmd.extend(['--'+key.replace('_','-'),str(value)])
subprocess.run(cmd,cwd=root,check=True)
