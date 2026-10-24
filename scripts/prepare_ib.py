from pathlib import Path
import re,json,shutil,hashlib
r=Path(__file__).resolve().parents[1]
sources=[]
for name in ['Launch-SOMA-VR.ps1','SOMA-VR-Settings.ps1']:
 p=r/'runtime'/name
 s=p.read_text(encoding='utf-8-sig')
 pattern=r"Add-Type -TypeDefinition @'\r?\n(.*?)\r?\n'@"
 m=re.search(pattern,s,re.S)
 if not m: continue
 sources.append(m.group(1))
 s=s[:m.start()]+"Add-Type -Path (Join-Path $PSScriptRoot 'SOMA-VR-LaunchSupport.dll')"+s[m.end():]
 p.write_text(s,encoding='utf-8-sig')
out=r/'launcher/source';out.mkdir(parents=True,exist_ok=True)
for i,s in enumerate(sources): (out/('Helper%d.cs'%i)).write_text(s)
for name in ['Build.ps1','Installer.cs','CurrentUpgradeTests.cs']:
 p=r/'installer/source'/name
 s=p.read_bytes().replace(b'1.0.9-S26IA',b'1.0.9-S26IB').replace(b'2026102302',b'2026102303')
 p.write_bytes(s)
p=r/'tests/test_delivery_ia.ps1'
s=p.read_text(encoding='utf-8-sig').replace('S26IA','S26IB').replace('delivery-ia-final','delivery-ib-final').replace('installer_delivery_ia','installer_delivery_ib')
(r/'tests/test_delivery_ib.ps1').write_text(s,encoding='utf-8-sig')
(r/'installer/output').mkdir(exist_ok=True)
(r/'build').mkdir(exist_ok=True)
(r/'docs/launcher-environment-ib.md').write_text('''# S26IB launcher environment compatibility

Impact: launcher startup helper loading and display helper loading; Steam/Epic/GOG share these scripts. No game DLL, script, pose or interaction changes. Preserve all inherited environment entries, monitor selection, settings repair, elevation and injection.

Baseline reproduced: Windows PowerShell Add-Type source compilation throws EnvironmentBlock.ToByteArray / CodeDom.Compiler.Executor with 325854 bytes. Synthetic variables exist only in a disposable child process. User screenshot has 325221 bytes.

Correction: precompile the exact two existing C# helpers into SOMA-VR-LaunchSupport.dll; load the assembly instead of compiling source at runtime. No environment pruning, registry changes, PowerShell migration or altered injection path.

Acceptance: ordinary and oversized environments load both helpers, enumerate actual monitor, create a suspended harmless process and resume it, launch redirected helper; environment snapshot unchanged. Installer payload and upgrade/recovery tests must pass. No headset/gameplay change; native mod remains S26IA, installer revision S26IB.
''')
print('Prepared IB')

