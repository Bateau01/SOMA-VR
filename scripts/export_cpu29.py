"""Export explicit public source/payload paths, excluding private audits/captures."""
from pathlib import Path
import hashlib,json,shutil,zipfile
r=Path(__file__).resolve().parents[1];name='SOMA-VR-1.0.9-S26CPU29-Experimental'
out=r/'release-cpu29';out.mkdir(exist_ok=True)
shutil.copy2(r/'installer-cpu29/output'/f'{name}-Setup.exe',out)
shutil.copy2(r/'docs/CPU29.md',out/'TESTING.md')
paths=[]
for folder in ('source','scripts','tests','third_party','installer-cpu29/source','installer-cpu29/art'):
    for p in (r/folder).rglob('*'):
        if p.is_file() and not any(x in p.name.lower() for x in ('stereo','sps','multiview')) and p.name not in ('prepare_context_probe.py','export_prototype.py','cpu29_crash_capture.c','inspect_cpu29_dump.py') and '__pycache__' not in p.parts and p.suffix.lower() not in ('.pyc','.log','.dmp','.flag','.rgba'):
            paths.append((p,p.relative_to(r).as_posix()))
paths.extend((p,'runtime/'+p.relative_to(r/'installer-cpu29/payload').as_posix()) for p in (r/'installer-cpu29/payload').rglob('*') if p.is_file())
paths.extend((r/p,p) for p in ('README.md','LICENSE','THIRD_PARTY_NOTICES.md','docs/CPU_EXPERIMENTAL.md','docs/IW_CPU7.md','docs/CPU9.md','docs/CPU15.md','docs/CPU16.md','docs/CPU29.md','docs/BUILD.md','docs/FEATURES.md','docs/INSTALLATION.md','docs/RELEASE_NOTES.md','reference/store-profile.json'))
with zipfile.ZipFile(out/f'{name}-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p,rel in sorted(paths,key=lambda x:x[1]):
        assert Path(rel).name.lower() not in ('agents.md','claude.md')
        if rel in ('README.md','docs/RELEASE_NOTES.md'):
            z.writestr(name+'/'+rel,(r/'docs/CPU29.md').read_text()+'\n\n---\nPrevious documentation follows.\n\n'+p.read_text(errors='replace'))
        else:z.write(p,name+'/'+rel)
with zipfile.ZipFile(out/f'{name}-Source.zip') as z:
    assert z.testzip() is None
    assert not any('/audit/' in n or '/evidence/' in n for n in z.namelist())
(out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(out)
