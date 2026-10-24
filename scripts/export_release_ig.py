from pathlib import Path
import shutil,zipfile,hashlib,json
R=Path(__file__).resolve().parents[1];out=R.parent/'release-IG';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26IG-Setup.exe','SOMA-VR-update.json']:shutil.copy2(R/'installer/output'/name,out/name)
shutil.copy2(R/'docs/HAND_TIMING_IG.md',out/'SOMA-VR-1.0.9-S26IG-VALIDATION.md')
(out/'TESTING.txt').write_text('S26IG candidate: queued crouch timing correction; general movement jitter audit remains open.\nClose SOMA and install. Preserve any old timing capture before relaunching. With the existing hpl3vr_hand_timing.flag, the recorder automatically saves hpl3vr_hand_timing_IF.bin after approximately 17 seconds at 120 Hz. No flag is installed automatically.\nFor comparison: immediately after loading, crouch/stand twice, then pick up a nearby prop and walk/crouch briefly. Keep 120 Hz and roomscale unchanged for the first comparison. A separate ocean run and 60 Hz comparison remain pending. The recorder does not measure final mesh/display motion.\nNo new smoothing/interpolation. Grabbing/collision rules and authored item poses unchanged. Do not publish this candidate as a fully validated jitter fix.\n')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26IG-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in R.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(R);parts=rel.parts
  if parts[0] in {'build','audit','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag','.bin'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26IG/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
