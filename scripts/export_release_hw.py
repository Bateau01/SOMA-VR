from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HW-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes='''SOMA VR 1.0.9-S26HW - candidate for headset testing

Adds a read-only hand guide at Upsilon's comms escape ledge. SUBTITLE DISTANCE now applies to hints and info as well as subtitles. Includes capped observation-only subtitle transform diagnostics; the reported stereo issue is not confirmed fixed. Native usage, shoulder poses and physics are unchanged.

See VALIDATION.md for test scope and the remaining headset checks. Close SOMA before installing.
'''
(out/'SOMA-VR-1.0.9-S26HW-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/escape-subtitle-hw.md',out/'SOMA-VR-1.0.9-S26HW-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HW-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HW/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
