"""Stage CPU16 separately; no modification of installed games or stable updates."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
version='1.0.9-S26CPU16-Experimental';build=2026102703
stage=r/'installer-cpu16'
assert (stage/'source/Installer.cs').is_file() and (stage/'art/soma.ico').is_file(), 'Installer source/art must accompany this source archive'
assert not (stage/'payload').exists(), 'Use a fresh staging directory; preserve existing output explicitly'
(stage/'output').mkdir(exist_ok=True)
payload=stage/'payload';shutil.copytree(r/'runtime',payload)
receipt=json.loads((r/'build/native-runtime/build-receipt.json').read_text())
assert receipt['arguments']['production'] and receipt['arguments']['cpu_string_spans'] and receipt['arguments']['cpu_near_types'] and receipt['arguments']['cpu_texture_storage'] and receipt['arguments']['cpu_texture_latc']
assert receipt['arguments']['cpu_texture_release'] and receipt['arguments']['cpu_gui_prewarm']
assert receipt['arguments']['cpu_texture_min_bytes']==65536 and receipt['arguments']['cpu_render_jobs']
assert not receipt['arguments']['cpu_string_oracle'] and not receipt['arguments']['cpu_work_profile']
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in receipt['source_hashes'].items())
for src,dst in [('build/native-runtime/hpl3vr.dll','hpl3vr.dll'),('runtime/hpl3vr-store.dll','hpl3vr-store.dll')]:
    data=(r/src).read_bytes()
    assert b'>>> CPU_WORK row' not in data and b'>>> CPU_STRING_ORACLE' not in data and b'>>> CPU_METADATA_CENSUS' not in data
    assert all(marker not in data for marker in (b'>>> CPU16_GUI_INSTALL',b'>>> CPU16_SLOW_ENTITY',b'>>> CPU16_MAP_TOTAL',b'>>> CPU15_RENDER',b'>>> CPU16_POOL',b'>>> CPU16_CALLER',b'>>> CPU16_JOB_TYPE',b'>>> CPU_ENGINE',b'>>> CPU_FRAME',b'>>> CPU_NEAR_ORACLE',b'>>> CPU_TEXTURE_COST',b'>>> CPU_TEXTURE_SLOW'))
    shutil.copy2(r/src,payload/dst)
menu=payload/'script/modules/MenuHandler.hps'
menu.write_bytes(menu.read_bytes().replace(b'v1.0.9 - S26IW',b'v1.0.9 - S26CPU16 EXPERIMENTAL'))
(payload/'SOMA-VR-Update-Version.json').write_text(json.dumps({'version':version,'build':build},indent=2))
# Experimental notes are a separate upload, not installed game content.
(payload/'PACKAGE_VERIFICATION.json').write_text(json.dumps({'version':version,'status':'Native stereo only; SPS retired; retained metadata/texture optimizations and native render-list scheduling','steam_dll_sha256':receipt['dll_sha256']},indent=2))
files={p.relative_to(payload).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(payload.rglob('*')) if p.is_file() and p.name not in ('SOMA_VR_MANIFEST.json','installer-manifest.json')}
assert not any(Path(p).name.lower() in ('agents.md','claude.md') or p.endswith('.flag') for p in files)
(payload/'SOMA_VR_MANIFEST.json').write_text(json.dumps({'version':version,'files':files},indent=2))
print(stage)
