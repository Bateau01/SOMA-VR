from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
p=r/'scripts/package_ht.py';s=p.read_text().replace('S26HT','S26HU').replace('2026102203','2026102204')
s=s.replace("['key_geometry_summary_ht.json','unchanged_boundaries_ht.json','guide_vm_probe.json','installer_delivery_ht.json']","['native_summary_hu.json','world_gate_hu.json','registered_controls_hu.json','boundaries_hu.json','welcome_layout_hu.json','installer_delivery_hu.json']")
s=s.replace("Native geometry fixture activates targets and substitutes permission; it is not a full story or controller test.","Native fixtures supply starting states and a VR session flag; they are not full story or tracked-controller tests.")
(r/'scripts/package_hu.py').write_text(s)
p=r/'tests/test_delivery_ht_final.ps1';s=p.read_text().replace('S26HT','S26HU').replace('delivery-ht-final','delivery-hu-final').replace('installer_delivery_ht','installer_delivery_hu')
(r/'tests/test_delivery_hu_final.ps1').write_text(s)
notes="""# SOMA VR 1.0.9-S26HU — testing candidate

- Allows valid physical buttons while an ordinary laptop/terminal remains focused. Native permissions, held-object restrictions and scripted terminal ownership remain authoritative. This does not cancel the laptop's GUI or change tapping/laser input.
- Startup introduction now uses NEXT PAGE, revised category descriptions and first-time advice. Removes the standalone hand-reset sentence. Refreshes controller-profile information for physical button labels; disconnected/unknown controllers are identified honestly. Existing bindings remain unchanged.
- Moves 120HZ PHYSICS to VIDEO page one and TEXTURE BUDGET BOOST to page two.
- Gates Phi's launch moving-button and auxiliary callback by the authored launch-ready window. Early and duplicate launch actions are rejected.
- Adds Omicron/Phi armrest contact regions and a matching hand guide, gated by the original chair interaction. Existing center interaction remains. Guides OFF retains the added contact regions; flat-screen mode does not enable them.
- Confirms current Omni-Tool guide selection already follows the physical tool's upgrade-model file. All four canonical guide assets load.
- Retains S26HT item guides, including tracer-fluid and stun-baton exclusions.

See v109-followup-hu.md for tests and limitations. Final headset appearance, physical touches and complete story routes remain pending.
"""
p=r/'docs/RELEASE_NOTES.md';p.write_text(notes+'\n---\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
p=r/'docs/V109_TESTING.md';p.write_text('# Current candidate: S26HU\n\nSee [current checks and remaining headset validation](v109-followup-hu.md). Earlier reports below remain historical.\n\n'+p.read_text(),encoding='utf-8')
p=r/'docs/v109-followup-hu.md';s=p.read_text().replace('— in progress','— candidate checks').replace('Candidate implementation and verification pending. No confirmed fix or headset pass yet.','Candidate implementation complete; automated evidence below. Headset validation remains pending.')
s+='''

## Implementation and evidence
- The production fingertip entry branch was tested against HT: baseline fails the two terminal/world-control expectations; candidate passes while preserving held-object, grip-edge and non-terminal restrictions. This is an extracted branch with mocked state, not a tracked-controller test.
- Extracted registered-control dispatcher: 32 checks pass, including either hand, exact owner/main body, native denial, one-shot debounce, terminal permission granted/denied and unrelated neighbor state.
- Native apartment VM: existing Laptop_OnExit / VR_CanLeaveTerminalForPhysicalPickup permission is retained; ordinary return state accepted, scripted return state and missing prop denied. No automatic cancellation or synthetic B input.
- Phi's exact asset is Prop_MovingButton. The initial ordinary-button candidate did not cover it; native test caught that, and the unused ordinary-button edit was removed. Matched HT moving-button script fails the premature-launch checks; candidate passes.
- Native Phi callback test: early attempt schedules no launch, ready attempt schedules native delay and disables button, repeated callback executes no second accepted body. Timer removal is deferred by the engine; the test counts accepted callback execution rather than incorrectly expecting immediate disappearance from GetTimerTime.
- Native Omicron/Phi seat fixtures: both armrest regions resolve and forward native availability, rejecting inactive/disabled parent states. Existing area definitions are unchanged; two initially inactive VR-only auxiliary areas were added per map.
- Omicron chair is StaticProp and not a cLuxProp: guide/contact positions come from the original DAE and authored map placement. Phi's prop/submesh matrices were measured natively. Armrest surface projections were inspected; these are offline native-asset projections, not headset screenshots.
- Native controller-label tests cover Quest-style A/B/X/Y, Index left A, Frame D-pad labels and unknown profile. Native font metrics show the revised welcome lines fit; final rendered/headset layout remains unconfirmed.
- Native engine loaded all four Omni-Tool guide meshes. The slot's existing live carrier-file selection is unchanged.
- Adjacent regression: 64 pickup-chain assertions at 60/120 Hz; all 52 authored grip transforms/curls; source boundaries confirm PlayerToolHandler and Omni-slot code unchanged.
- Steam and exact-hash Epic/GOG DLLs compile. Store native script results and final installer delivery evidence are recorded in v109-evidence.

## Boundaries and remaining checks
No item usage, authored shoulder pose, native physics rate, headset renderer or terminal GUI touch/laser handler is changed. The world-control permission bit contains no pointers, is cleared on terminal/map lifecycle boundaries and is consulted only while an exact terminal state is active.
Fixture VR flags intentionally have no live OpenXR bridge; missing bridge messages in their logs are expected. These are native-script/geometry tests, not zero-error full-game VR sessions.

Headset checks: laptop then bathroom switch without B; normal terminal taps/laser and B/pause; scripted chair terminal cannot operate unrelated controls; welcome labels with controllers connected; Omicron/Phi chair armrests and guides at allowed/disallowed stages; Phi loading sequence then authorized launch. Old-save/new-area loading and a full campaign playthrough have not been certified.

Evidence: world_gate_hu.json, registered_controls_hu.json, boundaries_hu.json, welcome_layout_hu.json, native_summary_hu.json and installer_delivery_hu.json under docs/v109-evidence. Original installed game was not updated by development tests.
'''
p.write_text(s)

