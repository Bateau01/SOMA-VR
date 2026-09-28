"""Read-only verification of a player overlay or installed mod against its manifest."""
from pathlib import Path
import argparse,json,hashlib,sys
p=argparse.ArgumentParser();p.add_argument('folder',nargs='?',default=str(Path(__file__).resolve().parents[1]/'runtime'));args=p.parse_args()
root=Path(args.folder).resolve();manifest=json.loads((root/'SOMA_VR_MANIFEST.json').read_text())
errors=[]
for rel,want in manifest['files'].items():
 path=(root/rel).resolve()
 if not path.is_relative_to(root):raise ValueError('Manifest path outside root')
 if not path.is_file():errors.append('Missing: '+rel)
 elif hashlib.sha256(path.read_bytes()).hexdigest()!=want['sha256']:errors.append('Different: '+rel)
if errors:print('\n'.join(errors));sys.exit(1)
print('PASS:',len(manifest['files']),'overlay files match',manifest['version'])
