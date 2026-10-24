from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HV-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes='''SOMA VR 1.0.9-S26HV - candidate for headset testing

Corrects the first Upsilon Omni-Tool hologram after pickup and shoulder retrieval. The native slot provides placement, while the authored trigger provides initial-use permission. The guide now follows that distinction. Usage, physical insertion, shoulder poses, collisions and progression code are unchanged. Tracer fluid and stun baton remain excluded.

Tests and limits
See VALIDATION.md for the completed native sequence, campaign audit, key geometry and installer evidence. Native fixtures supply tracking/held observations and selected starting states. They are not a full campaign playthrough or a headset test.

Please test
At Upsilon, turn on the room power, acquire the first Omni-Tool, stow and retrieve it near the upgrade terminal. Confirm its hologram appears at the socket, disappears when the tool is released or inserted, and the normal chip-upgrade sequence remains usable. Also check any previously affected guide destination in your existing saves.

Close SOMA and run the installer for the intended storefront. Development fixtures and diagnostics are not included in the player payload.
'''
(out/'SOMA-VR-1.0.9-S26HV-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/guide-audit-hv.md',out/'SOMA-VR-1.0.9-S26HV-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HV-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HV/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
