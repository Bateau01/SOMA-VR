"""Build the shared bounded writer, with no game/engine dependencies."""
from pathlib import Path
import argparse,subprocess,hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--zig',required=True);a=p.parse_args()
source=r/'source/logging_ji.c';out=r/'build/logging-support';out.mkdir(parents=True,exist_ok=True);dll=out/'SOMA-VR-Logging.dll'
subprocess.run([a.zig,'cc','-target','x86_64-windows-gnu','-O2','-Wall','-Wextra','-Werror','-shared',str(source),'-o',str(dll),'-lkernel32'],check=True)
(r/'build/logging-ji-receipt.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'dll_sha256':hashlib.sha256(dll.read_bytes()).hexdigest()},indent=2))

shutil.copy2(dll,r/'runtime/SOMA-VR-Logging.dll')
