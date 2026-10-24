from pathlib import Path
import shutil,zipfile,hashlib,json
R=Path(__file__).resolve().parents[1];out=R.parent/'release-IR';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26IR-Setup.exe','SOMA-VR-update.json']:shutil.copy2(R/'installer/output'/name,out/name)
shutil.copy2(R/'docs/PHONE_GUIDE_ROTATION.md',out/'SOMA-VR-1.0.9-S26IR-VALIDATION.md')
(out/'TESTING.txt').write_text((R/'docs/PHONE_GUIDE_ROTATION.md').read_text())
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26IR-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in R.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(R);parts=rel.parts
  if parts[0] in {'build','audit','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'} or (p.suffix.lower()=='.bin' and rel.as_posix() not in {'runtime/hand_left.bin','runtime/hand_right.bin'}):continue
  z.write(p,'SOMA-VR-1.0.9-S26IR/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
