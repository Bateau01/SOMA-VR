from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parents[1];version='1.0.9-S26HZ';build=2026102301
for p in [r/'installer/source/Build.ps1',r/'installer/source/Installer.cs',r/'installer/source/CurrentUpgradeTests.cs']:
 p.write_bytes(p.read_bytes().replace(b'1.0.8-S26HQ',version.encode()).replace(b'2026101617',str(build).encode()))
(r/'installer/output').mkdir(exist_ok=True)
shutil.copy2(r/'build/hpl3vr.dll',r/'runtime/hpl3vr.dll');shutil.copy2(r/'build/store/hpl3vr-store.dll',r/'runtime/hpl3vr-store.dll')
(r/'runtime/SOMA-VR-Update-Version.json').write_text(json.dumps({'version':version,'build':build},indent=2))
v={'version':version,'build':build,'status':'candidate for headset testing','automated_reports':['boundaries_hz.json','escape_lower_clearance_hz.json','installer_delivery_hz.json'],'headset_validation':'not performed','limits':['Phi save-load regression tested in native engine with supplied VR capability and hand-pose acknowledgement.','Escape surface placement checked with geometry fixture; runtime skeletal pose and comfortable reach require headset confirmation.','Existing HY coverage exclusions remain: eight deferred ladder areas; not universal ladder coverage.']}
(r/'runtime/PACKAGE_VERIFICATION.json').write_text(json.dumps(v,indent=2))
p=r/'runtime/SOMA_VR_FEATURES.md';s=p.read_text(encoding='utf-8-sig')
if '## 1.0.9 candidate' not in s:p.write_text(s+'\n\n## 1.0.9 candidate\n\nAdds collision-tested roomscale movement, default-on INTERACTION GUIDES, first-run VR settings guidance, and a main-menu version label. Improves direct tap sampling, registered palm buttons and remote readable handoff. Guides respect native permission and item order. Existing bindings and optional remote settings are preserved. Native/mock tests are not headset validation.\n',encoding='utf-8')
files={p.relative_to(r/'runtime').as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted((r/'runtime').rglob('*')) if p.is_file() and p.name!='SOMA_VR_MANIFEST.json'}
(r/'runtime/SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
shutil.copytree(r/'runtime',r/'installer/payload',dirs_exist_ok=True)
print('Prepared',version,len(files),'runtime files')
