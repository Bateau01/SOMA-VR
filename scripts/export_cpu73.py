from pathlib import Path
import zipfile,json,hashlib,shutil
r=Path(__file__).resolve().parents[1];old='SOMA-VR-1.0.9-S26CPU72-Experimental';name='SOMA-VR-1.0.9-S26CPU73-Experimental'
out=r/'release-cpu73';out.mkdir(exist_ok=True);paths={}
with zipfile.ZipFile(r/'release-cpu72'/f'{old}-Source.zip') as z:
 for n in z.namelist():
  rel=n.removeprefix(old+'/')
  if not rel or n.endswith('/') or rel.startswith('runtime/'):continue
  if rel in ('scripts/package_cpu72.py','scripts/export_cpu72.py','tests/test_package_cpu72.py'):continue
  if rel.startswith('installer-cpu72/'):
   rel=rel.replace('installer-cpu72/','installer-cpu73/');paths[rel]=(r/rel).read_bytes()
  else:paths[rel]=z.read(n)
for rel in ('scripts/package_cpu73.py','scripts/export_cpu73.py','tests/test_package_cpu73.py','docs/CPU73_RELEASE.md','docs/CPU73_VALIDATION.md'):
 paths[rel]=(r/rel).read_bytes()
# Include the exact compiled source, not inherited historical source bytes.
for p in (r/'source').iterdir():
 if p.is_file():paths[p.relative_to(r).as_posix()]=p.read_bytes()
for rel in ('scripts/build_cpu_experimental.py','scripts/build_smaa_test_iu.py','scripts/build_store.py','scripts/cpu-runtime-options.json','tests/cpu70_scope_test.c','tests/cpu73_palm_equivalence.c','tests/test_cpu73_palm.py','tests/ark_query_ct_test.c','tests/test_omni_recall.py','docs/CPU73_PLAN.md'):
 paths[rel]=(r/rel).read_bytes()
for p in (r/'installer-cpu73/payload').rglob('*'):
 if p.is_file():paths['runtime/'+p.relative_to(r/'installer-cpu73/payload').as_posix()]=p.read_bytes()
for rel in ('README.md','docs/RELEASE_NOTES.md'):
 paths[rel]=(r/'docs/CPU73_RELEASE.md').read_bytes()+b'\n\n---\nHistorical documentation follows.\n\n'+paths[rel]
with zipfile.ZipFile(out/f'{name}-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for rel,data in sorted(paths.items()):
  assert Path(rel).name.lower() not in ('agents.md','claude.md')
  assert not any(x in rel.lower() for x in ('/audit/','/evidence/','verification-private','sps','multiview'))
  z.writestr(name+'/'+rel,data)
with zipfile.ZipFile(out/f'{name}-Source.zip') as z:assert z.testzip() is None
shutil.copy2(r/'installer-cpu73/output'/f'{name}-Setup.exe',out)
shutil.copy2(r/'docs/CPU73_RELEASE.md',out/'TESTING.md')
shutil.copy2(r/'installer-cpu73/output/SOMA-VR-update.json',out/'SOMA-VR-update.json')
(out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(out)
