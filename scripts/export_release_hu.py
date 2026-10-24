from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HU-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes='''SOMA VR 1.0.9-S26HU - candidate for headset testing

Changes
- Permits eligible physical world buttons after ordinary laptop/terminal use without requiring B or distance-based exit. Scripted terminal restrictions remain authoritative.
- Welcome pages use NEXT PAGE, first-time advice, category summaries and refreshed physical controller labels. Existing bindings are preserved.
- VIDEO page one includes 120HZ PHYSICS; TEXTURE BUDGET BOOST moves to page two.
- Phi launch button requires the authored ready window, including direct and auxiliary interaction routes; duplicate launch acceptance is rejected.
- Omicron and Phi pilot seats gain VR armrest contact regions and hand guides based on native chair geometry and native seat availability.
- Existing Omni-Tool hologram selection retains all four upgrade variants. Item usage and authored shoulder grips are unchanged.

Automated evidence
Extracted production-control tests, native Steam and Epic/GOG script fixtures, native asset geometry inspection, controller-label checks, 64 pickup-chain assertions and 52 authored grip checks passed. The prior Phi moving-button script fails the tested permission gate, while the candidate passes. Actual installer fresh/upgrade/recovery/updater tests and embedded payload hashes passed.

Limits
Native fixtures supply starting states and a VR-session flag. They do not validate physical controller input, a complete story sequence, headset guide appearance or old-save area migration. This is a candidate, not a claim that all v1.0.9 hardware checks are complete.

Please test
1. Use Simon's apartment laptop, then touch the bathroom light switch without pressing B or walking far away. Also verify terminal taps, laser input and B still work.
2. Check welcome text, connected-controller button names and VIDEO pagination.
3. At Omicron/Phi, inspect the armrest guide and grab it when the native seat is available. Confirm the guide disappears when seated.
4. At Phi, confirm the launch button rejects early interaction, then works after loading and Catherine's instruction.

Installation
Close SOMA and run the setup for the intended installation. Both supported storefront DLLs and updated scripts are included. Development test fixtures, capture flags, AGENTS.md, CLAUDE.md and release notes are not installed into the game.
'''
(out/'SOMA-VR-1.0.9-S26HU-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/v109-followup-hu.md',out/'SOMA-VR-1.0.9-S26HU-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HU-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc','.flag'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HU/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
