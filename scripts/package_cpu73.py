from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parents[1];stage=r/'installer-cpu73';assert not (stage/'payload').exists()
for folder in ('source','art'):
 if not (stage/folder).exists():shutil.copytree(r/'installer-cpu72'/folder,stage/folder)
base=r/'installer-cpu72/payload' if (r/'installer-cpu72/payload').exists() else r/'runtime'
shutil.copytree(base,stage/'payload')
(stage/'output').mkdir(exist_ok=True)
for p in (stage/'source').iterdir():
 if p.suffix in ('.cs','.ps1'):p.write_bytes(p.read_bytes().replace(b'S26CPU72',b'S26CPU73').replace(b'2026103001',b'2026103002'))
payload=stage/'payload';shutil.copy2(r/'build/native-runtime/hpl3vr.dll',payload/'hpl3vr.dll');shutil.copy2(r/'build/store-cpu65/hpl3vr-store.dll',payload/'hpl3vr-store.dll');shutil.copy2(r/'runtime/script/modules/PlayerHandsHandler.hps',payload/'script/modules/PlayerHandsHandler.hps')
p=payload/'script/modules/MenuHandler.hps';p.write_bytes(p.read_bytes().replace(b'S26CPU72',b'S26CPU73'))
p=payload/'SOMA-VR-Update-Version.json';j=json.loads(p.read_text(encoding='utf-8-sig'));j.update(version='1.0.9-S26CPU73-Experimental',build=2026103002);p.write_text(json.dumps(j,indent=2))
p=payload/'PACKAGE_VERIFICATION.json';j=json.loads(p.read_text());j.update(version='1.0.9-S26CPU73-Experimental',status='Experimental palm fitting preparation; identical geometry and native physics retained');p.write_text(json.dumps(j,indent=2))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={p.relative_to(payload).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(payload.rglob('*')) if p.is_file() and p.name not in ('SOMA_VR_MANIFEST.json','installer-manifest.json')}
(payload/'SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':'1.0.9-S26CPU73-Experimental','files':files},indent=2))
assert sha(payload/'hpl3vr.dll')==sha(r/'build/native-runtime/hpl3vr.dll')
assert sha(payload/'hpl3vr-store.dll')==sha(r/'build/store-cpu65/hpl3vr-store.dll')
print('Staged CPU73 palm-fitting candidate over CPU72 payload')
