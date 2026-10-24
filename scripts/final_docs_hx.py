from pathlib import Path
r=Path('.');p=r/'docs/escape-followup-hx.md';s=p.read_text();s+='''
## Candidate changes
- Guide anchor is now native AreaClimbHole local (0,-2.12,+.42), toward the lower/player-facing face. The hand's 25mm surface offset remains inside the .583m half-depth; the contact's native inverse coordinates verify the lower-zone placement. No native trigger dimensions, collision, haptics or grip logic changed.
- Subtitle diagnostics removed at user request. Subtitle rendering remains unchanged, and SUBTITLE DISTANCE continues to control hints/info too.
- Escape-only status logging records at most 16 state transitions: native gate closed, option off, outside range, mesh/pose rejected, visible. This is intended to distinguish eligibility/mesh failure from occlusion on the next hardware run.

## Evidence and limits
- The prior log's zero rotation deltas do not prove correct eye projections because eye identity was not captured. No subtitle fix is claimed.
- Native map Update runs; permission/withdrawal/reentry/accepted-climb checks pass. The guide point is inside the original interaction box.
- Extended native visibility fixture supplies VR capability and bone-pose acknowledgements; it tests mesh creation and visibility flags, not the live DLL's final bone pose or rendered headset pixels. Initial fixture failed because the isolated folder lacked guide.mat; the harness now copies/restores the delivered material. The user's installed material already matches the package, so that fixture omission is not an explanation of their report.
- Source comparison confirms only the guide helper/status logging and removal of subtitle diagnostics changed, apart from build identity. Native climb callbacks, item usage and shoulder poses are unchanged. Full flooding-to-wake playback and visual comfort remain hardware checks.
''';p.write_text(s)
s=(r/'scripts/export_release_hw.py').read_text().replace('S26HW','S26HX').replace('escape-subtitle-hw.md','escape-followup-hx.md');a=s.index("notes='''");b=s.index("'''",a+9)
s=s[:a]+"notes='''SOMA VR 1.0.9-S26HX - escape guide candidate\n\nMoves the Upsilon comms escape hand guide to the bottom/player-facing edge of the existing interaction zone. Removes subtitle diagnostics without changing subtitle rendering. Shared subtitle/hint/info distance remains. Includes capped escape-guide visibility-status logging.\n\nClose SOMA and install. At the escape opening, check the lower reach cue and normal climb. If it remains missing, retain hpl3vr.log for the S26HX ESCAPE GUIDE messages. See VALIDATION.md for the automated-test limitations.\n"+s[b:];(r/'scripts/export_release_hx.py').write_text(s)
