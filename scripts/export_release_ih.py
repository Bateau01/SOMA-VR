from pathlib import Path
import shutil,zipfile,hashlib,json
R=Path(__file__).resolve().parents[1];out=R.parent/'release-IH';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26IH-Setup.exe','SOMA-VR-update.json']:shutil.copy2(R/'installer/output'/name,out/name)
shutil.copy2(R/'docs/FRAME_TIMING_IH.md',out/'SOMA-VR-1.0.9-S26IH-VALIDATION.md')
(out/'TESTING.txt').write_text('S26IH diagnostic candidate, not a confirmed jitter fix. Close SOMA and install. Place the supplied hpl3vr_frame_timing.flag beside SOMA.exe (already prepared in the developer Steam installation). Keep current physics and roomscale settings. After loading, walk/turn for 10 seconds, crouch/stand, then hold a nearby prop while walking. Leave game open for 35 seconds. Capture saves automatically as hpl3vr_frame_timing_IH.bin; no recording-menu command. Preserve that file and hpl3vr.log before restarting. Remove flag to disable capture. Old IF hand recorder is suppressed while new flag is present. See VALIDATION for completed tests and limits.\n')
(out/'hpl3vr_frame_timing.flag').write_text('S26IH bounded observation-only diagnostic. Remove to disable next launch.\n')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26IH-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in R.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(R);parts=rel.parts
  if parts[0] in {'build','audit','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag','.bin'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26IH/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
