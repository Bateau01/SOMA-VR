from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HX-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes='''SOMA VR 1.0.9-S26HX - escape guide candidate

Moves the Upsilon comms escape hand guide to the bottom/player-facing edge of the existing interaction zone. Removes subtitle diagnostics without changing subtitle rendering. Shared subtitle/hint/info distance remains. Includes capped escape-guide visibility-status logging.

Close SOMA and install. At the escape opening, check the lower reach cue and normal climb. If it remains missing, retain hpl3vr.log for the S26HX ESCAPE GUIDE messages. See VALIDATION.md for the automated-test limitations.
'''
(out/'SOMA-VR-1.0.9-S26HX-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/escape-followup-hx.md',out/'SOMA-VR-1.0.9-S26HX-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HX-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HX/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
