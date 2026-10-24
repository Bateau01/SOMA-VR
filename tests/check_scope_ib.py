from pathlib import Path
import re,json
r=Path(__file__).resolve().parents[1]
old=r.parents[1]/'SOMA_VR_109_S26IA/repo'
allowed={'Launch-SOMA-VR.ps1','SOMA-VR-Settings.ps1','SOMA-VR-LaunchSupport.dll','SOMA-VR-Update-Version.json','PACKAGE_VERIFICATION.json','SOMA_VR_MANIFEST.json'}
changed=[]
for p in (r/'runtime').rglob('*'):
 if not p.is_file():continue
 n=p.relative_to(r/'runtime').as_posix();q=old/'runtime'/n
 if not q.exists() or p.read_bytes()!=q.read_bytes():
  changed.append(n);assert n in allowed,n
for i,n in enumerate(['Launch-SOMA-VR.ps1','SOMA-VR-Settings.ps1']):
 before=(old/'runtime'/n).read_text(encoding='utf-8-sig')
 after=(r/'runtime'/n).read_text(encoding='utf-8-sig')
 pattern=r"Add-Type -TypeDefinition @'\n(.*?)\n'@"
 m=re.search(pattern,before,re.S);assert m
 assert m.group(1)==(r/'launcher/source'/('Helper%d.cs'%i)).read_text()
 expected=before[:m.start()]+"Add-Type -Path (Join-Path $PSScriptRoot 'SOMA-VR-LaunchSupport.dll')"+before[m.end():]
 assert expected==after,n
report={'changedRuntimeFiles':changed,'helperSourceIdentical':True,'launcherOnlyHelperLoadingChanged':True,'gameDllsScriptsAssetsUnchanged':True}
(r/'docs/v109-evidence/scope-ib.json').write_text(json.dumps(report,indent=2));print(report)
