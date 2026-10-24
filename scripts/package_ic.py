from pathlib import Path
import json,hashlib,shutil,zipfile
r=Path(__file__).resolve().parents[1]
version='1.0.9-S26IE'
(r/'runtime/SOMA-VR-Update-Version.json').write_text(json.dumps({'version':version,'build':2026102306},indent=2))
(r/'runtime/PACKAGE_VERIFICATION.json').write_text(json.dumps({'version':version,'native_runtime':'S26IE Steam and store','change':'Roomscale camera and velocity history preservation; physical-travel footsteps','tests':'docs/ROOMSCALE_IE.md'},indent=2))
files={p.relative_to(r/'runtime').as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted((r/'runtime').rglob('*')) if p.is_file() and p.name!='SOMA_VR_MANIFEST.json'}
(r/'runtime/SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
shutil.copytree(r/'runtime',r/'installer/payload',dirs_exist_ok=True)
out=r.parent/'release';out.mkdir(exist_ok=True)

