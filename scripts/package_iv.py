from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];version='1.0.9-S26IV';build=2026102405
for name in ['Build.ps1','Installer.cs','CurrentUpgradeTests.cs']:
 p=R/'installer/source'/name;p.write_bytes(p.read_bytes().replace(b'1.0.9-S26IU',version.encode()).replace(b'2026102404',str(build).encode()))
p=R/'runtime/script/modules/MenuHandler.hps';p.write_bytes(p.read_bytes().replace(b'v1.0.9 - S26IU',b'v1.0.9 - S26IV'))
for src,dst in [('build/hpl3vr.dll','hpl3vr.dll'),('build/store/hpl3vr-store.dll','hpl3vr-store.dll')]:shutil.copy2(R/src,R/'runtime'/dst)
(R/'runtime/SOMA-VR-Update-Version.json').write_text(json.dumps({'version':version,'build':build},indent=2))
(R/'runtime/PACKAGE_VERIFICATION.json').write_text(json.dumps({'version':version,'status':'candidate; headset comparison pending','change':'Unified anti-aliasing selection and VIDEO ordering; no gameplay changes','tests':'docs/FOLLOWUP_IV.md','open':['Human comfort/quality comparison and other GPU vendors remain unverified']},indent=2))
files={p.relative_to(R/'runtime').as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted((R/'runtime').rglob('*')) if p.is_file() and p.name!='SOMA_VR_MANIFEST.json'}
assert not any(Path(p).name.lower()=='agents.md' or p.endswith('.flag') for p in files)
(R/'runtime/SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
shutil.copytree(R/'runtime',R/'installer/payload',dirs_exist_ok=True)
(R/'installer/output').mkdir(exist_ok=True)
