from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HT-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes="""SOMA VR 1.0.9-S26HT - candidate for headset testing

Key-item guide update
- Covers 16 campaign key-item identities and 24 destination routes, including upgraded/formatted states.
- Excludes tracer fluid and the stun baton, as requested.
- Uses native placed mesh/submesh transforms, including native final placement offsets and animated mesh bones.
- Native permissions and Omicron suit stage order govern eligibility. No use callbacks are invoked by guides.
- Item usage, campaign scripts, entity definitions and authored shoulder poses remain unchanged.
- Existing Omni-Tool guidance and prior S26HS fixes are retained.

Checks completed
- Native geometry comparisons in eight campaign maps.
- Epic/GOG engine-profile geometry checks at Theta and Omicron (the supplied executable files are identical).
- Native permission, guide exclusion and lifecycle fixture; zero item-use callbacks.
- Pickup-chain regression and 52 authored grip-pose checks.
- Actual installer payload, fresh/repeat install, upgrade, interrupted-install recovery and updater checks.

Limits
Geometry fixtures activate targets and substitute permission, except the recorded native Theta permission cases. They validate transforms, not full story progression, physical controller input or headset appearance. No complete playthrough or headset visual pass is claimed. Earlier v1.0.9 hardware checks remain outstanding.

Please check
Hold an eligible key item near its destination. Confirm the hologram is aligned and readable, disappears after use, and does not appear for an ineligible stage. At Omicron check chip, battery, then gel. Tracer fluid and the stun baton should have no guide.

Installation
Close SOMA and run the setup for the intended installation. The installer includes both storefront DLLs and the updated scripts. Test fixtures, capture flags, AGENTS.md, CLAUDE.md and release notes are not installed into the game.
"""
(out/'SOMA-VR-1.0.9-S26HT-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/key-item-guides-ht.md',out/'SOMA-VR-1.0.9-S26HT-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HT-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HT/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))

