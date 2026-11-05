from pathlib import Path
import json,hashlib,shutil,zipfile
r=Path(__file__).resolve().parents[1];name='SOMA-VR-1.1.1-S26JH';out=r/'release-jh';out.mkdir(exist_ok=True)
payload=r/'installer-jh/payload'
for rel,build in [('hpl3vr.dll','build/native-runtime/hpl3vr.dll'),('hpl3vr-store.dll','build/store-cpu65/hpl3vr-store.dll')]:
 data=(payload/rel).read_bytes();assert data==(r/build).read_bytes();assert b'NI_TEST LOOK' not in data
for p in (r/'runtime/script').rglob('*.hps'):assert p.read_bytes()==(payload/'script'/p.relative_to(r/'runtime/script')).read_bytes()
paths={}
for folder in ('source','scripts','tests','reference','third_party','docs'):
 for p in (r/folder).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  rel=p.relative_to(r).as_posix()
  if p.name=='NATIVE_INPUT_PLAN.md' or any(x in rel.lower() for x in ('verification-private','private_verification','/audit/','/evidence/')):continue
  if folder=='tests' and p.suffix.lower() in ('.dll','.exe','.pyc'):continue
  paths[rel]=p.read_bytes()
for p in (r/'installer-jh').rglob('*'):
 if p.is_file() and p.relative_to(r/'installer-jh').parts[0] in ('source','art'):paths[p.relative_to(r).as_posix()]=p.read_bytes()
for p in payload.rglob('*'):
 if p.is_file():paths['runtime/'+p.relative_to(payload).as_posix()]=p.read_bytes()
for rel in ('README.md','LICENSE','THIRD_PARTY_NOTICES.md'):paths[rel]=(r/rel).read_bytes()
paths['README.md']=b'# SOMA VR 1.1.1-S26JH\n\nSee [1.1.1 validation and remaining checks](docs/V111_VALIDATION_JH.md). Validation limits are documented there.\n\n'+paths['README.md']
with zipfile.ZipFile(out/(name+'-Source.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for rel,data in sorted(paths.items()):
  assert Path(rel).name.lower() not in ('agents.md','claude.md')
  z.writestr(name+'/'+rel,data)
with zipfile.ZipFile(out/(name+'-Source.zip')) as z:assert z.testzip() is None
shutil.copy2(r/'installer-jh/output'/(name+'-Setup.exe'),out)
shutil.copy2(r/'docs/V111_VALIDATION_JH.md',out/'TESTING.md')
shutil.copy2(r/'installer-jh/output/SOMA-VR-update.json',out/'SOMA-VR-update.json')
(out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(out)
