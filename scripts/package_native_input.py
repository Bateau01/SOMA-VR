from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parents[1];stage=r/'installer-ja'
assert not (stage/'payload').exists() and not (stage/'output').exists(), 'Preserve an existing package; use a clean source extraction'
version='1.1.0-S26JA'
for folder in ('source','art'):
 if not (stage/folder).exists():shutil.copytree(r/'installer-cpu73'/folder,stage/folder)
for p in (stage/'source').iterdir():
 if p.suffix in ('.cs','.ps1'):p.write_bytes(p.read_bytes().replace(b'1.0.9-S26CPU73-Experimental',b'1.1.0-S26JA').replace(b'S26CPU73',b'S26JA').replace(b'2026103002',b'2026103103'))
shutil.copytree(r/'runtime',stage/'payload');(stage/'output').mkdir()
payload=stage/'payload'
for source,dest in [('build/native-runtime/hpl3vr.dll','hpl3vr.dll'),('build/store-cpu65/hpl3vr-store.dll','hpl3vr-store.dll')]:shutil.copy2(r/source,payload/dest)
for name in ('installer-manifest.json','SOMA_VR_MANIFEST.json'):
 p=payload/name
 if p.exists():p.unlink()
p=payload/'SOMA-VR-Update-Version.json';j=json.loads(p.read_text(encoding='utf-8-sig'));j.update(version=version,build=2026103103);p.write_text(json.dumps(j,indent=2))
p=payload/'PACKAGE_VERIFICATION.json';p.write_text(json.dumps({'version':version,'status':'Experimental native-input candidate; see separate TESTING.md for validation limits'},indent=2))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={p.relative_to(payload).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(payload.rglob('*')) if p.is_file()}
assert not any(Path(f).name.lower() in ('agents.md','claude.md') or 'audit/' in f or 'verification-private' in f for f in files)
(payload/'SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
print(stage)
