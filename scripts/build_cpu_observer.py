import json,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'scripts/cpu-runtime-options.json').read_text());a['production']=False;a['cpu_work_profile']=True;a['cpu_near_types']=True
cmd=[sys.executable,str(r/'scripts/build_smaa_test_iu.py'),'--zig',str(r.parent/'SOMA_VR_SCALE_INVESTIGATION/tools/ziglang/zig.exe')]
for k,v in a.items():
 if v is True:cmd.append('--'+k.replace('_','-'))
 elif v is not False and v is not None:cmd += ['--'+k.replace('_','-'),str(v)]
subprocess.run(cmd,cwd=r,check=True)
