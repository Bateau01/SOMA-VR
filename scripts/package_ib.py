from pathlib import Path
import json,hashlib,shutil,zipfile
r=Path(__file__).resolve().parents[1]
version='1.0.9-S26IB'
(r/'runtime/SOMA-VR-Update-Version.json').write_text(json.dumps({'version':version,'build':2026102303},indent=2))
(r/'runtime/PACKAGE_VERIFICATION.json').write_text(json.dumps({'version':version,'native_runtime':'unchanged S26IA','change':'Precompiled startup/display helpers; no environment modification','tests':'docs/launcher-environment-ib.md'},indent=2))
files={p.relative_to(r/'runtime').as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted((r/'runtime').rglob('*')) if p.is_file() and p.name!='SOMA_VR_MANIFEST.json'}
(r/'runtime/SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
shutil.copytree(r/'runtime',r/'installer/payload',dirs_exist_ok=True)
out=r.parent/'release';out.mkdir(exist_ok=True)
with zipfile.ZipFile(out/(version+'-Launcher-Fix.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for name in ['Launch-SOMA-VR.ps1','SOMA-VR-Settings.ps1','SOMA-VR-LaunchSupport.dll']:z.write(r/'runtime'/name,name)
 z.writestr('README.txt','Close SOMA. Extract all three files into the SOMA game folder alongside Launch-SOMA-VR.cmd, replacing the two scripts. Keep the DLL alongside them. Alternatively run the full installer. This does not modify Windows environment variables. Native game runtime remains S26IA; this package fixes launcher startup only.\n')
