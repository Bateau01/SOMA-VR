from pathlib import Path
import zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
archive=out/'SOMA-VR-1.0.9-S26IA-Source.zip';files=set()
for folder in ['source','runtime','scripts','reference','third_party','tests','installer/source','installer/art']:
 for p in (r/folder).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix.lower() in ['.pyc','.obj','.log','.ppm']:continue
  if folder=='tests' and p.suffix.lower() in ['.dll','.exe']:continue
  files.add(p)
for p in (r/'docs').rglob('*'):
 if p.is_file() and p.suffix.lower() in ['.md','.json'] and not any(x in str(p).lower() for x in ['user-hy','provenance']):files.add(p)
for n in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','AGENTS.md']:files.add(r/n)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,p.relative_to(r).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for folder in ['runtime','source']:
  for p in (r/folder).rglob('*'):
   if p.is_file():assert z.read(p.relative_to(r).as_posix())==p.read_bytes()
report={'files':len(files),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'archive_integrity':'passed','source_and_runtime':'byte-identical'}
(out/'source-verification.json').write_text(json.dumps(report,indent=2));print(report)
