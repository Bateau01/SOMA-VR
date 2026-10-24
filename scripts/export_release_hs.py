from pathlib import Path
import shutil,zipfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r.parent/'release';out.mkdir(exist_ok=True)
for name in ['SOMA-VR-1.0.9-S26HS-Setup.exe','SOMA-VR-update.json']:
 shutil.copy2(r/'installer/output'/name,out/name)
notes='''SOMA VR 1.0.9-S26HS — candidate for testing

Changes since S26HR
- Clears the palm-control registry during normal map transfers and removes cached-body matrix queries from palm target selection. Addresses the crash path found in the Upsilon wake-up dump.
- Direct terminal touch retains an unconsumed contact briefly while the fingertip settles onto a button. Stops after native consumption, release or timeout. Laser input keeps its original press behavior.
- Corrects Omni-Tool guide transforms using the visible submesh. Corrects the lab chair surface anchor using its visible armrest geometry.
- Adds snap-follow behavior to the separate upper-view hint anchor.
- Adds a startup controller-buttons page using current bindings and controller-profile labels. Existing bindings remain intact.

Validation
Steam and Epic/GOG builds passed. Focused and adjacent regression suites passed. Native widget tests reproduced a blank-space-first missed click and confirmed the candidate contact policy, without repeating accepted buttons or custom handlers. Native map probes measured actual chair/tool geometry. Installer payload, upgrade, interrupted-install recovery and updater checks passed.

Limits
The native fixtures substitute input and do not prove the full Munchi-to-Upsilon VR transition or physical fingertip behavior. Window capture timed out and the game's screenshot request produced no image; final welcome-page and hologram visuals are not certified. No full-playthrough or headset pass is claimed.

Next headset checks
1. Play through the brain scan to Upsilon; check controls afterward.
2. Try the apartment/lab laptops and keypad, including light repeated taps, touching blank space then a button, and holding/dragging.
3. At Lambda, hold the eligible Omni-Tool near the slot, check the guide, insert it, and verify the guide disappears.
4. Check the chair hand on its armrest after dialogue permits interaction.
5. Check hint snap-follow and both startup pages, including BACK and CONTINUE. Verify your bindings are displayed correctly.

Installation
Close SOMA, run the setup, and update the intended installation. The setup includes the scripts and both storefront DLLs. Test fixtures, capture tools, AGENTS.md, CLAUDE.md and these release notes are not installed into the game.
'''
(out/'SOMA-VR-1.0.9-S26HS-TESTING.txt').write_text(notes,encoding='utf-8')
shutil.copy2(r/'docs/v109-followup-hs.md',out/'SOMA-VR-1.0.9-S26HS-VALIDATION.md')
with zipfile.ZipFile(out/'SOMA-VR-1.0.9-S26HS-Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in r.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(r);parts=rel.parts
  if parts[0] in {'build','.git','.agents','.codex'} or '__pycache__' in parts:continue
  if parts[:2] in {('installer','payload'),('installer','output'),('docs','v109-evidence')}:continue
  if rel.as_posix()=='installer/payload.zip' or p.suffix.lower() in {'.dmp','.log','.pyc'}:continue
  z.write(p,'SOMA-VR-1.0.9-S26HS/'+rel.as_posix())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
(out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(hashes.items())))
print(json.dumps({'release':str(out),'files':list(hashes)},indent=2))
